from app.service.delivery_validation.penguin_json_validator import PenguinFormattingValidator
from app.service.delivery_validation.rlhf_validator import RlhfValidator
from app.service.delivery_validation.rlhf_imagegen import RlhfImageGenValidator
from app.service.delivery_validation.deduplicate import DeDuplication
from app.service.delivery_validation.eval_result_imagegen import EvalImageGenValidator
from app.service.delivery_validation.sft_app_tool import SftSchemaValidator
from app.service.delivery_validation.s3_link_validator import S3LinkValidator
from app.service.delivery_validation.sft_code_int_validator import SftCodeIntValidation
from app.service.delivery_validation.enums import TaskType, ValidationType


class Validator:
    def __init__(self, data, assets, assets_path):
        self.data = data
        self.assets = assets  # array of image names
        self.assets_path = assets_path
        # self.rlhf_image_gen_validator = RlhfImageGenValidator(self.data)
        self.rlhf_text_vision = RlhfValidator(self.data)
        self.eval_image_gen_validatior = EvalImageGenValidator(self.data)
        self.de_duplication = DeDuplication()
        self.sft_app_tool_validator = SftSchemaValidator()
        self.s3_link_validator = S3LinkValidator(data, assets, assets_path)
        self.sft_code_int_validator = SftCodeIntValidation(data)
        self.penguin_format_validator = PenguinFormattingValidator(data)

    # validate at a time for 1 JSON
    def validate(self, task_type, validation_type):
        match task_type:
            case TaskType.RLHF_TEXT:
                match validation_type:
                    case ValidationType.SCHEMA:
                        return self.rlhf_text_vision.validate()
                    case _:
                        return ["Invalid validation type for the task type."]
            case TaskType.RLHF_IMAGE:
                match validation_type:
                    case ValidationType.SCHEMA:
                        return self.rlhf_text_vision.validate()
                    case ValidationType.S3_LINK:
                        return self.s3_link_validator.validate(task_type)
                    case _:
                        return ["Invalid validation type for the task type."]
            case TaskType.RLHF_IMAGE_GEN_PROMPT:
                match validation_type:
                    case ValidationType.SCHEMA:
                        return self.rlhf_text_vision.validate()
                    case ValidationType.S3_LINK:
                        return self.s3_link_validator.validate(task_type)
                    case _:
                        return ["Invalid validation type for the task type."]
            case TaskType.EVALS_IMAGE_GEN_PROMPT:
                match validation_type:
                    case ValidationType.SCHEMA:
                        return self.rlhf_text_vision.validate()
                    case ValidationType.S3_LINK:
                        return self.s3_link_validator.validate(task_type)
                    case _:
                        return ["Invalid validation type for the task type."]
            case TaskType.CODE_INT:
                match validation_type:
                    case ValidationType.S3_LINK:
                        return self.s3_link_validator.validate(task_type)
                    case _:
                        return ["Invalid validation type for the task type."]
            case TaskType.SFT_APP_TOOL:
                match validation_type:
                    case ValidationType.SCHEMA:
                        return self.sft_app_tool_validator.process_schema_validation(self.data)
                    case _:
                        return ["Invalid validation type for the task type."]
            case TaskType.SFT_CODE_INT:
                match validation_type:
                    case ValidationType.SCHEMA:
                        return self.sft_code_int_validator.validate()
            case _:
                return ["Invalid task type."]

    def deduplicate(self):
        return self.de_duplication.validate(self.data)

    def penguin_format_validate(self):
        return self.penguin_format_validator.validate()
