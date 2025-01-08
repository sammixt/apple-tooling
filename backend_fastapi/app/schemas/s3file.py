from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict
from app.schemas.stat import Stat
from app.schemas.file_content import FileContent
from app.schemas.file_validation import FileValidation

class S3FileBase(BaseModel):
    s3key: str
    file_url: str
    workstream: Optional[str] = None
    annotator_id: Optional[int] = None

class S3FileCreateUpdate(S3FileBase):
    content: Dict[str, str]
    file_type: str

class S3FileCreate(S3FileBase):
    action: str

class S3FileUpdate(S3FileBase):
    pass

class S3File(S3FileBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = Field(None)

    class Config:
        from_attributes = True

class S3FilesResponse(S3FileBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = Field(None)
    file_stats: Optional[Stat] = Field(None)

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class S3FileResponseWithAllData(S3FileBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = Field(None)
    file_stats: Optional[Stat] = Field(None)
    file_content: FileContent = Field(None)
    file_validations: List[FileValidation] = []

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class PaginatedS3FilesResponse(BaseModel):
    s3_files: List[S3FilesResponse]
    page: int
    pageSize: int
    total: int
    pageCount: int


class WebhookPayload(BaseModel):
    bucket: str
    changes: List[S3FileCreate]
