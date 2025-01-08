from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.schemas.role import RoleResponse


class UserBase(BaseModel):
    email: str
    profile_pic_url: Optional[str] = None
    name: str
    role_id: int
    is_active: Optional[bool] = False

class UserCreate(UserBase):
    pass


class UpdateUserActiveStatus(BaseModel):
    is_active: Optional[bool] = False

class UserUpdate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        
class UserResponse(BaseModel):
    id: int
    google_auth_id: Optional[str]
    email: str
    profile_pic_url: Optional[str]
    name: str
    is_active: bool
    role: Optional[RoleResponse]
    created_at: datetime
    updated_at: Optional[datetime]
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True  # Enables Pydantic to work with ORM objects