import logging
import json
from fastapi import UploadFile
from typing import List, Dict, Any
import uuid
from celery import Task
from app.db.database import SessionLocal
from app.db.enums import StatusEnum, ValidationErrorTypeEnum
from app.db.models import Batch, PreProcessingFile, PreProcessingFileJson
from app.db.models import Batch, ValidationError
from app.jobs.celery_task import validations_sft_code_int
from .base import PreProcessingStrategy
from sqlalchemy.orm import Session


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SFTCodeIntPreProcessingStrategy(PreProcessingStrategy):
    def validate_files(self, files: List[UploadFile],  batch: Batch, db: Session) -> None:
        for file in files:
            if file.content_type != "application/json":
                batch.status = StatusEnum.FAILED
                batch.has_validation_error = True
                validation_error = ValidationError(
                    batch_id=batch.id,
                    type=ValidationErrorTypeEnum.JSON_FORMATTING,
                    error_message="Invalid file type.",
                )
                db.add(validation_error)
                db.commit()

    def validate_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        pass


    def create_tasks(self, json_data: Dict[str, Any], batch_id: uuid.UUID) -> Task:
        pass

    async def execute_tasks(self, batch: Batch, parallel_tasks: List[Task]) -> None:
        try:
            db = SessionLocal()
            validations_sft_code_int.apply_async(args=[batch.id])
        except Exception as e:
            batch.status = StatusEnum.FAILED
            batch.has_validation_error = True
            validation_error = ValidationError(
                batch_id=batch.id,
                type=ValidationErrorTypeEnum.TASK_PROCESSING,
                error_message=f"Error in task processing: {str(e)}",
            )
            db.add(validation_error)
            db.commit()
            logger.error(f"Error in executing tasks: {e}")

    async def _process_file(self, file: UploadFile, batch: Batch, db: Session, json_record: PreProcessingFile) -> Task:
        if batch.status == StatusEnum.FAILED:
            return

        contents = await file.read()
        try:
            data = contents.decode("utf-8")
            json_data = json.loads(data)

            json_data = self.validate_json(json_data)

            json_data_record = PreProcessingFileJson(
                content=data,
                preprocessing_file_id=json_record.id,
            )
            db.add(json_data_record)
            db.commit()
            return

        except Exception as e:
            logger.error(f"Error in _process_file: {e}")
            batch.status = StatusEnum.FAILED
            batch.has_validation_error = True
            print(batch.id)
            validation_error = ValidationError(
                batch_id=batch.id,
                type=ValidationErrorTypeEnum.JSON_FORMATTING,
                error_message=f"Error in JSON decoding: {str(e)}",
            )
            print(validation_error)
            db.add(validation_error)
            db.commit()
