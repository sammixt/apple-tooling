import gzip
import io
import re
import boto3
from google.cloud import storage
from google.api_core.exceptions import Forbidden, NotFound
from app.config import settings
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.core.s3_client import S3Client
from app.db.database import SessionLocal
from app.db.models import ConfigOption


s3 = S3Client()


class ImageProcessor:
    def __init__(self, json_data, s3_folder):
        self.json_data = json_data
        self.s3_folder = s3_folder
        self.gcs_client = self.initialize_gcs_client()
        db = SessionLocal()
        apple_upload = db.query(ConfigOption).filter_by(name="enable_penguin_s3_upload").first()
        apple_upload_value = apple_upload.value if apple_upload else False

        if apple_upload_value:
            s3._refresh_if_credentials_expired()
            self.s3_client = s3.s3_client
            self.s3_bucket = settings.AWS_BUCKET_NAME
        else:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.DEV_AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.DEV_AWS_SECRET_ACCESS_KEY,
            )
            self.s3_bucket = settings.DEV_AWS_BUCKET_NAME

    def initialize_gcs_client(self):
        return storage.Client.from_service_account_json("turing-gpt.json")

    def gcloud_to_s3(self, bucket_name, source_blob_name, s3_key):
        buffer = io.BytesIO()

        try:
            bucket = self.gcs_client.bucket(bucket_name)
            blob = bucket.blob(source_blob_name)

            with blob.open("rb") as file_stream:
                if blob.content_encoding == "gzip":
                    with gzip.GzipFile(fileobj=file_stream) as decompressed_file:
                        buffer.write(decompressed_file.read())
                else:
                    buffer.write(file_stream.read())
            buffer.seek(0)

            self.s3_client.upload_fileobj(buffer, self.s3_bucket, s3_key)
            print(f"File {source_blob_name} from uploaded to {s3_key} in {self.s3_bucket}")

        except NotFound:
            print(f"Error: The object {source_blob_name} was not found in {bucket_name}")
        except Forbidden as e:
            print(f"Access Denied: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            buffer.close()

    def extract_uuid(self, url):
        match = re.search(r"([a-f0-9\-]{36})", url)
        return match.group(0) if match else None

    def process_item(self, item):
        turing_task_url = item["metadata"].get("turing_task_url")
        deliverable_id = self.extract_uuid(turing_task_url)
        gcs_url = item["messages"][1]["images_list"][0]["uri"]
        file_name = os.path.basename(gcs_url)
        _, file_extension = os.path.splitext(file_name)

        if not file_extension:
            file_extension = ".jpeg"

        s3_key = f"{self.s3_folder}{deliverable_id}{file_extension}"

        if gcs_url.startswith("gcs://"):
            gcs_url = gcs_url.replace("gcs://", "gs://")
        bucket_name, source_blob_name = gcs_url[5:].split("/", 1)

        self.gcloud_to_s3(bucket_name, source_blob_name, s3_key)

    def process_all_items(self):
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.process_item, item) for item in self.json_data]

            for future in as_completed(futures):
                try:
                    future.result()  # Check for exceptions
                except Exception as e:
                    print(f"An error occurred: {e}")
