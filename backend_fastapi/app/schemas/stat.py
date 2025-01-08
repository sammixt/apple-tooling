from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional

class StatBase(BaseModel):
    stats_data: Any

class StatCreate(StatBase):
    pass

class StatUpdate(StatBase):
    pass

class Stat(StatBase):
    id: int
    s3file_id: int
    created_at: datetime
    updated_at: Optional[datetime] = Field(None)

    class Config:
        from_attributes = True
