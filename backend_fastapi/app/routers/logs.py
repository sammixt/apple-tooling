from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import or_
from app.db.database import get_db
from app.db.models import Log, ActivityLog, User
from app.schemas.logger import LoggerResponse
from typing import Optional, List
from datetime import datetime
import traceback
from datetime import datetime, timedelta
from app.schemas.activity_log import PaginatedActivityLogResponse, ActivityLogResponse
from sqlalchemy import asc, desc

router = APIRouter()


@router.get("/logs/", response_model=dict)
def get_logs(
    start_date: Optional[datetime] = Query(None), 
    end_date: Optional[datetime] = Query(None),  
    log_level: Optional[str] = Query(None),  # Change datetime to str for log_level
    page: int = Query(1, ge=1),  # Default page is 1, ensure it's at least 1
    limit: int = Query(10, ge=1, le=100),  # Default page size is 10, max size 100
    db: Session = Depends(get_db),
):
    try:
        query = db.query(Log)

        # Apply date filters
        if start_date:
            start_date = datetime.combine(start_date, datetime.min.time())  # Set time to 00:00:00
            query = query.filter(Log.created_at >= start_date)
        if end_date:
            end_date = datetime.combine(end_date, datetime.max.time())  # Set time to 23:59:59
            query = query.filter(Log.created_at <= end_date)

        if log_level:
            query = query.filter(Log.log_level == log_level)

        # Order by created_at in descending order
        query = query.order_by(Log.created_at.desc())

        # Get total count of logs (for calculating total pages)
        total = query.count()

        # Calculate the offset based on the page number and page size
        offset = (page - 1) * limit

        # Fetch the logs with pagination
        logs = query.offset(offset).limit(limit).all()

        # Calculate total page count
        page_count = (total + limit - 1) // limit  # Round up division for page count

        # Return the final response
        return {
            "items": [LoggerResponse.from_orm(log) for log in logs],  # Convert logs to Pydantic model
            "page": page,
            "limit": limit,
            "total": total,
            "pageCount": page_count
        }

    except Exception as e:
        print("============ START ==========")
        print(e)
        print("Traceback:")
        traceback.print_exc()
        print("============ END ==========")
        raise HTTPException(status_code=500, detail="Failed to retrieve records")

@router.get("/log-levels", response_model=dict)  # Returning a dict with unique log levels
def get_log_levels(db: Session = Depends(get_db)):
    try:
        # Fetch all unique log_level values from the Log table
        log_levels = db.query(Log.log_level).distinct().all()

        # Extract the log_level values into a list of strings
        log_level_list = [log_level[0] for log_level in log_levels]

        # Return the unique log levels
        return {
            "logLevels": log_level_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve log levels")

@router.get("/activity-logs/", response_model=PaginatedActivityLogResponse)
def fetch_activity_logs(
    request: Request,
    db: Session = Depends(get_db),
    sort: Optional[List[str]] = Query(None, alias="sort"),
    limit: Optional[int] = 25,
    page: Optional[int] = 1,
    s: Optional[str] = None,  # Search term for resource or user name
    user_name: Optional[str] = None,
    start_date: Optional[datetime] = None,  # Optional start date filter
    end_date: Optional[datetime] = None,  # Optional end date filter
):
    query = db.query(ActivityLog).options(joinedload(ActivityLog.user))
    
    # Apply date filters
    if start_date:
        # Set time to 00:00:00 for start date filter
        start_date = datetime.combine(start_date, datetime.min.time())
        query = query.filter(ActivityLog.timestamp >= start_date)
        
    if end_date:
        # Set time to 23:59:59 for end date filter
        end_date = datetime.combine(end_date, datetime.max.time())
        query = query.filter(ActivityLog.timestamp <= end_date)
    
    # Search on resource or user name
    if s:
        query = query.join(User, ActivityLog.user_id == User.id, isouter=True).filter(
            or_(
                ActivityLog.resource.ilike(f"%{s}%"), 
                User.name.ilike(f"%{s}%")
            )
        )

    # Search on resource or user name
    if user_name:
        query = query.join(User, ActivityLog.user_id == User.id, isouter=True).filter(
            User.name.ilike(f"%{user_name}%")
        )

    # Sorting
    if sort:
        try:
            for sort_param in sort:
                field, order = sort_param.split(",")
                model_field = getattr(ActivityLog, field, None)
                if model_field is not None:
                    order_func = asc if order.upper() == "ASC" else desc
                    query = query.order_by(order_func(model_field))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid sort parameter: {e}")
    else:
        query = query.order_by(ActivityLog.timestamp.desc())  # Default sort by timestamp descending

    # Total count
    total = query.count()

    # Pagination
    if page and limit:
        query = query.offset((page - 1) * limit).limit(limit)

    activity_logs = query.all()

    # Transform response
    return PaginatedActivityLogResponse(
        logs=[
            ActivityLogResponse(
                id=log.id,
                user={"id": log.user.id, "name": log.user.name, "email": log.user.email} if log.user else None,
                action=log.action,
                resource=log.resource,
                resource_id=log.resource_id,
                details=log.details,
                timestamp=log.timestamp,
            )
            for log in activity_logs
        ],
        page=page,
        pageSize=limit,
        total=total,
        pageCount=(total + limit - 1) // limit,
    )
