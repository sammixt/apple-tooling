import logging
import pandas as pd
from sqlalchemy.orm import Session
from app.db.models import ConfigOption, DeliveredId
from app.db.database import get_db


logger = logging.getLogger(__name__)


class DeDuplication:
    def format_duplicate_message(self, duplicate_type: str) -> str:
        messages = {
            "internal": "This deliverable ID is duplicated within the input data",
            "database": "This deliverable ID already exists in the database",
        }
        return messages.get(duplicate_type, "Duplicate entry detected")

    def remove_duplicates(self, data):
        # Extract unique records by "deliverable_id"
        seen = set()
        unique_data = []
        duplicates = []

        for obj in data:
            deliverable_id = obj.get("deliverable_id")
            if deliverable_id in seen:
                duplicates.append(
                    {"deliverableId": deliverable_id, "message": [self.format_duplicate_message("internal")]}
                )
            else:
                seen.add(deliverable_id)
                unique_data.append(obj)

        return unique_data, duplicates

    # def remove_duplicates(self, data):
    #     df = pd.DataFrame(data)
    #     duplicates = df[df.duplicated(subset=["deliverable_id"], keep=False)]
    #     unique_data = df.drop_duplicates(subset=["deliverable_id"])

    #     internal_duplicates = [
    #         {"deliverableId": row["deliverable_id"], "message": [self.format_duplicate_message("internal")]}
    #         for _, row in duplicates.iterrows()
    #     ]

    #     return unique_data.to_dict(orient="records"), internal_duplicates

    def compare_with_postgres(self, unique_data):
        db: Session = next(get_db())
        config_option = db.query(ConfigOption).filter_by(name="delivered_id_check").first()
        delivered_id_check = config_option.value if config_option else True
        logger.info(f"delivered_id_check: {'true' if delivered_id_check else 'false'}")
        if not delivered_id_check:
            return unique_data, []
        deliverable_ids = [data["deliverable_id"] for data in unique_data]
        existing_ids = (
            db.query(DeliveredId.deliverable_id).filter(DeliveredId.deliverable_id.in_(deliverable_ids)).all()
        )
        existing_ids = {id_[0] for id_ in existing_ids}

        filtered_data = []
        db_duplicates = []
        for data in unique_data:
            if data["deliverable_id"] in existing_ids:
                db_duplicates.append(
                    {"deliverableId": data["deliverable_id"], "message": [self.format_duplicate_message("database")]}
                )
            else:
                filtered_data.append(data)

        return filtered_data, db_duplicates

    def validate(self, json_data):
        unique_data, internal_duplicates = self.remove_duplicates(json_data)
        filtered_data, db_duplicates = self.compare_with_postgres(unique_data)

        all_duplicates = internal_duplicates + db_duplicates

        return {"data": filtered_data, "errors": all_duplicates if all_duplicates else None}
