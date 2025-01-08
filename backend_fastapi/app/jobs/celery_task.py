from uuid import UUID
import hashlib
import boto3
from celery import Celery
from celery.schedules import crontab
import os
from app.core.s3_client import S3Client
from app.db.enums import StatusEnum, ValidationErrorTypeEnum
from app.db.redis_client import redis_client
from app.service.delivery_validation.parse_json_data import process_json_data
from app.service.json_conversion.image_processor_image_eval import ImageProcessorImageEval
from app.service.json_conversion.image_processor_rlhf_vison import ImageProcessor
from app.db.models import Batch, ConfigOption, DeliveryJson, PreProcessingFile, PreProcessingFileJson, ValidationError
from app.service.json_conversion import convert_rlhf_vision, convert_image_eval
from app.service.delivery_validation.validation import Validator
from app.service.delivery_validation.enums import TaskType, ValidationType
from app.service.json_conversion.rlhf_text import RLHFTextJSONProcessor
from app.service.json_conversion.sft_reasoning import (
    authenticate_drive,
    convert_ipynb_to_py,
    download_ipynb,
    extract_file_id,
    process_file_content,
)
from .handler import process_s3file_job
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, get_db
import json
from app.config import settings
import logging
from .log_cleanup import cleanup_old_logs
import re
import traceback
from app.db.enums import ClientEnum


s3 = S3Client()


redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", "6379")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configure Celery to use Redis as the broker and backend
celery_app = Celery(
    "worker",
    broker=f"redis://{redis_host}:{redis_port}/0",
    backend=f"redis://{redis_host}:{redis_port}/0",
)

# Enable retry on startup to retain the old behavior
celery_app.conf.update(broker_connection_retry_on_startup=True)

celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "cleanup-logs-daily": {
        "task": "app.cleanup_old_logs_task",
        "schedule": crontab(hour=0, minute=0),
    },
}


@celery_app.task()
def worker():
    logger.info("Worker started")
    data = redis_client.rpop("update_s3file_webhooks")

    if data:
        logger.info("Job data retrieved from Redis: %s", data)
        job = json.loads(data)

        # Use a session context manager to handle the DB session
        db: Session = next(get_db())  # Create a new database session
        try:
            logger.info("Processing job: %s", job)
            process_s3file_job(job, db)  # Implement this function based on your logic
            logger.info("Job processed successfully: %s", job)
        except Exception as e:
            logger.error("Error processing job: %s", e)
    else:
        logger.info("No job data found in Redis")

    logger.info("Worker finished processing")


@celery_app.task()
def process_images_task(json_data, s3_folder, batch_id):
    try:
        db = SessionLocal()
        batch = db.query(Batch).filter(Batch.id == batch_id).one()
        logger.info("Image Processing Started S3 folder: %s", s3_folder)
        processor = ImageProcessor(json_data, s3_folder)
        processor.process_all_items()
        return "Image Processing Completed"
    except Exception as e:
        batch.status = StatusEnum.FAILED
        batch.has_validation_error = True
        validation_error = ValidationError(
            batch_id=batch.id,
            type=ValidationErrorTypeEnum.TASK_PROCESSING,
            error_message=f"Error in task processing: {str(e)}",
        )
        db.add(validation_error)
        db.commit()
        logger.error(f"Error in process_images_task: {str(e)}")
        return
    finally:
        db.close()


@celery_app.task()
def process_images_task_image_eval(json_data, s3_folder, batch_id):
    try:
        db = SessionLocal()
        batch = db.query(Batch).filter(Batch.id == batch_id).one()
        logger.info("Image Processing Started S3 folder: %s", s3_folder)
        processor = ImageProcessorImageEval(json_data, s3_folder)
        processor.process_all_items()
        return "Image Processing Completed"
    except Exception as e:
        batch.status = StatusEnum.FAILED
        batch.has_validation_error = True
        validation_error = ValidationError(
            batch_id=batch.id,
            type=ValidationErrorTypeEnum.TASK_PROCESSING,
            error_message=f"Error in task processing: {str(e)}",
        )
        db.add(validation_error)
        db.commit()
        logger.error(f"Error in process_images_task: {str(e)}")
        return
    finally:
        db.close()


@celery_app.task()
def convert_to_apple_format_rlhf_vision(prev_result, batch_id):
    try:
        db = SessionLocal()
        batch = db.query(Batch).filter(Batch.id == batch_id).one()
        folder_date = batch.delivery_date.strftime("%Y%m%d")
        s3_prefix = f"s3://og82-drop-turing-deputy/2410-rlhf-vision/assets/{folder_date}"
        images_folder = f"2410-rlhf-vision/assets/{folder_date}/"

        processor = convert_rlhf_vision.JSONProcessor(s3_prefix, images_folder)
        results = (
            db.query(PreProcessingFileJson.content)
            .join(
                PreProcessingFile,
                PreProcessingFile.id == PreProcessingFileJson.preprocessing_file_id,
            )
            .filter(PreProcessingFile.batch_id == batch_id)
            .all()
        )
        input_array = [json.loads(result.content) for result in results]
        apple_json = processor.process_file(input_array)
        if not apple_json:
            batch.status = StatusEnum.FAILED
            batch.has_validation_error = True
            validation_error = ValidationError(
                batch_id=batch.id,
                type=ValidationErrorTypeEnum.JSON_FORMATTING,
                error_message="No data generated in Apple format conversion; check JSON and its formatting.",
            )
            db.add(validation_error)
            db.commit()
            return
        return apple_json
    except Exception as e:
        logger.error(f"Error in convert_to_apple_format: {str(e)}")
        batch.status = StatusEnum.FAILED
        batch.has_validation_error = True
        validation_error = ValidationError(
            batch_id=batch.id,
            type=ValidationErrorTypeEnum.JSON_FORMATTING,
            error_message=f"Error in JSON formatting: {str(e)}",
        )
        db.add(validation_error)
        db.commit()
        return
    finally:
        db.close()


@celery_app.task()
def validations_rlhf_vision(prev_result, batch_id):
    try:
        db = SessionLocal()
        if not prev_result:
            return f"No data for Validations for batch {batch_id}"
        batch = db.query(Batch).filter(Batch.id == batch_id).one()
        assets = []
        folder_date = batch.delivery_date.strftime("%Y%m%d")
        images_folder = f"2410-rlhf-vision/assets/{folder_date}/"
        apple_upload = db.query(ConfigOption).filter_by(name="enable_penguin_s3_upload").first()
        apple_upload_value = apple_upload.value if apple_upload else False

        if apple_upload_value:
            s3._refresh_if_credentials_expired()
            s3_client = s3.s3_client
            aws_bucket_name = settings.AWS_BUCKET_NAME
        else:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.DEV_AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.DEV_AWS_SECRET_ACCESS_KEY,
            )
            aws_bucket_name = settings.DEV_AWS_BUCKET_NAME

        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=aws_bucket_name, Prefix=images_folder)
        for page in pages:
            if "Contents" not in page:
                logger.error(f"No contents found in S3 folder: {images_folder}")
                continue
            for obj in page["Contents"]:
                image = obj["Key"].split("/")[-1]
                assets.append(image)

        assets_path = f"s3://og82-drop-turing-deputy/2410-rlhf-vision/assets/{folder_date}/"
        validator1 = Validator(prev_result, assets, assets_path)
        dedup_result = validator1.deduplicate()
        unique_data = dedup_result["data"]

        validation_error_records = []

        if dedup_result["errors"]:
            for error in dedup_result["errors"]:
                deliverable_id = UUID(error["deliverableId"])
                messages = error["message"]
                for message in messages:
                    validation_error = ValidationError(
                        batch_id=batch_id,
                        delivery_id=deliverable_id,
                        error_message=message,
                        type=ValidationErrorTypeEnum.DUPLICATION,
                    )
                    validation_error_records.append(validation_error)

        validator2 = Validator(unique_data, assets, assets_path)
        errors = validator2.validate(TaskType.RLHF_IMAGE, ValidationType.SCHEMA)

        error_delivery_ids = {error["deliverableId"] for error in errors}
        filtered_data = [entry for entry in unique_data if entry["deliverable_id"] not in error_delivery_ids]

        for error in errors:
            deliverable_id = UUID(error["deliverableId"])
            messages = error["message"]
            for message in messages:
                validation_error = ValidationError(
                    batch_id=batch_id,
                    delivery_id=deliverable_id,
                    error_message=message,
                    type=ValidationErrorTypeEnum.SCHEMA,
                )
                validation_error_records.append(validation_error)

        validator3 = Validator(filtered_data, assets, assets_path)
        s3_link_errors = validator3.validate(TaskType.RLHF_IMAGE, ValidationType.S3_LINK)

        for error in s3_link_errors:
            deliverable_id = UUID(error["deliverable_id"])
            message = error["message"]
            validation_error = ValidationError(
                batch_id=batch_id,
                delivery_id=deliverable_id,
                error_message=message,
                type=ValidationErrorTypeEnum.S3_LINK,
            )
            validation_error_records.append(validation_error)

        s3_link_error_delivery_ids = {error["deliverable_id"] for error in s3_link_errors}
        filtered_data2 = [
            entry for entry in filtered_data if entry["deliverable_id"] not in s3_link_error_delivery_ids
        ]

        validator = Validator(filtered_data2, assets, "assets_path")
        penguin_format_errors = validator.penguin_format_validate()
        for error in penguin_format_errors:
            deliverable_id = error["deliverableId"]
            messages = error["message"]
            for message in messages:
                validation_error = ValidationError(
                    batch_id=batch_id,
                    delivery_id=deliverable_id,
                    error_message=message,
                    type=ValidationErrorTypeEnum.PENGUIN_FORMATTING,
                )
                validation_error_records.append(validation_error)

        penguin_error_del_ids = {error["deliverableId"] for error in penguin_format_errors}
        filtered_data2 = [entry for entry in filtered_data2 if entry["deliverable_id"] not in penguin_error_del_ids]

        if validation_error_records:
            batch = db.query(Batch).filter(Batch.id == batch_id).one()
            batch.has_validation_error = True
            db.add_all(validation_error_records)
            db.commit()

        if filtered_data2:
            batch = db.query(Batch).filter(Batch.id == batch_id).one()
            batch.status = StatusEnum.COMPLETED
            delivery = DeliveryJson(content=filtered_data2, batch_id=batch_id)
            file_stats = process_json_data(filtered_data2, "rlhf-vision")
            batch.stats = file_stats
            db.add(delivery)
            db.commit()
        else:
            batch.status = StatusEnum.FAILED
            batch.has_validation_error = True
            validation_error = ValidationError(
                batch_id=batch.id,
                type=ValidationErrorTypeEnum.JSON_FORMATTING,
                error_message="No data after validation",
            )
            db.add(validation_error)
            db.commit()
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        batch.status = StatusEnum.FAILED
        batch.has_validation_error = True
        validation_error = ValidationError(
            batch_id=batch.id,
            type=ValidationErrorTypeEnum.TASK_PROCESSING,
            error_message=f"Error in task processing: {str(e)}",
        )
        db.add(validation_error)
        db.commit()
    finally:
        db.close()

    return f"Validations Completed for batch {batch_id}"


@celery_app.task()
def convert_to_apple_format_image_eval(prev_result, batch_id):
    try:
        db = SessionLocal()
        batch = db.query(Batch).filter(Batch.id == batch_id).one()
        folder_date = batch.delivery_date.strftime("%Y%m%d")
        s3_prefix = f"s3://og82-drop-turing-deputy/2410-eval-results/assets/{folder_date}"
        images_folder = f"2410-eval-results/assets/{folder_date}/"

        processor = convert_image_eval.JSONProcessor(s3_prefix, images_folder)
        results = (
            db.query(PreProcessingFileJson.content)
            .join(
                PreProcessingFile,
                PreProcessingFile.id == PreProcessingFileJson.preprocessing_file_id,
            )
            .filter(PreProcessingFile.batch_id == batch_id)
            .all()
        )
        input_array = [json.loads(result.content) for result in results]
        apple_json = processor.process_file(input_array)
        if not apple_json:
            batch.status = StatusEnum.FAILED
            batch.has_validation_error = True
            validation_error = ValidationError(
                batch_id=batch.id,
                type=ValidationErrorTypeEnum.JSON_FORMATTING,
                error_message="No data generated in Apple format conversion; check JSON and its formatting.",
            )
            db.add(validation_error)
            db.commit()
            return
        return apple_json
    except Exception as e:
        logger.error(f"Error in convert_to_apple_format: {str(e)}")
        batch.status = StatusEnum.FAILED
        batch.has_validation_error = True
        validation_error = ValidationError(
            batch_id=batch.id,
            type=ValidationErrorTypeEnum.JSON_FORMATTING,
            error_message=f"Error in JSON formatting: {str(e)}",
        )
        db.add(validation_error)
        db.commit()
        return
    finally:
        db.close()


@celery_app.task()
def validations_image_eval(prev_result, batch_id):
    try:
        db = SessionLocal()
        if not prev_result:
            return f"No data for Validations for batch {batch_id}"
        batch = db.query(Batch).filter(Batch.id == batch_id).one()
        assets = []
        images_folder = "2410-eval-results/assets/20241112/"
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.DEV_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.DEV_AWS_SECRET_ACCESS_KEY,
        )
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=settings.DEV_AWS_BUCKET_NAME, Prefix=images_folder)
        for page in pages:
            if "Contents" not in page:
                print("content is not there")
                continue
            for obj in page["Contents"]:
                image = obj["Key"].split("/")[-1]
                assets.append(image)

        validator1 = Validator(prev_result, assets, images_folder)
        dedup_result = validator1.deduplicate()
        unique_data = dedup_result["data"]

        validation_error_records = []

        if dedup_result["errors"]:
            for error in dedup_result["errors"]:
                deliverable_id = UUID(error["deliverableId"])
                messages = error["message"]
                for message in messages:
                    validation_error = ValidationError(
                        batch_id=batch_id,
                        delivery_id=deliverable_id,
                        error_message=message,
                        type=ValidationErrorTypeEnum.DUPLICATION,
                    )
                    validation_error_records.append(validation_error)

        if validation_error_records:
            batch = db.query(Batch).filter(Batch.id == batch_id).one()
            batch.has_validation_error = True
            db.add_all(validation_error_records)
            db.commit()

        # error_delivery_ids = {error["deliverableId"] for error in errors}
        # filtered_data = [entry for entry in unique_data if entry["deliverable_id"] not in error_delivery_ids]
        if unique_data:
            batch = db.query(Batch).filter(Batch.id == batch_id).one()
            batch.status = StatusEnum.COMPLETED
            delivery = DeliveryJson(content=unique_data, batch_id=batch_id)
            db.add(delivery)
            db.commit()
        else:
            batch.status = StatusEnum.FAILED
            batch.has_validation_error = True
            validation_error = ValidationError(
                batch_id=batch.id,
                type=ValidationErrorTypeEnum.JSON_FORMATTING,
                error_message="No data after validation",
            )
            db.add(validation_error)
            db.commit()
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        batch.status = StatusEnum.FAILED
        batch.has_validation_error = True
        validation_error = ValidationError(
            batch_id=batch.id,
            type=ValidationErrorTypeEnum.TASK_PROCESSING,
            error_message=f"Error in task processing: {str(e)}",
        )
        db.add(validation_error)
        db.commit()
    finally:
        db.close()

    return f"Validations Completed for batch {batch_id}"


@celery_app.task(name="app.cleanup_old_logs_task")
def cleanup_old_logs_task():
    cleanup_old_logs()


@celery_app.task()
def process_colab_link(links, ids, batch_id, client):
    try:
        db = SessionLocal()
        batch = db.query(Batch).filter(Batch.id == batch_id).one()
        drive_service = authenticate_drive()

        output_array = []
        error_array = []

        for idx, link in enumerate(links):
            try:
                print("idx", idx)
                file_id = extract_file_id(link)
                ipynb_content = download_ipynb(drive_service, file_id)
                py_content = convert_ipynb_to_py(ipynb_content)

                # Determine category and patterns
                category_match = re.search(r"(?i)\*\*Category\:\*\*\s*-\s*([^\n]*)", py_content)
                category = category_match.group(1).strip() if category_match else "General"

                type = "General"
                if category.lower() == "agent":
                    type = "Agent"
                elif category.lower() == "coding":
                    if re.search(r"(?i)\*\*\[CHAIN", py_content) and re.search(r"(?i)\*\*\[THOUGHT", py_content):
                        type = "Coding"

                json_data = process_file_content(type, py_content, ids[idx], client, file_id)
                output_array.append(json_data)
            except Exception as e:
                logger.error("colab file: " + link + " error trace: " + traceback.format_exc())
                error_array.append({"link": link, "message": str(e)})

        validation_error_records = []

        for error in error_array:
            link = error["link"]
            message = error["message"]
            validation_error = ValidationError(
                batch_id=batch_id,
                link=link,
                error_message=message,
                type=ValidationErrorTypeEnum.SCHEMA,
            )
            validation_error_records.append(validation_error)

        # if duplicate_links:
        #     validation_error = ValidationError(
        #         batch_id=batch_id,
        #         link=', '.join(duplicate_links),
        #         error_message=f"The following links are duplicated in the CSV: {', '.join(duplicate_links)}",
        #         type=ValidationErrorTypeEnum.DUPLICATION,
        #     )
        #     validation_error_records.append(validation_error)
        # with open("output_array.json", "w") as file:
        #     json.dump(output_array, file, indent=4)
        assets = []
        validator = Validator(output_array, assets, "assets_path")
        dedup_result = validator.deduplicate()
        unique_data = dedup_result["data"]
        with open("output1.json", "w") as file:
            json.dump(unique_data, file, indent=4)

        if dedup_result["errors"]:
            for error in dedup_result["errors"]:
                deliverable_id = error["deliverableId"]
                messages = error["message"]
                for message in messages:
                    validation_error = ValidationError(
                        batch_id=batch_id,
                        delivery_id=deliverable_id,
                        error_message=message,
                        type=ValidationErrorTypeEnum.DUPLICATION,
                    )
                    validation_error_records.append(validation_error)

        if client == ClientEnum.PENGUIN.value:
            validator = Validator(unique_data, assets, "assets_path")
            schema_errors = validator.penguin_format_validate()
            if len(schema_errors) > 0:
                for error in schema_errors:
                    deliverable_id = error["deliverableId"]
                    messages = error["message"]
                    for message in messages:
                        validation_error = ValidationError(
                            batch_id=batch_id,
                            delivery_id=deliverable_id,
                            error_message=message,
                            type=ValidationErrorTypeEnum.PENGUIN_FORMATTING,
                            link=f"https://colab.research.google.com/drive/{deliverable_id}",
                        )
                        validation_error_records.append(validation_error)

                error_delivery_ids = {error["deliverableId"] for error in schema_errors}
                unique_data = [entry for entry in unique_data if entry["deliverable_id"] not in error_delivery_ids]

        if validation_error_records:
            batch = db.query(Batch).filter(Batch.id == batch_id).one()
            batch.has_validation_error = True
            db.add_all(validation_error_records)
            db.commit()

        if unique_data:
            with open("output.json", "w") as file:
                json.dump(unique_data,file, indent=4)
            batch = db.query(Batch).filter(Batch.id == batch_id).one()
            batch.status = StatusEnum.COMPLETED
            delivery = DeliveryJson(content=unique_data, batch_id=batch_id)
            db.add(delivery)
            db.commit()
            return f"process_colab_link Completed for batch {batch_id}"
        else:
            batch.status = StatusEnum.FAILED
            batch.has_validation_error = True
            validation_error = ValidationError(
                batch_id=batch.id,
                type=ValidationErrorTypeEnum.JSON_FORMATTING,
                error_message="No data generated in Apple format conversion; check Colab and its formatting.",
            )
            db.add(validation_error)
            db.commit()
            return
    except Exception as e:
        logger.error(f"Error in process_colab_link: {str(e)}")
        batch.status = StatusEnum.FAILED
        batch.has_validation_error = True
        validation_error = ValidationError(
            batch_id=batch.id,
            type=ValidationErrorTypeEnum.JSON_FORMATTING,
            error_message=f"Error in JSON formatting: {str(e)}",
        )
        db.add(validation_error)
        db.commit()
        return
    finally:
        db.close()


@celery_app.task()
def validations_rlhf_text(prev_result, batch_id):
    try:
        db = SessionLocal()
        if not prev_result:
            return f"No data for Validations for batch {batch_id}"
        batch = db.query(Batch).filter(Batch.id == batch_id).one()
        assets = []

        validator1 = Validator(prev_result, assets, "assets_path")
        dedup_result = validator1.deduplicate()
        unique_data = dedup_result["data"]

        validation_error_records = []

        if dedup_result["errors"]:
            for error in dedup_result["errors"]:
                deliverable_id = UUID(error["deliverableId"])
                messages = error["message"]
                for message in messages:
                    validation_error = ValidationError(
                        batch_id=batch_id,
                        delivery_id=deliverable_id,
                        error_message=message,
                        type=ValidationErrorTypeEnum.DUPLICATION,
                    )
                    validation_error_records.append(validation_error)

        validator2 = Validator(unique_data, assets, "assets_path")
        errors = validator2.validate(TaskType.RLHF_IMAGE, ValidationType.SCHEMA)

        error_delivery_ids = {error["deliverableId"] for error in errors}
        filtered_data = [entry for entry in unique_data if entry["deliverable_id"] not in error_delivery_ids]

        for error in errors:
            deliverable_id = UUID(error["deliverableId"])
            messages = error["message"]
            for message in messages:
                validation_error = ValidationError(
                    batch_id=batch_id,
                    delivery_id=deliverable_id,
                    error_message=message,
                    type=ValidationErrorTypeEnum.SCHEMA,
                )
                validation_error_records.append(validation_error)

        if validation_error_records:
            batch = db.query(Batch).filter(Batch.id == batch_id).one()
            batch.has_validation_error = True
            db.add_all(validation_error_records)
            db.commit()

        if filtered_data:
            batch = db.query(Batch).filter(Batch.id == batch_id).one()
            batch.status = StatusEnum.COMPLETED
            delivery = DeliveryJson(content=filtered_data, batch_id=batch_id)
            file_stats = process_json_data(filtered_data, "rlhf-vision")
            batch.stats = file_stats
            db.add(delivery)
            db.commit()
        else:
            batch.status = StatusEnum.FAILED
            batch.has_validation_error = True
            validation_error = ValidationError(
                batch_id=batch.id,
                type=ValidationErrorTypeEnum.JSON_FORMATTING,
                error_message="No data after validation",
            )
            db.add(validation_error)
            db.commit()
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        batch.status = StatusEnum.FAILED
        batch.has_validation_error = True
        validation_error = ValidationError(
            batch_id=batch.id,
            type=ValidationErrorTypeEnum.TASK_PROCESSING,
            error_message=f"Error in task processing: {str(e)}",
        )
        db.add(validation_error)
        db.commit()
    finally:
        db.close()

    return f"Validations Completed for batch {batch_id}"


@celery_app.task()
def convert_to_apple_format_rlhf_text(batch_id):
    try:
        db = SessionLocal()
        batch = db.query(Batch).filter(Batch.id == batch_id).one()
        processor = RLHFTextJSONProcessor()
        results = (
            db.query(PreProcessingFileJson.content)
            .join(
                PreProcessingFile,
                PreProcessingFile.id == PreProcessingFileJson.preprocessing_file_id,
            )
            .filter(PreProcessingFile.batch_id == batch_id)
            .all()
        )
        input_array = [json.loads(result.content) for result in results]
        apple_json = processor.process_file(input_array)
        if not apple_json:
            batch.status = StatusEnum.FAILED
            batch.has_validation_error = True
            validation_error = ValidationError(
                batch_id=batch.id,
                type=ValidationErrorTypeEnum.JSON_FORMATTING,
                error_message="No data generated in Apple format conversion; check JSON and its formatting.",
            )
            db.add(validation_error)
            db.commit()
            return
        return apple_json
    except Exception as e:
        logger.error(f"Error in convert_to_apple_format_rlhf_text: {str(e)}")
        batch.status = StatusEnum.FAILED
        batch.has_validation_error = True
        validation_error = ValidationError(
            batch_id=batch.id,
            type=ValidationErrorTypeEnum.JSON_FORMATTING,
            error_message=f"Error in JSON formatting: {str(e)}",
        )
        db.add(validation_error)
        db.commit()
        return
    finally:
        db.close()


@celery_app.task()
def validations_sft_code_int(batch_id):
    try:
        db = SessionLocal()
        batch = db.query(Batch).filter(Batch.id == batch_id).one()
        result = (
            db.query(PreProcessingFileJson.content)
            .join(PreProcessingFile, PreProcessingFile.id == PreProcessingFileJson.preprocessing_file_id)
            .filter(PreProcessingFile.batch_id == batch_id)
            .one()
        )

        if not result:
            return f"No data for Validations for batch {batch_id}"

        apple_json = json.loads(result.content)

        assets = []

        validator1 = Validator(apple_json, assets, "assets_path")
        dedup_result = validator1.deduplicate()
        unique_data = dedup_result["data"]

        validation_error_records = []

        if dedup_result["errors"]:
            for error in dedup_result["errors"]:
                deliverable_id = error["deliverableId"]
                messages = error["message"]
                for message in messages:
                    validation_error = ValidationError(
                        batch_id=batch_id,
                        delivery_id=deliverable_id,
                        error_message=message,
                        type=ValidationErrorTypeEnum.DUPLICATION,
                    )
                    validation_error_records.append(validation_error)

        validator2 = Validator(unique_data, assets, "assets_path")
        errors = validator2.validate(TaskType.SFT_CODE_INT, ValidationType.SCHEMA)
        error_delivery_ids = {error["deliverableId"] for error in errors}
        filtered_data = [entry for entry in unique_data if entry["deliverable_id"] not in error_delivery_ids]
        for error in errors:
            deliverable_id = error["deliverableId"]
            messages = error["message"]
            validation_error = ValidationError(
                batch_id=batch_id,
                delivery_id=deliverable_id,
                error_message=messages,
                type=ValidationErrorTypeEnum.SCHEMA,
            )
            validation_error_records.append(validation_error)

        if validation_error_records:
            batch = db.query(Batch).filter(Batch.id == batch_id).one()
            batch.has_validation_error = True
            db.add_all(validation_error_records)
            db.commit()

        if filtered_data:
            batch = db.query(Batch).filter(Batch.id == batch_id).one()
            batch.status = StatusEnum.COMPLETED
            delivery = DeliveryJson(content=filtered_data, batch_id=batch_id)
            file_stats = process_json_data(filtered_data, "2410-sft-code-int")
            batch.stats = file_stats
            db.add(delivery)
            db.commit()
        else:
            batch.status = StatusEnum.FAILED
            batch.has_validation_error = True
            validation_error = ValidationError(
                batch_id=batch.id,
                type=ValidationErrorTypeEnum.JSON_FORMATTING,
                error_message="No data after validation",
            )
            db.add(validation_error)
            db.commit()
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        batch.status = StatusEnum.FAILED
        batch.has_validation_error = True
        validation_error = ValidationError(
            batch_id=batch.id,
            type=ValidationErrorTypeEnum.TASK_PROCESSING,
            error_message=f"Error in task processing: {str(e)}",
        )
        db.add(validation_error)
        db.commit()
    finally:
        db.close()

    return f"Validations Completed for batch {batch_id}"
