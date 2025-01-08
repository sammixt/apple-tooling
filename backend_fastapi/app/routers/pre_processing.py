from datetime import date, datetime
import io
import logging
from typing import List, Dict, Any, Optional
import uuid
import boto3
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Request, Form, Query
from sqlalchemy.orm import Session
from app.auth.jwt import create_access_token
from app.core.s3_client import S3Client
from app.jobs.celery_task import process_colab_link
from app.service.delivery_validation.validation import Validator
from app.middleware.limiter import limiter
from app.context.preprocessing_context import PreProcessingContextFactory
from app.db.database import get_db
from app.db.enums import StatusEnum, WorkstreamEnum, ClientEnum
from app.db.models import Batch, DeliveryJson, PreProcessingFile, PreProcessingFileJson, User, ValidationError, ConfigOption, ActivityLog
from app.middleware.memory_check import memory_check_middleware
from app.schemas.pre_processing import (
    BatchResponse,
    PaginatedS3FilesResponse,
    PreProcessingFileResponse,
    PreProcessingFileUploadRequest,
    ValidationErrorResponse,
)
from fastapi.responses import StreamingResponse, JSONResponse
import asyncio
import json
import csv
import re
from celery.result import AsyncResult
from app.config import settings
from sqlalchemy import cast,func,String
from pydantic import BaseModel
from collections import Counter
from app.service.json_conversion.sft_reasoning import (
    authenticate_drive,
    convert_ipynb_to_py,
    download_ipynb,
    extract_file_id,
    parse_agent_colab_notebooks,
    parse_code_colab_notebooks,
    parse_other_colab_notebooks,
    process_file_content,
    validate_notebook_json,
)
from app.utils.error_handler_for_colab import handle_error_for_colab_link
from app.auth.dependencies import user_session
from sqlalchemy import asc, desc

s3 = S3Client()


class ValidationRequest(BaseModel):
    json_data: Dict[str, Any]


class ColabLinksRequest(BaseModel):
    links: list[str]
    type: str
    user_email: str
    user_name: str
    delivery_date: date


from app.auth.dependencies import get_current_user, has_permission


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/")
# @limiter.limit("1/5minute")  # Allow 1 request every 5 minutes per IP address
@memory_check_middleware(min_memory_gb=1)
async def upload_json(
    request: Request,
    files: List[UploadFile] = File(...),
    request_data: PreProcessingFileUploadRequest = Depends(),
    db: Session = Depends(get_db),
):
    try:
        if not files or len(files) < 1:
            raise HTTPException(status_code=400, detail="At least one file is required.")

        # Check total file size (500MB = 500 * 1024 * 1024 bytes)
        MAX_TOTAL_SIZE = 800 * 1024 * 1024  # 500MB in bytes
        total_size = 0

        for file in files:
            # Get file size from the file object
            file.file.seek(0, 2)  # Seek to end of file
            file_size = file.file.tell()  # Get current position (file size)
            file.file.seek(0)  # Reset file position to beginning

            total_size += file_size

            if total_size > MAX_TOTAL_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"Total file size exceeds maximum limit of 500MB. Current total: {total_size / (1024 * 1024):.2f}MB",
                )

        upload_date_restriction = db.query(ConfigOption).filter_by(name="upload_date_restriction").first()
        upload_date_restriction_value = upload_date_restriction.value if upload_date_restriction else False

        if upload_date_restriction_value:
        # Validate delivery date range
            current_date = datetime.now().date()
            delivery_date = request_data.delivery_date
            date_diff = abs((delivery_date - current_date).days)

            if date_diff > 7:
                raise HTTPException(
                    status_code=400, detail="Delivery date must be within 1 week before or after the current date"
                )

        client_enum = ClientEnum.PENGUIN if not request_data.client else ClientEnum(request_data.client)

        # Create context using factory
        context = PreProcessingContextFactory.create_context(request_data.workstream, db)

        # Create and set batch
        batch_id = uuid.uuid4()
        name = PreProcessingContextFactory.get_batch_name(request_data.workstream, request_data.delivery_date)

        batch = Batch(
            id=batch_id,
            workstream=request_data.workstream,
            user_email=request_data.user_email,
            user_name=request_data.user_name,
            delivery_date=request_data.delivery_date,
            name=name,
            client=client_enum.value
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        context.set_batch(batch)

        # Process files using the selected strategy
        for file in files:
            await context.process_file(file)

        if not batch.status == StatusEnum.FAILED:
            # Execute tasks using strategy
            await context.execute_tasks()

        db.commit()
        detail = {
            "batch_id": str(batch_id),
            "batch":name, 
            "status": batch.status.value,
            "client": client_enum.value
        }
        add_to_activity_log(db, user_session.get("user_id"), "UPLOAD", detail, "activity")
        return {"message": "JSON data stored successfully"}
    except HTTPException as he:
        # Re-raise HTTP exceptions directly to preserve their original status code and detail
        raise he
    except Exception as e:
        db.rollback()
        logger.error(f"Error in upload_json: {str(e)}")
        # Extract the status code if present in the error message
        if ": " in str(e):
            try:
                status_code = int(str(e).split(":")[0])
                detail = str(e).split(":", 1)[1].strip()
                raise HTTPException(status_code=status_code, detail=detail)
            except ValueError:
                pass
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


# Define the generator function for SSE
async def event_stream(progress_percentage):
    while progress_percentage < 100:
        progress_percentage = progress_percentage + 1
        await asyncio.sleep(1)  # Control the frequency of updates
        yield f"data: {json.dumps({'progress': progress_percentage})}\n\n"


# Define the SSE endpoint
@router.get("/stream/{id}")
async def stream(id: int):
    return StreamingResponse(event_stream(0), media_type="text/event-stream")


@router.get("/", response_model=PaginatedS3FilesResponse)
async def get_jsons(
    sort: Optional[List[str]] = Query(None, alias="sort"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    workstream: Optional[str] = None,
    limit: Optional[int] = 25,
    page: Optional[int] = 1,
    db: Session = Depends(get_db),
):
    try:
        query = db.query(Batch).order_by(Batch.created_at.desc())

        if start_date:
            query = query.filter(Batch.created_at >= start_date)
        if end_date:
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.filter(Batch.created_at <= end_date)
        if workstream:
            query = query.filter(func.upper(cast(Batch.workstream, String)).ilike(f"%{workstream.upper()}%"))

        # Apply sorting
        if sort:
            try:
                for sort_param in sort:
                    field, order = sort_param.split(",")
                    model_field = getattr(Batch, field, None)
                    if model_field is not None:
                        order_func = asc if order.upper() == "ASC" else desc
                        query = query.order_by(order_func(model_field))
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        else:
            query = query.order_by(desc(Batch.updated_at))

        total = query.count()
        page_count = (total + limit - 1) // limit

        if page and limit:
            query = query.offset((page - 1) * limit).limit(limit)

        results = query.all()
        return PaginatedS3FilesResponse(
            items=[
                BatchResponse(
                    uuid=s3file.id,
                    name=s3file.name,
                    created_at=s3file.created_at,
                    updated_at=s3file.updated_at,
                    status=s3file.status,
                    workstream=s3file.workstream,
                    user_email=s3file.user_email,
                    user_name=s3file.user_name,
                    is_uploaded=s3file.is_uploaded,
                    s3_path=s3file.s3_path,
                    has_validation_error=s3file.has_validation_error,
                    delivery_date=s3file.delivery_date,
                    stats=s3file.stats,
                    files=[
                        PreProcessingFileResponse(
                            id=file.id,
                            name=file.name,
                            created_at=file.created_at,
                            updated_at=file.updated_at,
                        )
                        for file in s3file.preprocessing_files
                    ],
                )
                for s3file in results
            ],
            page=page,
            pageSize=limit,
            total=total,
            pageCount=page_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve records")


@router.post("/task-status/{task_id}")
async def task_status(task_id: str):
    task = AsyncResult(task_id)
    if task.state == "PENDING":
        return {"status": "Task is still pending"}
    elif task.state == "SUCCESS":
        return {"status": "Task completed successfully", "result": task.result}
    elif task.state == "FAILURE":
        return {"status": "Task failed", "error": task.info}
    return {"status": task.state}


# @router.get("/remove-delivery-with-errors/{preprocessing_file_id}")
# async def remove_delivery_with_errors(preprocessing_file_id: int, db: Session = Depends(get_db)):
#     # Getting the file content based on preprocessing_file_id
#     pre_processing_file_json = (
#         db.query(PreProcessingFileJson)
#         .filter(PreProcessingFileJson.preprocessing_file_id == preprocessing_file_id)
#         .first()
#     )

#     if not pre_processing_file_json:
#         raise HTTPException(status_code=404, detail="Pre Processing File Json Data not found")

#     # Geting all errors list based on preprocessing_file_id
#     errors = db.query(ValidationError).filter(ValidationError.preprocessing_file_id == preprocessing_file_id).all()

#     if not errors:
#         return {"message": "No errors found, no changes made"}

#     # Parsing the content and remove objects matching delivery_id from errors list
#     content = pre_processing_file_json.content
#     # Assuming content is a JSON string, use json.loads() to parse it
#     try:
#         content = json.loads(content)  # as content is in string format in db
#     except json.JSONDecodeError as e:
#         raise HTTPException(status_code=400, detail=f"Invalid JSON format in content: {str(e)}")

#     delivery_ids_to_remove = [str(error.delivery_id) for error in errors]  # Ensure delivery_id is a string

#     # Filter out objects where 'deliverable_id' matches a delivery_id in the errors
#     filtered_content = [obj for obj in content if str(obj.get("deliverable_id", "")) not in delivery_ids_to_remove]

#     # Update the filtered PreProcessingFileJson content in the database
#     pre_processing_file_json.content = json.dumps(filtered_content)
#     db.commit()

#     # Remove all the errors for this preprocessing_file_id
#     db.query(ValidationError).filter(ValidationError.preprocessing_file_id == preprocessing_file_id).delete()

#     db.commit()

#     return {"message": "Content updated and errors removed successfully"}


@router.post("/convert-colab-link-to-json")
async def convert_colab_link_to_json(link: str, client: str, annotator_email: Optional[str] = None):
    drive_service = authenticate_drive()
    try:
        file_id = extract_file_id(link)
        ipynb_content = download_ipynb(drive_service, file_id)
        py_content = convert_ipynb_to_py(ipynb_content)

        # Determine category and patterns
        category_match = re.search(r"(?i)\*\*Category\:\*\*\s*-\s*([^\n]*)", py_content)
        category = category_match.group(1).strip() if category_match else "General"

        type = "General"
        if category.lower() == "agent":
            type = "Agent"
        elif category.lower() == "coding":
            if re.search(r"(?i)\*\*\[CHAIN", py_content) and re.search(r"(?i)\*\*\[THOUGHT", py_content):
                type = "Coding"

        json_data = process_file_content(type, py_content, annotator_email, client, file_id)
        return JSONResponse(status_code=200, content=json_data)
    except Exception as e:
        error_response = handle_error_for_colab_link(e, link)
        # Return the structured error response
        return JSONResponse(status_code=400, content=error_response)


# @router.post("/convert-colab-code-to-json")
# async def convert_colab_code_to_json(
#     file: UploadFile = File(...),
# ):
#     filename = file.filename
#     if not filename.endswith(".py"):
#         raise HTTPException(status_code=400, detail="File must be a Python (.py) file")

#     try:
#         contents = await file.read()
#         data = contents.decode("utf-8")
#         if "Automatically generated by Colab" not in data:
#             raise HTTPException(status_code=400, detail="This file is not exported by Colab")

#         final_json = parse_code_colab_notebooks(data)
#     except Exception as e:
#         raise HTTPException(status_code=400, detail="Error occurred. Check file format and try again! " + str(e))

#     return JSONResponse(status_code=200, content=final_json)


# @router.post("/convert-colab-to-json")
# async def convert_colab_to_json(
#     file: UploadFile = File(...),
# ):
#     filename = file.filename
#     if not filename.endswith(".py"):
#         raise HTTPException(status_code=400, detail="File must be a Python (.py) file")

#     try:
#         contents = await file.read()
#         data = contents.decode("utf-8")
#         if "Automatically generated by Colab" not in data:
#             raise HTTPException(status_code=400, detail="This file is not exported by Colab")

#         final_json = parse_other_colab_notebooks(data)
#     except Exception as e:
#         raise HTTPException(status_code=400, detail="Error occurred. Check file format and try again! " + str(e))

#     return JSONResponse(status_code=200, content=final_json)


# @router.post("/validate-tool-colab-notebook-json")
# def validate_tool_colab_notebook_json(request: ValidationRequest):
#     errors = []
#     data = request.json_data
#     errors = validate_notebook_json(data)
#     return errors or None


# @router.post("/convert-colab-tool-to-json")
# async def convert_colab_tool_to_json(
#     file: UploadFile = File(...),
# ):
#     filename = file.filename
#     if not filename.endswith(".py"):
#         raise HTTPException(status_code=400, detail="File must be a Python (.py) file")

#     try:
#         contents = await file.read()
#         data = contents.decode("utf-8")
#         if "Automatically generated by Colab" not in data:
#             raise HTTPException(status_code=400, detail="This file is not exported by Colab")

#         final_json = parse_agent_colab_notebooks(data)

#     except Exception as e:
#         print(e)
#         raise HTTPException(status_code=400, detail="Error occurred. Check file format and try again! " + str(e))

#     return JSONResponse(status_code=200, content=final_json)


@router.get("/errors/", response_model=ValidationErrorResponse)
def get_errors_by_batch(batch_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get both a summary and detailed list of validation errors for a batch.
    """
    # Check if batch exists
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch with id {batch_id} not found")

    # Get error summary grouped by type
    error_summary = (
        db.query(ValidationError.type, func.count(ValidationError.id).label("count"))
        .filter(ValidationError.batch_id == batch_id)
        .group_by(ValidationError.type)
        .all()
    )

    # Get detailed error list
    error_list = (
        db.query(ValidationError).filter(ValidationError.batch_id == batch_id).order_by(ValidationError.type).all()
    )

    return ValidationErrorResponse(
        summary={
            "error_types": [{"error_type": error_type.value, "count": count} for error_type, count in error_summary],
            "total_errors": sum(count for _, count in error_summary),
        },
        errors=[
            {
                "type": error.type,
                "error_message": error.error_message,
                "delivery_id": error.delivery_id,
                "link": error.link,
            }
            for error in error_list
        ],
    )


@router.get("/delivery-file/", dependencies=[Depends(has_permission("download_from_s3"))])
def get_delivery_file(batch_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    view/download delivery file from batch id.
    """
    delivery_json = db.query(DeliveryJson).filter(DeliveryJson.batch_id == batch_id).first()

    if not delivery_json:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    detail = {
            "batch_id": str(batch_id)
        }
    add_to_activity_log(db, user_session.get("user_id"), "DOWNLOAD_FROM_S3", detail, "delivery_files")

    return JSONResponse(content=delivery_json.content)



@router.post("/uoload-s3/", dependencies=[Depends(has_permission("upload_to_s3"))])
def upload_to_s3(batch_id: uuid.UUID, s3_bucket: str = None, db: Session = Depends(get_db)):
    """
    Upload a batch to S3.
    """
    delivery_file = db.query(DeliveryJson).filter(DeliveryJson.batch_id == batch_id).first()
    if not delivery_file:
        raise HTTPException(status_code=404, detail="Delivery file not found")

    apple_upload_value = get_apple_upload_value(db)

    json_content = json.dumps(delivery_file.content)
    json_file = io.BytesIO(json_content.encode("utf-8"))

    # Determine S3 client and bucket name based on provided arguments and system configurations
    s3_client, aws_bucket_name, is_penguin_s3 = select_s3_client_and_bucket(
        s3_bucket, apple_upload_value, db, batch_id
    )
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).one()
        key = build_s3_key(batch)
        
        # Upload the file to S3
        s3_client.upload_fileobj(json_file, aws_bucket_name, key)
        s3_path = f"s3://{aws_bucket_name}/{key}"
        
        # Update batch record and log the activity
        update_batch_and_log_activity(db, batch, batch_id, s3_path, is_penguin_s3)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")

    return {"message": "Files uploaded successfully to S3", "url": s3_path}


def get_apple_upload_value(db: Session) -> bool:
    """Retrieve whether Penguin S3 upload is enabled."""
    apple_upload = db.query(ConfigOption).filter_by(name="enable_penguin_s3_upload").first()
    return apple_upload.value if apple_upload else False


def select_s3_client_and_bucket(
    s3_bucket: str, apple_upload_value: bool, db: Session, batch_id: uuid.UUID
) -> tuple:
    """Select the correct S3 client and bucket based on the request and configuration."""
    is_penguin_s3 = False

    # Determine the S3 client and bucket based on the input `s3_bucket` and the app configuration
    if not s3_bucket:
        if apple_upload_value:
            s3._refresh_if_credentials_expired()
            s3_client = s3.s3_client
            aws_bucket_name = settings.AWS_BUCKET_NAME
            is_penguin_s3 = True
        else:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.DEV_AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.DEV_AWS_SECRET_ACCESS_KEY,
            )
            aws_bucket_name = settings.DEV_AWS_BUCKET_NAME
    else:
        if s3_bucket == "penguin":
            s3._refresh_if_credentials_expired()
            s3_client = s3.s3_client
            aws_bucket_name = settings.AWS_BUCKET_NAME
            is_penguin_s3 = True
        elif s3_bucket == "turing":
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.DEV_AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.DEV_AWS_SECRET_ACCESS_KEY,
            )
            aws_bucket_name = settings.DEV_AWS_BUCKET_NAME

    # If apple upload is enabled and client isn't penguin, override the s3 client and bucket
    if apple_upload_value and db.query(Batch).filter(Batch.id == batch_id).one().client != ClientEnum.PENGUIN.value:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.DEV_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.DEV_AWS_SECRET_ACCESS_KEY,
        )
        aws_bucket_name = settings.DEV_AWS_BUCKET_NAME
        is_penguin_s3 = False

    return s3_client, aws_bucket_name, is_penguin_s3


def build_s3_key(batch: Batch) -> str:
    """Construct the S3 key based on batch workstream."""
    folder_date = batch.delivery_date.strftime("%Y%m%d")
    name = batch.name
    
    match batch.workstream:
        case WorkstreamEnum.RLHF_VISION:
            return f"2410-rlhf-vision/_raw/{folder_date}/{name}"
        case WorkstreamEnum.IMAGE_EVAL:
            return f"2410-eval-results/_raw/{folder_date}/{name}"
        case WorkstreamEnum.SFT_REASONING:
            return f"2410-sft-reasoning/_raw/{folder_date}/{name}"
        case WorkstreamEnum.RLHF_TEXT:
            return f"2410-rlhf-text/_raw/{folder_date}/{name}"
        case WorkstreamEnum.SFT_CODE_INT:
            return f"2412-sft-swift-code-interpreter/_raw/{folder_date}/{name}"


def update_batch_and_log_activity(
    db: Session, batch: Batch, batch_id: uuid.UUID, s3_path: str, is_penguin_s3: bool
):
    """Update batch and log the activity."""
    batch.is_uploaded = True
    batch.s3_path = s3_path
    db.commit()
    
    # Log the activity
    detail = {
        "batch_id": str(batch_id),
        "batch": batch.name,
        "s3_path": s3_path,
        "s3_bucket": "penguin" if is_penguin_s3 else "turing"
    }
    message = "UPLOAD_TO_PENGUIN_S3" if is_penguin_s3 else "UPLOAD_TO_TURING_S3"
    add_to_activity_log(db, user_session.get("user_id"), message, detail, "activity")



@router.get("/workstreams/", response_model=List[dict])
async def list_workstreams():
    """
    Get a list of available workstreams.
    """
    return PreProcessingContextFactory.get_available_workstreams()

@router.get("/clients/", response_model=List[dict])
async def list_workstreams():
    """
    Get a list of available clients.
    """
    return PreProcessingContextFactory.get_clients()


@router.post("/colab/")
async def process_colab(
    file: UploadFile = File(...),
    user_email: str = Form(...),
    user_name: str = Form(...),
    delivery_date: date = Form(...),
    client: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        # Ensure the file is a CSV
        if not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")

        # Validate delivery date range
        current_date = datetime.now().date()
        date_diff = abs((delivery_date - current_date).days)
        if date_diff > 7:
            raise HTTPException(
                status_code=400, detail="Delivery date must be within 1 week before or after the current date"
            )
        if not client:
            raise HTTPException(status_code=400, detail="Client is required")
        
        client_enum = ClientEnum(client)
            
        
        content = await file.read()
        decoded = content.decode("utf-8").splitlines()
        csv_reader = csv.DictReader(decoded)

        # Ensure "ColabLinks" header exists
        if "ColabLinks" not in csv_reader.fieldnames:
            raise HTTPException(status_code=400, detail="CSV must contain 'ColabLinks' header.")

        links = []
        ids = []
        invalid_links = []

        # Validate links and check for duplicates
        colab_link_pattern = r"^https:\/\/colab\.research\.google\.com\/drive\/[\w_-]+$"
        for row in csv_reader:
            link = row.get("ColabLinks")
            id = row.get("EmailId")
            if link:
                if re.match(colab_link_pattern, link):
                    links.append(link)
                    ids.append(id)
                else:
                    invalid_links.append(link)

        if invalid_links:
            raise HTTPException(
                status_code=400, detail=f"The following links are invalid Colab notebook links: {invalid_links}"
            )

        # Check for duplicates within the CSV
        # duplicate_links = [link for link, count in Counter(links).items() if count > 1]
        # if duplicate_links:
        #     links = list(dict.fromkeys(links))

        workstream = WorkstreamEnum.SFT_REASONING

        # Create context using factory
        context = PreProcessingContextFactory.create_context(workstream, db)

        # Create and set batch
        batch_id = uuid.uuid4()
        name = PreProcessingContextFactory.get_batch_name(workstream, delivery_date)

        batch = Batch(
            id=batch_id,
            workstream=workstream,
            user_email=user_email,
            user_name=user_name,
            delivery_date=delivery_date,
            name=name,
            client=client_enum.value
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        context.set_batch(batch)

        for link in links:
            files = PreProcessingFile(
                batch_id=batch.id,
                name=link,
            )
            db.add(files)
            db.commit()

        process_colab_link.delay(links, ids, batch_id, client_enum.value)

        db.commit()
        return {"message": "Colab links uploaded successfully"}

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logger.error(f"Error in upload_json: {str(e)}")
        # Extract the status code if present in the error message
        if ": " in str(e):
            try:
                status_code = int(str(e).split(":")[0])
                detail = str(e).split(":", 1)[1].strip()
                raise HTTPException(status_code=status_code, detail=detail)
            except ValueError:
                pass
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.get("/token/")
async def get_token(
    user: User = Depends(get_current_user)
):
    print("user", user.email)
    try:
        token = create_access_token(
            {
                "id": user.id,
                "sub": user.google_auth_id,
                "name": user.name,
                "profile_pic_url": user.profile_pic_url,
                "email": user.email,
            }
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "email": user.email,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def add_to_activity_log(db: Session, user_id,action, details, resource):
     # Create the log entry
    log_entry = ActivityLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id="log",
        details=details,
    )

    # Use the same connection to insert into the activity_logs table
    try:
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Error logging to database: {e}")
