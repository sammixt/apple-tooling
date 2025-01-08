from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from app.db.database import get_db
from app.schemas.user import UserCreate, UserUpdate, User, UserResponse, UpdateUserActiveStatus
from app.db.models import User as UserModel
from app.db.models import Role
from typing import Optional, Dict,List
from datetime import datetime
import traceback
from sqlalchemy.sql import func
from app.auth.dependencies import has_permission, get_current_user

router = APIRouter()

@router.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if not user.email.endswith('@turing.com'):
        raise HTTPException(status_code=500, detail="User outside the organization is not allowed.")
    if not user.role_id:
        raise HTTPException(status_code=500, detail="User without the role is not allowed.")

    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists.")

    db_user = UserModel(email=user.email, name=user.name, role_id=user.role_id, is_active=user.is_active, profile_pic_url=user.profile_pic_url, updated_at=func.now())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/", response_model=Dict)
def get_users(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    role_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort: Optional[str] = Query("created_at,DESC"),
    db: Session = Depends(get_db),
):
    try:
        # Query users with role eagerly loaded
        query = db.query(UserModel).outerjoin(Role).options(
            joinedload(UserModel.role)
        )

        # Apply date filters
        if start_date:
            start_date = datetime.combine(start_date, datetime.min.time())
            query = query.filter(UserModel.created_at >= start_date)
        if end_date:
            end_date = datetime.combine(end_date, datetime.max.time())
            query = query.filter(UserModel.created_at <= end_date)
        if role_id:
            query = query.filter(UserModel.role_id == role_id)

        # Handle sorting
        if sort:
            sort_field, sort_order = sort.split(",")
            sort_column = getattr(UserModel, sort_field, None)
            if sort_column is None:
                raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_field}")
            if sort_order.upper() == "DESC":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        # Pagination
        total = query.count()
        offset = (page - 1) * limit
        db_users = query.offset(offset).limit(limit).all()

        # Prepare response
        return {
            "users": [UserResponse.from_orm(user) for user in db_users],  # Convert using Pydantic
            "page": page,
            "limit": limit,
            "total": total,
            "pageCount": (total + limit - 1) // limit,
        }

    except Exception as e:
        print("Error:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve records")

@router.get("/users/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).outerjoin(Role).options(
            joinedload(UserModel.role)
        ).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, data: dict, db: Session = Depends(get_db)):
    # Fetch the user from the database
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields dynamically
    for key, value in data.items():
        if hasattr(db_user, key):  # Ensure field exists on the model
            setattr(db_user, key, value)
        else:
            raise HTTPException(status_code=400, detail=f"Field '{key}' does not exist on UserModel")

    # Commit changes to the database
    db_user.updated_at = func.now()
    db.commit()
    db.refresh(db_user)

    return db_user

@router.put("/users/{user_id}/update-status", response_model=User)
def update_user_status(user_id: int, data: UpdateUserActiveStatus, db: Session = Depends(get_db)):
    # Fetch the user from the database
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Commit changes to the database
    db_user.is_active = data.is_active
    db_user.updated_at = func.now()
    db.commit()
    db.refresh(db_user)

    return db_user


@router.delete("/users/{user_id}", response_model=User)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return db_user
