from abc import ABC, abstractmethod
from fastapi import UploadFile
from typing import List, Dict, Any
import uuid
from celery import Task
from sqlalchemy.orm import Session
from app.db.models import Batch, PreProcessingFile


class PreProcessingStrategy(ABC):
    @abstractmethod
    def validate_files(self, files: List[UploadFile], batch: Batch) -> None:
        """Validate the uploaded files"""
        pass

    @abstractmethod
    def validate_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate the JSON data"""
        pass

    @abstractmethod
    def create_tasks(self, json_data: Dict[str, Any], batch: Batch) -> Task:
        """Create celery tasks for processing"""
        pass

    @abstractmethod
    async def execute_tasks(self, batch: Batch, parallel_tasks: List[Task]) -> None:
        """Execute the processing tasks"""
        pass

    async def _store_file(self, file: UploadFile, batch: Batch, db: Session) -> PreProcessingFile:
        """Store file metadata in the database"""
        files = PreProcessingFile(
            batch_id=batch.id,
            name=file.filename,
        )
        db.add(files)
        db.commit()
        return files

    async def process_file(self, file: UploadFile, batch: Batch, db: Session) -> Task:
        """Process the uploaded file and return a task"""
        json_record = await self._store_file(file, batch, db)

        self.validate_files([file], batch, db)

        return await self._process_file(file, batch, db, json_record)

    @abstractmethod
    async def _process_file(self, file: UploadFile, batch: Batch, db: Session, json_record: PreProcessingFile) -> Task:
        """Internal method to process the file after validation"""
        pass
