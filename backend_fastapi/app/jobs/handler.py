from app.core.s3_client import S3Client
from app.db.models import S3File, FileContent, Stat, DeliveredId
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.service.delivery_validation.validation import Validator
from app.service.delivery_validation.enums import TaskType
from app.service.delivery_validation.parse_json_data import process_json_data
import os
import requests
from datetime import datetime
from app.service.delivery_validation.add_deliverable_ids import add_deliverable_ids

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/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");
s3_client = S3Client()

# Helper Methods
def prepare_slack_message(file_stats, file_path):
    total_conversations = file_stats.get("totalConversations", 0)
    total_user_turns = file_stats.get("totalUserTurns", 0)
    ideal_sft = file_stats.get("ideal_sft", 0)
    rlhf = file_stats.get("rlhf", 0)
    category_groups = file_stats.get("categoryGroups", {})

    message_data = {
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*File Stats Notification*"}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"Details of the `{file_path}` file:\n"
                        f"- Total Conversations: {total_conversations}\n"
                        f"- Total User Turns: {total_user_turns}\n"
                        f"- Ideal SFT: {ideal_sft}\n"
                        f"- RLHF: {rlhf}\n"
                        f"- Categories: {category_groups}"
                    )
                }
            }
        ]
    }
    return message_data


def send_slack_notification(file_stats, file_path):
    if not SLACK_WEBHOOK_URL:
        raise ValueError("Slack webhook URL not found. Please check .env file.")

    slack_message = prepare_slack_message(file_stats, file_path)

    response = requests.post(
        SLACK_WEBHOOK_URL,
        json=slack_message,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code != 200:
        raise ValueError(
            f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}")
    else:
        print("Slack notification sent successfully.")

# Main handler methods
def process_s3file_job(job, db: Session):
    # Check if the file key points to a JSON file
    if not job["s3key"].endswith(".json"):
        raise HTTPException(
            status_code=400, detail="File key must point to a JSON file."
        )

    if job["action"] == "created":
        create_s3file(job, db)

    elif job["action"] == "updated":
        # Update the existing S3 file
        existing_s3_file = db.query(S3File).filter(S3File.s3key == job["s3key"]).first()
        if existing_s3_file:
            update_s3file(job, db, existing_s3_file)
        else:
            file_key = job['s3key']
            print(f"File with key '{file_key}' does not exist in the database. Creating a new entry...")
            create_s3file(job, db)

    elif job["action"] == "deleted":
        # Delete the S3 file entry and its associated content
        existing_s3_file = db.query(S3File).filter(S3File.s3key == job["s3key"]).first()

        if existing_s3_file:
            delete_s3file(job, db, existing_s3_file)

    else:
        raise HTTPException(status_code=400, detail="Invalid action specified.")

def create_s3file(job, db: Session):
    # Step 1: Download file content from S3
    file_content = s3_client.download_file(job["s3key"])
    if not file_content:
        raise HTTPException(status_code=404, detail="File not found in S3.")

    # Step 2: Process JSON data and collect stats
    file_stats = process_json_data(file_content, job["workstream"])

    # Step 3: Create new S3 file entry in the database
    new_s3_file = create_s3_file_entry(job, db)

    # Step 4: Save file content to the database
    save_file_content(new_s3_file.id, file_content, db)

    # Step 5: Save file stats to the database
    save_file_stats(new_s3_file.id, file_stats, db)

    # Step 6: Process deliverable IDs if applicable
    if is_valid_deliverable_content(file_content):
        process_deliverable_ids(file_content, job, db)

    # Step 7: Send Slack notification
    send_slack_notification(file_stats, job["s3key"])

def create_s3_file_entry(job, db: Session) -> S3File:
    """Helper function to create and commit a new S3File entry."""
    new_s3_file = S3File(
        s3key=job["s3key"],
        file_url=job["file_url"],
        workstream=job["workstream"],
    )
    db.add(new_s3_file)
    db.commit()
    db.refresh(new_s3_file)
    return new_s3_file

def save_file_content(s3file_id: int, file_content: str, db: Session):
    """Helper function to save file content to the database."""
    new_content = FileContent(
        s3file_id=s3file_id,
        content=file_content,
        file_type="json",  # Assuming content is JSON
    )
    db.add(new_content)
    db.commit()

def save_file_stats(s3file_id: int, file_stats: dict, db: Session):
    """Helper function to save stats to the database."""
    new_stat = Stat(s3file_id=s3file_id, stats_data=file_stats)
    db.add(new_stat)
    db.commit()

def is_valid_deliverable_content(file_content) -> bool:
    """Check if the file content contains valid deliverables."""
    return isinstance(file_content, list) and all('deliverable_id' in item for item in file_content)

def process_deliverable_ids(file_content, job, db: Session):
    """Process deliverable IDs and insert them into the DeliveredId table."""
    deliverable_ids = add_deliverable_ids(file_content, job["file_url"], job["workstream"])

    # Step 1: Fetch existing deliverable_ids as a set to avoid duplicates
    existing_ids = {item[0] for item in db.query(DeliveredId.deliverable_id).all()}

    # Step 2: Prepare new deliverable entries, filtering out existing ones
    new_deliverable_objects = [
        DeliveredId(
            project_name=item['project_name'],
            deliverable_id=item['deliverable_id'],
            s3_path=item['s3_path'],
            last_modified=item['last_modified']
        )
        for item in deliverable_ids if item['deliverable_id'] not in existing_ids
    ]

    # Step 3: Bulk insert new deliverables
    if new_deliverable_objects:
        db.bulk_save_objects(new_deliverable_objects)
        db.commit()

        print("Records inserted successfully")
    else:
        print("No new deliverables to insert.")

def update_s3file(job, db: Session, existing_s3_file):
    # Download the updated JSON file content from S3
    file_content = s3_client.download_file(job["s3key"])
    if not file_content:
        raise HTTPException(status_code=404, detail="File not found in S3.")

    # Step 1: Update S3 file record
    """Helper function to update the S3 file record."""
    existing_s3_file.file_url = job["file_url"]
    existing_s3_file.workstream = job["workstream"]

    # Step 2: Update or insert file content
    update_or_insert_content(existing_s3_file.id, file_content, db)

    # Step 3: Update or insert file stats
    update_or_insert_stats(existing_s3_file.id, file_content, job["workstream"], db)

    # Step 4: Process deliverable IDs if applicable
    if is_valid_deliverable_content(file_content):
        process_deliverable_ids(file_content, job, db)

    # Step 5: Send Slack notification
    send_slack_notification(process_json_data(file_content, job["workstream"]), job["s3key"])



def update_or_insert_content(s3file_id: int, file_content: str, db: Session):
    """Helper function to update or insert file content."""
    content_record = (
        db.query(FileContent)
        .filter(FileContent.s3file_id == s3file_id)
        .first()
    )
    if content_record:
        content_record.content = file_content
        content_record.file_type = "json"
    else:
        new_content = FileContent(
            s3file_id=s3file_id,
            content=file_content,
            file_type="json",
        )
        db.add(new_content)
    db.commit()


def update_or_insert_stats(s3file_id: int, file_content: str, workstream: str, db: Session):
    """Helper function to update or insert file stats."""
    existing_file_stats = (
        db.query(Stat).filter(Stat.s3file_id == s3file_id).first()
    )
    file_stats = process_json_data(file_content, workstream)
    
    if existing_file_stats:
        existing_file_stats.stats_data = file_stats
    else:
        new_file_stats = Stat(
            s3file_id=s3file_id,
            stats_data=file_stats,
        )
        db.add(new_file_stats)
    
    db.commit()

def delete_s3file(job, db: Session, existing_s3_file):
    # Delete associated content records
    content_records = (
        db.query(FileContent)
        .filter(FileContent.s3file_id == existing_s3_file.id)
        .all()
    )
    for content_record in content_records:
        db.delete(content_record)

    # Delete associated stats records
    stats_records = (
        db.query(Stat).filter(Stat.s3file_id == existing_s3_file.id).all()
    )
    for stats_record in stats_records:
        db.delete(stats_record)

    db.delete(existing_s3_file)  # Delete the S3 file entry
    db.commit()  # Commit the changes
    