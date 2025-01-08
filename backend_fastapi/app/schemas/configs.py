from pydantic import BaseModel
from typing import Dict

class ConfigurationModel(BaseModel):
    configuration: Dict[str, bool]
