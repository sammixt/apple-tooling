import json
import logging
from fastapi import UploadFile, HTTPException
from typing import List, Dict, Any
from celery import Task, chain, group
from app.db.database import SessionLocal
from app.db.enums import StatusEnum, ValidationErrorTypeEnum
from app.db.models import Batch, ValidationError
from app.jobs.celery_task import process_images_task, convert_to_apple_format_rlhf_vision, validations_rlhf_vision
from .base import PreProcessingStrategy
from app.db.models import PreProcessingFile, PreProcessingFileJson
from sqlalchemy.orm import Session


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RLHFPreProcessingStrategy(PreProcessingStrategy):
    def validate_files(self, files: List[UploadFile], batch: Batch, db: Session) -> None:
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
        if "rlhf" not in json_data or "sft" not in json_data:
            raise HTTPException(
                status_code=400,
                detail="Both 'rlhf' and 'sft' keys are required in JSON data.",
            )

        return json_data

    def create_tasks(self, json_data: Dict[str, Any], batch: Batch) -> Task:
        try:
            db = SessionLocal()
            folder_date = batch.delivery_date.strftime("%Y%m%d")
            return process_images_task.s(json_data["rlhf"], f"2410-rlhf-vision/assets/{folder_date}/", batch.id)
        except Exception as e:
            batch.status = StatusEnum.FAILED
            batch.has_validation_error = True
            validation_error = ValidationError(
                batch_id=batch.id,
                type=ValidationErrorTypeEnum.TASK_CREATION,
                error_message=f"Error in task creation: {str(e)}",
            )
            db.add(validation_error)
            db.commit()
            logger.error(f"Error creating tasks: {e}")

    async def execute_tasks(self, batch: Batch, parallel_tasks: List[Task]) -> None:
        try:
            db = SessionLocal()
            parallel_group = group(parallel_tasks)
            sequential_tasks = chain(
                convert_to_apple_format_rlhf_vision.s(batch.id), validations_rlhf_vision.s(batch.id)
            )
            task_chain = chain(parallel_group, sequential_tasks)
            task_chain.apply_async()
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

    async def _process_file(self, file: UploadFile, batch: Batch, db: Session, file_record: PreProcessingFile) -> Task:
        if batch.status == StatusEnum.FAILED:
            return

        contents = await file.read()
        try:
            data = contents.decode("utf-8")
            json_data = json.loads(data)

            json_data = self.validate_json(json_data)

            json_data_record = PreProcessingFileJson(
                content=data,
                preprocessing_file_id=file_record.id,
            )
            db.add(json_data_record)
            db.commit()

            task = self.create_tasks(json_data, batch)
            return task

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
