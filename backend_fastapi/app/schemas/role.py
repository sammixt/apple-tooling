from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime


# Base schema
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Dict[str, bool]


# Schema for creating a role
class RoleCreate(RoleBase):
    pass


# Schema for updating a role
class RoleUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    permissions: Optional[Dict[str, bool]]


# Schema for response
class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaginatedRolesResponse(BaseModel):
    roles: List[RoleResponse]
    page: int
    pageSize: int
    total: int
    pageCount: int
