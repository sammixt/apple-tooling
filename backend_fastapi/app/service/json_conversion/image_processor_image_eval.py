import gzip
import io
import re
import boto3
from google.cloud import storage
from google.api_core.exceptions import Forbidden, NotFound
from app.config import settings
import os
from concurrent.futures import ThreadPoolExecutor, as_completed


class ImageProcessorImageEval:
    def __init__(self, json_data, s3_folder):
        self.json_data = json_data
        self.s3_bucket = settings.DEV_AWS_BUCKET_NAME
        self.s3_folder = s3_folder
        self.gcs_client = self.initialize_gcs_client()
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.DEV_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.DEV_AWS_SECRET_ACCESS_KEY,
        )

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

    @staticmethod
    def extract_numeric_prefix(text):
        # Use regular expression to capture the numeric prefix at the beginning of the string
        match = re.match(r"^(\d+)_", text)
        if match:
            return match.group(1)
        else:
            return None

    def process_item(self, item):
        numeric_value = ""
        for msg in item["messages"]:

            if msg["role"] == "user":
                numeric_value = self.extract_numeric_prefix(msg["text"])

            if msg["role"] == "assistant":
                for option in msg["response_options"]:
                    if not option["text"] == "no image":
                        model_id = option["model_id"].replace("-", "_")
                        image_name = f"{model_id}_{numeric_value}"

                        gcs_url = option["text"]
                        file_name = os.path.basename(gcs_url)
                        _, file_extension = os.path.splitext(file_name)

                        if not file_extension:
                            file_extension = ".jpeg"

                        s3_key = f"{self.s3_folder}{image_name}{file_extension}"

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
