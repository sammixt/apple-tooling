from fastapi import APIRouter, Header, HTTPException
from app.schemas.s3file import WebhookPayload
import json
from app.db.redis_client import redis_client
from app.jobs.celery_task import worker
import logging
from dotenv import load_dotenv
import os

router = APIRouter()
# Load environment variables from .env
load_dotenv()
logging.basicConfig(level=logging.DEBUG)  # You can set this to DEBUG for more detailed logs
logger = logging.getLogger(__name__)

# Get the token from .env
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")

if not WEBHOOK_SECRET_TOKEN:
    logger.error("WEBHOOK_SECRET_TOKEN not set in environment variables")
    raise RuntimeError("WEBHOOK_SECRET_TOKEN must be set in the .env file")

@router.post("/s3files/update-webhook", response_model=None)  # No response model needed
def update_s3file_webhook(s3files: WebhookPayload, x_webhook_token: str = Header(None)):
    # Check if the token matches
    if x_webhook_token != WEBHOOK_SECRET_TOKEN:
        logger.warning("Unauthorized access attempt with token: %s", x_webhook_token)
        raise HTTPException(status_code=403, detail="Forbidden: Invalid token")

    logger.info("Received webhook payload: %s", s3files)

    # Push each job to Redis
    for s3file in s3files.changes:
        job_data = s3file.dict()  # Serialize the necessary data
        # Convert the dictionary to a JSON string
        job_data_json = json.dumps(job_data)
        logger.debug("Pushing job data to Redis: %s", job_data_json)

        try:
            redis_client.lpush("update_s3file_webhooks", job_data_json)
            worker.delay()  # Assuming this is a Celery task
            logger.info("Job added to Redis for file: %s", s3file)
        except Exception as e:
            logger.error("Failed to push job data to Redis: %s", e)

    return {"message": "Jobs added successfully"}
