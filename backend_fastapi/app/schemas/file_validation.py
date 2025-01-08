from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional

class FileValidationBase(BaseModel):
    validation_type: str
    validation_errors: Optional[Any] = None

class FileValidationCreate(FileValidationBase):
    pass

class FileValidationUpdate(FileValidationBase):
    pass

class FileValidation(FileValidationBase):
    id: int
    s3file_id: int
    created_at: datetime
    updated_at: Optional[datetime] = Field(None)

    class Config:
        from_attributes = True
