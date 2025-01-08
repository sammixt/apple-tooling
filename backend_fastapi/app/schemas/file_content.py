from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional

class FileContentBase(BaseModel):
    content: Any
    file_type: str
    s3file_id: int

class FileContentCreate(FileContentBase):
    pass

class FileContentUpdate(FileContentBase):
    pass

class FileContent(FileContentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = Field(None)

    class Config:
        from_attributes = True
