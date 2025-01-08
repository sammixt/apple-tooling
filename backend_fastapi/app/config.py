import os
from dotenv import load_dotenv


load_dotenv(override=True)


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    REDIS_HOST: str = os.getenv("REDIS_HOST")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))

    AWS_ROLE_ARN: str = os.getenv("AWS_ROLE_ARN")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_BUCKET_NAME: str = os.getenv("AWS_BUCKET_NAME")

    DEV_AWS_ACCESS_KEY_ID: str = os.getenv("DEV_AWS_ACCESS_KEY_ID")
    DEV_AWS_SECRET_ACCESS_KEY: str = os.getenv("DEV_AWS_SECRET_ACCESS_KEY")
    DEV_AWS_BUCKET_NAME: str = os.getenv("DEV_AWS_BUCKET_NAME")

    GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64"
    )


settings = Settings()
