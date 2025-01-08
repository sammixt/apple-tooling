import enum


class WorkstreamEnum(enum.Enum):
    RLHF_VISION = "rlhf_vision"
    IMAGE_EVAL = "image_eval"
    SFT_REASONING = "sft_reasoning"
    RLHF_TEXT = "rlhf_text"
    SFT_CODE_INT = "sft_code_int"


class ValidationErrorTypeEnum(enum.Enum):
    SCHEMA = "Schema validation error"
    S3_LINK = "Image not found"
    DUPLICATION = "Duplicate task"
    JSON_FORMATTING = "JSON formatting error"
    TASK_CREATION = "Task creation error"
    TASK_PROCESSING = "Task processing error"
    PENGUIN_FORMATTING = "Penguin formatting error"


class StatusEnum(enum.Enum):
    IN_PROGRESS = "In progress"
    COMPLETED = "Completed"
    FAILED = "Failed"


class ClientEnum(enum.Enum):
    PENGUIN = "penguin"
    BYTEDANCE = "bytedance"
