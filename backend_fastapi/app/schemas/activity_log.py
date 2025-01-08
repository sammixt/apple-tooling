from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

class ActivityLogResponse(BaseModel):
    id: int
    user: Optional[UserResponse]  
    action: str
    resource: str
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]  
    timestamp: datetime

class PaginatedActivityLogResponse(BaseModel):
    logs: List[ActivityLogResponse]  
    page: int  
    pageSize: int  
    total: int  
    pageCount: int  
