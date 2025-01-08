import logging
from fastapi import Depends, UploadFile, HTTPException
from typing import List, Dict, Any
import uuid
from celery import Task, chain, group
from app.db.database import SessionLocal
from app.db.enums import StatusEnum
from app.db.models import Batch, PreProcessingFile
from app.jobs.celery_task import process_images_task, convert_to_apple_format_rlhf_vision, validations_rlhf_vision
from .base import PreProcessingStrategy
from sqlalchemy.orm import Session


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SFTReasoningPreProcessingStrategy(PreProcessingStrategy):
    def validate_files(self, files: List[UploadFile]) -> None:
        logger.info("validate_files")
        return 

    def validate_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def process_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("process_json")
        return []

    def create_tasks(self, json_data: Dict[str, Any], batch_id: uuid.UUID) -> Task:
        logger.info("create_tasks")
        return

    async def execute_tasks(self, batch_id: uuid.UUID, parallel_tasks: List[Task]) -> None:
        logger.info("execute_tasks")
        return

    async def _process_file(self, file: UploadFile, batch: Batch, db: Session, json_record: PreProcessingFile) -> Task:
        pass
