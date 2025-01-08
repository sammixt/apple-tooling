from fastapi import APIRouter, Request, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional
from sqlalchemy.orm import Session, load_only
from app.db.database import get_db
from app.schemas.s3file import (
    S3FileCreate,
    S3FileUpdate,
    S3File,
    S3FileCreateUpdate,
    S3FilesResponse,
    S3FileResponseWithAllData,
    PaginatedS3FilesResponse,
    WebhookPayload,
)
from app.db.models import FileContent, ActivityLog
from app.db.models import S3File as S3FileModel
import json
from app.db.redis_client import redis_client
from app.jobs.celery_task import worker
from sqlalchemy import asc, desc
import logging
from app.auth.dependencies import has_permission, user_session

router = APIRouter()

logging.basicConfig(level=logging.DEBUG)  # You can set this to DEBUG for more detailed logs
logger = logging.getLogger(__name__)


@router.post("/s3files/create-or-update", response_model=S3File)
def create_or_update_s3_file(s3_file_data: S3FileCreateUpdate, db: Session = Depends(get_db)):
    # Check if the S3 file already exists
    existing_s3_file = db.query(S3FileModel).filter(S3FileModel.s3key == s3_file_data.s3key).first()

    if existing_s3_file:
        # Update existing S3 file
        existing_s3_file.file_url = s3_file_data.file_url
        existing_s3_file.workstream = s3_file_data.workstream

        # Update the file contents
        content_record = db.query(FileContent).filter(FileContent.s3file_id == existing_s3_file.id).first()
        if content_record:
            content_record.content = s3_file_data.content
            content_record.file_type = s3_file_data.file_type
        else:
            # Create new content record if it doesn't exist
            new_content = FileContent(
                s3file_id=existing_s3_file.id, content=s3_file_data.content, file_type=s3_file_data.file_type
            )
            db.add(new_content)

        db.commit()  # Save changes to the database
        return existing_s3_file  # Return the updated S3 file data
    else:
        # Create a new S3 file
        new_s3_file = S3FileModel(
            s3key=s3_file_data.s3key, file_url=s3_file_data.file_url, workstream=s3_file_data.workstream
        )
        db.add(new_s3_file)
        db.commit()  # Commit the new S3 file to the database
        db.refresh(new_s3_file)  # Refresh to get the new S3 file ID

        # Create the associated content record
        new_content = FileContent(
            s3file_id=new_s3_file.id, content=s3_file_data.content, file_type=s3_file_data.file_type
        )
        db.add(new_content)
        db.commit()  # Commit the new content record to the database

        return new_s3_file


@router.post("/s3files/", response_model=S3File)
def create_s3file(s3file: S3FileCreate, db: Session = Depends(get_db)):
    db_s3file = S3FileModel(**s3file.dict())
    db.add(db_s3file)
    db.commit()
    db.refresh(db_s3file)
    return db_s3file


@router.get("/s3files/{s3file_id}", response_model=S3File)
def read_s3file(s3file_id: int, db: Session = Depends(get_db)):
    db_s3file = db.query(S3FileModel).filter(S3FileModel.id == s3file_id).first()
    if db_s3file is None:
        raise HTTPException(status_code=404, detail="S3File not found")
    return db_s3file


@router.get("/s3files/{s3file_id}/get-all", response_model=S3FileResponseWithAllData, dependencies=[Depends(has_permission("download_from_s3"))])
def read_s3file(s3file_id: int, db: Session = Depends(get_db)):
    db_s3file = db.query(S3FileModel).filter(S3FileModel.id == s3file_id).first()
    if db_s3file is None:
        raise HTTPException(status_code=404, detail="S3File not found")

    workstream = db_s3file.workstream
    # Convert each S3FileModel to S3FileResponse using Pydantic's from_orm
    s3files_response = S3FileResponseWithAllData.from_orm(db_s3file)
    detail = {
            "s3file_id": str(s3file_id),
            "workstream": workstream
        }
    add_to_activity_log(db, user_session.get("user_id"), "DOWNLOAD", detail)
    return s3files_response


from datetime import datetime
from fastapi import HTTPException, Query, Request, Depends
from sqlalchemy.orm import Session

@router.get("/s3files/", response_model=PaginatedS3FilesResponse)
def read_all_s3files(
    request: Request,
    db: Session = Depends(get_db),
    sort: Optional[List[str]] = Query(None, alias="sort"),
    limit: Optional[int] = 25,
    page: Optional[int] = 1,
    workstream: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    query = db.query(S3FileModel)

    # Apply workstream filter if provided
    if workstream:
        query = query.filter(S3FileModel.workstream.ilike(f"%{workstream}%"))

    # Apply date filters if provided
    try:
        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            start_date_obj = datetime.combine(start_date_obj, datetime.min.time())
            query = query.filter(S3FileModel.updated_at >= start_date_obj)

        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            end_date_obj = datetime.combine(end_date_obj, datetime.max.time())
            query = query.filter(S3FileModel.updated_at <= end_date_obj)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    # Apply sorting
    sort_params = request.query_params.getlist("sort")
    if sort_params:
        try:
            for sort_param in sort_params:
                field, order = sort_param.split(",")
                model_field = getattr(S3FileModel, field, None)
                if model_field is not None:
                    order_func = asc if order.upper() == "ASC" else desc
                    query = query.order_by(order_func(model_field))
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        query = query.order_by(desc(S3FileModel.updated_at))

    # Total count
    total = query.count()

    # Calculate page count
    page_count = (total + limit - 1) // limit

    # Pagination
    query = query.offset((page - 1) * limit).limit(limit)

    # Fetch results
    db_s3files = query.all()

    # Handle empty results
    if not db_s3files:
        return PaginatedS3FilesResponse(
            s3_files=[],
            page=page,
            pageSize=limit,
            total=0,
            pageCount=0,
        )

    # Return paginated response
    return PaginatedS3FilesResponse(
        s3_files=[S3FilesResponse.from_orm(s3file) for s3file in db_s3files],
        page=page,
        pageSize=limit,
        total=total,
        pageCount=page_count,
    )


@router.put("/s3files/{s3file_id}", response_model=S3File)
def update_s3file(s3file_id: int, s3file: S3FileUpdate, db: Session = Depends(get_db)):
    db_s3file = db.query(S3FileModel).filter(S3FileModel.id == s3file_id).first()
    if db_s3file is None:
        raise HTTPException(status_code=404, detail="S3File not found")
    for key, value in s3file.dict(exclude_unset=True).items():
        setattr(db_s3file, key, value)
    db.commit()
    db.refresh(db_s3file)
    return db_s3file


@router.delete("/s3files/{s3file_id}", response_model=S3File)
def delete_s3file(s3file_id: int, db: Session = Depends(get_db)):
    db_s3file = db.query(S3FileModel).filter(S3FileModel.id == s3file_id).first()
    if db_s3file is None:
        raise HTTPException(status_code=404, detail="S3File not found")
    db.delete(db_s3file)
    db.commit()
    return db_s3file
    # Check if the S3 file already exists
    existing_s3_file = db.query(S3File).filter(S3File.s3key == s3_file_data.s3key).first()

    if existing_s3_file:
        # Update existing S3 file
        existing_s3_file.file_url = s3_file_data.file_url
        existing_s3_file.workstream = s3_file_data.workstream

        # Update the file contents
        content_record = db.query(FileContent).filter(FileContent.s3file_id == existing_s3_file.id).first()
        if content_record:
            content_record.content = s3_file_data.content
            content_record.file_type = s3_file_data.file_type
        else:
            # Create new content record if it doesn't exist
            new_content = FileContent(
                s3file_id=existing_s3_file.id, content=s3_file_data.content, file_type=s3_file_data.file_type
            )
            db.add(new_content)

        db.commit()  # Save changes to the database
        return existing_s3_file  # Return the updated S3 file data
    else:
        # Create a new S3 file
        new_s3_file = S3File(
            s3key=s3_file_data.s3key, file_url=s3_file_data.file_url, workstream=s3_file_data.workstream
        )
        db.add(new_s3_file)
        db.commit()  # Commit the new S3 file to the database
        db.refresh(new_s3_file)  # Refresh to get the new S3 file ID

        # Create the associated content record
        new_content = FileContent(
            s3file_id=new_s3_file.id, content=s3_file_data.content, file_type=s3_file_data.file_type
        )
        db.add(new_content)
        db.commit()  # Commit the new content record to the database

        return new_s3_file  # Return the newly created S3 file data

@router.get("/s3files-workstream/", response_model=dict)
def get_workstream(db: Session = Depends(get_db)):
    try:
        # Fetch all unique workstream values from the S3FileModel table
        workstreams = db.query(S3FileModel.workstream).distinct().all()

        # Extract the workstream values into a list
        workstream_list = [workstream[0] for workstream in workstreams]

        # Return the unique workstream list in the response
        return {"workstream": workstream_list}
    except Exception as e:
        # Log the exception message for debugging
        logger.error("Error retrieving workstreams: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve workstreams")
    
def add_to_activity_log(db: Session, user_id,action, details):
     # Create the log entry
    log_entry = ActivityLog(
        user_id=user_id,
        action=action,
        resource="s3_files",
        resource_id="log",
        details=details,
    )

    # Use the same connection to insert into the activity_logs table
    try:
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Error logging to database: {e}")

