# global pydantic models


import datetime
from pydantic import BaseModel, SecretStr


class BasePydantic(BaseModel):
    class Config:
        # ORM - Object-Relational Mapping
        from_attributes = True
        # re-validate when update
        validate_assignment = True
        arbitrary_types_allowed = True
        str_strip_whitespace = True

        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%dT%H:%M:%S.%fZ") if v else None,
            SecretStr: lambda v: v.get_secret_value() if v else None,
        }
