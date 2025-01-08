from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Role, User
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse, PaginatedRolesResponse
from typing import List, Optional
from sqlalchemy import asc, desc, func
from datetime import datetime
from app.auth.dependencies import has_permission


router = APIRouter(
    prefix="/roles",
    tags=["Roles"]
)


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    db_role = db.query(Role).filter(func.lower(Role.name) == func.lower(role.name)).first()
    if db_role:
        if db_role.deleted_at:
            db_role.name = role.name
            db_role.deleted_at = None
            db_role.description = role.description
            db_role.permissions = role.permissions

            db.commit()
            db.refresh(db_role)
            return db_role
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Role with this name already exists."
        )
    new_role = Role(
        name=role.name,
        description=role.description,
        permissions=role.permissions
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role


# @router.get("/", response_model=List[RoleResponse])
# def get_roles(db: Session = Depends(get_db)):
#     roles = db.query(Role).filter(Role.deleted_at.is_(None)).all()
#     return roles

@router.get("/", response_model=PaginatedRolesResponse)
def read_all_roles(
    db: Session = Depends(get_db),
    limit: Optional[int] = Query(25, ge=1, le=100),  # Default limit per page
    page: Optional[int] = Query(1, ge=1),           # Default to the first page
    sort: Optional[str] = Query("created_at,DESC"), # Default sorting by `created_at` descending
):
    try:
        # Base query filtering out soft-deleted roles
        query = db.query(Role).filter(Role.deleted_at.is_(None))

        # Handle sorting
        if sort:
            sort_field, sort_order = sort.split(",")
            sort_column = getattr(Role, sort_field, None)
            if sort_column is None:
                raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_field}")
            if sort_order.upper() == "DESC":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        # Total count of roles
        total = query.count()

        # Calculate total page count
        page_count = (total + limit - 1) // limit

        # Apply pagination
        query = query.offset((page - 1) * limit).limit(limit)

        # Fetch paginated roles
        db_roles = query.all()

        # Handle empty results
        if not db_roles:
            return PaginatedRolesResponse(
                roles=[],
                page=page,
                pageSize=limit,
                total=0,
                pageCount=0,
            )

        # Return the paginated roles response
        return PaginatedRolesResponse(
            roles=[RoleResponse.from_orm(role) for role in db_roles],
            page=page,
            pageSize=limit,
            total=total,
            pageCount=page_count,
        )
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve records")


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(role_id: int, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id, Role.deleted_at.is_(None)).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, role: RoleUpdate, db: Session = Depends(get_db)):
    db_role = db.query(Role).filter(Role.id == role_id, Role.deleted_at.is_(None)).first()
    if not db_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    for key, value in role.dict(exclude_unset=True).items():
        setattr(db_role, key, value)

    existing_db_role = db.query(Role).filter(func.lower(Role.name) == func.lower(role.name), Role.id != role_id).first()
    if existing_db_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Role with this name already exists."
        )
    db_role.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_role)
    return db_role

@router.get("/role-list/all", response_model=List[RoleResponse])
def read_all_roles(
    db: Session = Depends(get_db),
):
    try:
        # Query to fetch roles excluding soft-deleted ones, sorted by name ascending
        db_roles = db.query(Role).filter(Role.deleted_at.is_(None)).order_by(Role.name.asc()).all()

        # Return the roles response directly
        return [RoleResponse.from_orm(role) for role in db_roles]
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve records")

@router.delete("/{role_id}", response_model=RoleResponse)
def delete_role(role_id: int, db: Session = Depends(get_db)):
    # Fetch the role, ensuring it has not been deleted
    role = db.query(Role).filter(Role.id == role_id, Role.deleted_at.is_(None)).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Check if the role is assigned to any user
    user_count = db.query(User).filter(User.role_id == role_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role cannot be deleted as it is assigned to {user_count} user(s)."
        )

    # Soft delete the role
    role.soft_delete(db)
    return role