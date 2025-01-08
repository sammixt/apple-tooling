import enum
import uuid
from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Date,
    Enum,
    Integer,
    String,
    ForeignKey,
    JSON,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
from app.db.database import Base
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.db.enums import StatusEnum, ValidationErrorTypeEnum, WorkstreamEnum, ClientEnum
from app.models import TimeStampMixin
from datetime import datetime, timezone

# User model
class User(Base):
    __tablename__ = "users"  # Changed to plural for consistency

    id = Column(Integer, primary_key=True, index=True)
    google_auth_id = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=False)
    profile_pic_url = Column(String, nullable=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    activity_logs = relationship("ActivityLog", back_populates="user", lazy="dynamic")
    role = relationship("Role", back_populates="users")


# S3File model
class S3File(Base):
    __tablename__ = "s3_files"

    id = Column(Integer, primary_key=True, index=True)
    s3key = Column(String, unique=True, index=True, nullable=False)
    file_url = Column(String, nullable=False)
    workstream = Column(String, nullable=True)
    annotator_id = Column(Integer, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    file_stats = relationship("Stat", back_populates="s3file", cascade="all, delete-orphan", uselist=False)
    file_content = relationship(
        "FileContent",
        back_populates="s3file",
        cascade="all, delete-orphan",
        uselist=False,
    )
    file_validations = relationship("FileValidation", back_populates="s3file", cascade="all, delete-orphan")


# Stat model
class Stat(Base):
    __tablename__ = "file_stats"

    id = Column(Integer, primary_key=True, index=True)
    s3file_id = Column(Integer, ForeignKey("s3_files.id"), nullable=False)  # Updated to s3_files
    stats_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    s3file = relationship("S3File", back_populates="file_stats")


# FileContent model
class FileContent(Base):
    __tablename__ = "file_contents"

    id = Column(Integer, primary_key=True, index=True)
    s3file_id = Column(Integer, ForeignKey("s3_files.id"), nullable=False)  # Updated to s3_files
    content = Column(JSON, nullable=False)
    file_type = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    s3file = relationship("S3File", back_populates="file_content")


# FileValidation model
class FileValidation(Base):
    __tablename__ = "file_validations"

    id = Column(Integer, primary_key=True, index=True)
    s3file_id = Column(Integer, ForeignKey("s3_files.id"), nullable=False)  # Updated to s3_files
    validation_type = Column(String, nullable=False)
    validation_errors = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    s3file = relationship("S3File", back_populates="file_validations")

    __table_args__ = (UniqueConstraint("s3file_id", "validation_type", name="uq_s3file_validation_type"),)


class PreProcessingFileJson(Base):
    __tablename__ = "pre_processing_file_json"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(JSONB)
    preprocessing_file_id = Column(Integer, ForeignKey("pre_processing_files.id"))

    preprocessing_file = relationship("PreProcessingFile", back_populates="json_data", uselist=False)


class Batch(Base, TimeStampMixin):
    __tablename__ = "batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=True)
    user_name = Column(String)
    user_email = Column(String)
    status = Column(Enum(StatusEnum), default=StatusEnum.IN_PROGRESS)
    workstream = Column(Enum(WorkstreamEnum))
    is_uploaded = Column(Boolean, default=False)
    s3_path = Column(String, nullable=True)
    delivery_date = Column(Date(), nullable=True)
    has_validation_error = Column(Boolean, default=False)
    stats = Column(JSON, nullable=True)
    client = Column(String)

    preprocessing_files = relationship("PreProcessingFile", back_populates="batch")
    validation_errors = relationship("ValidationError", back_populates="batch")
    delivery_jsons = relationship("DeliveryJson", back_populates="batch")


class DeliveryJson(Base):
    __tablename__ = "delivery_files"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(JSONB)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)

    batch = relationship("Batch", back_populates="delivery_jsons")


class PreProcessingFile(Base, TimeStampMixin):
    __tablename__ = "pre_processing_files"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=True)

    json_data = relationship("PreProcessingFileJson", back_populates="preprocessing_file", uselist=False)
    batch = relationship("Batch", back_populates="preprocessing_files")


class ValidationError(Base, TimeStampMixin):
    __tablename__ = "validation_errors"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=True)
    type = Column(Enum(ValidationErrorTypeEnum), default=ValidationErrorTypeEnum.SCHEMA)
    delivery_id = Column(String, nullable=True)
    error_message = Column(String, nullable=False)
    link = Column(String, nullable=True)

    batch = relationship("Batch", back_populates="validation_errors")


class DeliveredId(Base, TimeStampMixin):
    __tablename__ = "delivered_ids"

    id = Column(Integer, primary_key=True, index=True)
    deliverable_id = Column(String(100), nullable=False, unique=True, index=True)
    project_name = Column(String(255), nullable=False)
    s3_path = Column(String(500), nullable=False)
    last_modified = Column(TIMESTAMP, nullable=False)


class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_level = Column(String, nullable=False)
    log_message = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

class ConfigOption(Base):
    __tablename__ = "config_option"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    value = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    details = Column(JSONB, nullable=True)  # Use JSONB as it is good
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User")

class Role(Base, TimeStampMixin):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(String, nullable=True)
    permissions = Column(JSONB, nullable=True, default={})
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    users = relationship("User", back_populates="role", lazy="dynamic")

    def soft_delete(self, session: Session):
        self.deleted_at = datetime.utcnow()
        session.add(self)
        session.commit()
