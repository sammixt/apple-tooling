from typing import Any, Dict, List, Optional
from uuid import UUID
from app.schema import BasePydantic
from datetime import date, datetime
from app.db.enums import StatusEnum, ValidationErrorTypeEnum, WorkstreamEnum


class WorkstreamResponse(BasePydantic):
    id: int
    name: str


class WorkStreamCreate(BasePydantic):
    name: str


class PreProcessingFileUploadRequest(BasePydantic):
    workstream: WorkstreamEnum
    user_email: str
    user_name: str
    delivery_date: date
    client: str


class PreProcessingFileResponse(BasePydantic):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    batch_id: Optional[str] = None


class BatchResponse(BasePydantic):
    uuid: UUID
    name: Optional[str]
    user_email: Optional[str]
    user_name: Optional[str]
    workstream: WorkstreamEnum
    status: Optional[StatusEnum]
    created_at: datetime
    updated_at: datetime
    is_uploaded: Optional[bool]
    files: List[PreProcessingFileResponse]
    s3_path: Optional[str]
    delivery_date: Optional[date]
    has_validation_error: Optional[bool]
    stats: Optional[Any]


class PaginatedS3FilesResponse(BasePydantic):
    items: List[BatchResponse]
    page: int
    pageSize: int
    total: int
    pageCount: int


class ValidationErrorType(BasePydantic):
    error_type: ValidationErrorTypeEnum
    count: int


class ValidationErrorSummary(BasePydantic):
    error_types: List[ValidationErrorType]
    total_errors: int


class ValidationError(BasePydantic):
    error_message: str
    type: ValidationErrorTypeEnum
    delivery_id: Optional[str]
    link: Optional[str] = None


class ValidationErrorResponse(BasePydantic):
    summary: ValidationErrorSummary
    errors: List[ValidationError]
