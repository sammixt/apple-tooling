from app.schema import BasePydantic
from datetime import datetime
from typing import Optional

class LoggerResponse(BasePydantic):
    id: int
    log_level: str
    log_message: str
    created_at: datetime