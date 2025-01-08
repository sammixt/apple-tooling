from fastapi import UploadFile
from sqlalchemy.orm import Session
from typing import List
from app.db.enums import WorkstreamEnum, ClientEnum
from app.db.models import Batch
from app.strategies.preprocessing.base import PreProcessingStrategy
from app.strategies.preprocessing.rlhf_text_strategy import RLHFTextPreProcessingStrategy
from app.strategies.preprocessing.rlhf_vision_strategy import RLHFPreProcessingStrategy
from app.strategies.preprocessing.image_eval_strategy import ImageEvalPreProcessingStrategy
from app.strategies.preprocessing.sft_code_int_strategy import SFTCodeIntPreProcessingStrategy
from datetime import datetime
from app.strategies.preprocessing.sft_reasoning_strategy import SFTReasoningPreProcessingStrategy


class PreProcessingContext:
    def __init__(self, strategy: PreProcessingStrategy, db: Session):
        self.strategy = strategy
        self.db = db
        self.batch = None
        self.parallel_tasks = []

    def set_batch(self, batch: Batch):
        self.batch = batch

    async def process_file(self, file: UploadFile):
        task = await self.strategy.process_file(file, self.batch, self.db)
        if task:
            self.parallel_tasks.append(task)

    async def execute_tasks(self):
        await self.strategy.execute_tasks(self.batch, self.parallel_tasks)


class PreProcessingContextFactory:
    # Dictionary of supported workstreams and their descriptions
    SUPPORTED_WORKSTREAMS = {
        WorkstreamEnum.RLHF_VISION: "RLHF Vision",
        WorkstreamEnum.IMAGE_EVAL: "Image Evaluation",
        WorkstreamEnum.SFT_REASONING: "SFT Reasoning",
        WorkstreamEnum.RLHF_TEXT: "RLHF Text",
        WorkstreamEnum.SFT_CODE_INT: "SFT Code Interpreter"
    }
    
    STRATEGY_MAPPING = {
        WorkstreamEnum.RLHF_VISION: RLHFPreProcessingStrategy,
        WorkstreamEnum.IMAGE_EVAL: ImageEvalPreProcessingStrategy,
        WorkstreamEnum.SFT_REASONING: SFTReasoningPreProcessingStrategy,
        WorkstreamEnum.RLHF_TEXT: RLHFTextPreProcessingStrategy,
        WorkstreamEnum.SFT_CODE_INT: SFTCodeIntPreProcessingStrategy,
    }
    
    BATCH_NAME_MAPPING = {
        WorkstreamEnum.RLHF_VISION: "[{date_str}] RLHF Vision en_US.json",
        WorkstreamEnum.IMAGE_EVAL: "[{date_str}] Image Evaluation en_US.json",
        WorkstreamEnum.SFT_REASONING: "[{date_str}] sft-reasoning en_US.json",
        WorkstreamEnum.RLHF_TEXT: "[{date_str}] rlhf-code-python-swift-go-cpp-java-js en_US.json",
        WorkstreamEnum.SFT_CODE_INT: "[{date_str}] SFT Swift Code Interpreter en_US.json",
    }
    

    @staticmethod
    def create_context(workstream: WorkstreamEnum, db: Session) -> PreProcessingContext:
        strategy_class = PreProcessingContextFactory.STRATEGY_MAPPING.get(workstream)
        if strategy_class:
            strategy = strategy_class()
            return PreProcessingContext(strategy, db)
        else:
            raise ValueError(f"Unsupported workstream: {workstream}")

    @staticmethod
    def get_available_workstreams() -> List[dict]:
        """Returns a list of available workstreams"""

        return [{"id": key, "name": value} for key, value in PreProcessingContextFactory.SUPPORTED_WORKSTREAMS.items()]
    
    @staticmethod
    def get_clients() -> List[dict]:
        """Returns a list of available workstreams"""

        return [{"id": client.name, "name": client.value} for client in ClientEnum]

    @staticmethod
    def get_batch_name(workstream: WorkstreamEnum, delivery_date: datetime) -> str:
        """Returns the appropriate batch name based on workstream"""

        date_str = delivery_date.strftime("%Y-%m-%d")
        batch_name_format = PreProcessingContextFactory.BATCH_NAME_MAPPING.get(workstream)
        if batch_name_format:
            return batch_name_format.format(date_str=date_str)
        else:
            raise ValueError(f"Unsupported workstream: {workstream}")
