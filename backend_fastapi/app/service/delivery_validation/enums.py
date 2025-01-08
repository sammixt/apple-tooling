from enum import Enum


class TaskType(Enum):
    RLHF_TEXT = "rlhfText"
    RLHF_IMAGE = "rlfhVision"
    RLHF_IMAGE_GEN_PROMPT = "rlfhImageGenPrompts"
    EVALS_IMAGE_GEN_PROMPT = "evalsResultImageGenPrompt"
    CODE_INT = 'code_int'
    SFT_APP_TOOL  = "sftAppTool"
    SFT_CODE_INT = 'sft_code_int'

class ValidationType(Enum):
    SCHEMA = "schema"
    S3_LINK = "s3_link"
    PENGUIN_FORMATTING = "Penguin formatting"
