from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.database import get_db, SessionLocal
from app.db.models import ConfigOption
from app.schemas.configs import ConfigurationModel
import logging
import sys
from app.auth.dependencies import has_permission

router = APIRouter()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@router.on_event("startup")
def validate_config():
    # Fetch configuration values
    try:
        # Use a context manager for database session
        with SessionLocal() as db:
            apple_upload = db.query(ConfigOption).filter_by(name="enable_penguin_s3_upload").first()
            turing_upload = db.query(ConfigOption).filter_by(name="enable_turing_s3_upload").first()

            apple_upload_value = apple_upload.value if apple_upload else False
            turing_upload_value = turing_upload.value if turing_upload else False

            # Validation logic
            if apple_upload_value and turing_upload_value:
                print("Both enable_penguin_s3_upload and enable_turing_s3_upload cannot be True at the same time.")
                sys.exit(1)
    except Exception as e:
        print(f"Error in startup event: {e}")
        sys.exit(1)


@router.get("/config", response_model=ConfigurationModel)
def get_config(db: Session = Depends(get_db)):
    # Fetch all configurations
    config_options = db.query(ConfigOption).all()
    config_dict = {option.name: option.value for option in config_options}

    return ConfigurationModel(configuration=config_dict)


@router.post("/config", dependencies=[Depends(has_permission("configuration"))], response_model=ConfigurationModel)
def update_config(config: ConfigurationModel, db: Session = Depends(get_db)):
    # Extract configuration from the request
    updates = config.configuration
    updated_values = {}

    if "enable_turing_s3_upload" in updates and "enable_penguin_s3_upload" in updates:
        if updates["enable_turing_s3_upload"] == updates["enable_penguin_s3_upload"]:
            raise HTTPException(
                status_code=400,
                detail="enable_turing_s3_upload and enable_penguin_s3_upload cannot have the same value.",
            )

    # Iterate through provided configuration keys and update them
    for name, value in updates.items():
        if not isinstance(value, bool):
            raise HTTPException(status_code=400, detail=f"Invalid value for {name}. Expected a boolean.")

        # Fetch or create the configuration option
        config_option = db.query(ConfigOption).filter_by(name=name).first()
        if not config_option:
            config_option = ConfigOption(name=name, value=value)
            db.add(config_option)
        elif config_option.value != value:
            config_option.value = value  # Update only if value has changed

        updated_values[name] = value

    db.commit()

    all_config_options = db.query(ConfigOption).all()
    response_config = {option.name: option.value for option in all_config_options}

    return ConfigurationModel(configuration=response_config)
