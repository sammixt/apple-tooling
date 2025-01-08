import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from datetime import datetime, timezone
import json
from dotenv import load_dotenv
import logging

load_dotenv()  # Load environment variables from .env file


class S3Client:
    def __init__(self, session_name="s3_session"):
        self.role_arn = os.getenv("AWS_ROLE_ARN")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("AWS_BUCKET_NAME")
        self.session_name = session_name
        self.s3_client = None
        self.credentials = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Check for missing environment variables
        missing_env_vars = []
        if not self.role_arn:
            missing_env_vars.append("AWS_ROLE_ARN")
        if not self.aws_access_key_id:
            missing_env_vars.append("AWS_ACCESS_KEY_ID")
        if not self.aws_secret_access_key:
            missing_env_vars.append("AWS_SECRET_ACCESS_KEY")
        if not self.bucket_name:
            missing_env_vars.append("AWS_BUCKET_NAME")

        if missing_env_vars:
            self.logger.info(f"Error: Missing environment variables: {', '.join(missing_env_vars)}")
            raise EnvironmentError(f"Missing environment variables: {', '.join(missing_env_vars)}")
        
        self._assume_role_and_initialize()

    def _assume_role_and_initialize(self):
        try:
            # Initialize STS client with provided credentials if available
            sts_client = boto3.client(
                "sts",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
            )

            # Assume the role
            assumed_role = sts_client.assume_role(
                RoleArn=self.role_arn, RoleSessionName=self.session_name
            )

            # Create an S3 client using the assumed role's credentials
            self.credentials = assumed_role["Credentials"]
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=self.credentials["AccessKeyId"],
                aws_secret_access_key=self.credentials["SecretAccessKey"],
                aws_session_token=self.credentials["SessionToken"],
            )
        except (NoCredentialsError, PartialCredentialsError) as e:
            self.logger.error(f"Credentials error: {str(e)}", exc_info=True)
            print(f"Credentials error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Failed to assume role: {str(e)}", exc_info=True)
            print(f"Failed to assume role: {str(e)}")

    def _refresh_if_credentials_expired(self):
        """Refresh credentials if they are expired."""
        if not self.credentials:
            self.logger.info("Credentials are not initialized; reinitializing.")
            self._assume_role_and_initialize()
            return

        expiration = self.credentials["Expiration"]
        current_time = datetime.now(timezone.utc)
        if current_time >= expiration:
            self.logger.info("Credentials expired; reinitializing.")
            self._assume_role_and_initialize()

    def download_file(self, object_key):
        """Download a file from S3 and return its content."""
        # Refresh credentials if expired
        self._refresh_if_credentials_expired()
        
        if not self.s3_client:
            print("Error: S3 client is not initialized.")
            return None
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=object_key
            )
            file_content = response["Body"].read().decode("utf-8")
            return json.loads(file_content)  # Assuming the file is a JSON
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == "NoSuchKey":
                print(f"Error: The file {object_key} does not exist in the bucket {self.bucket_name}.")
            elif error_code == "AccessDenied":
                print(f"Error: Access denied for {object_key} in bucket {self.bucket_name}. Check your permissions.")
            else:
                print(f"Error downloading file from S3: {e.response['Error']['Message']}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON content from {object_key}: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return None
