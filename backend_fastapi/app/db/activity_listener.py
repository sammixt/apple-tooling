from sqlalchemy.event import listen
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import get_history
from datetime import datetime
import json

from app.db.models import ActivityLog, Base  # Base is your declarative base
from app.auth.dependencies import user_session


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, "__dict__"):  # Handle custom objects
        return obj.__dict__
    return str(obj)  # Fallback to string representation



def serialize_attribute(value):
    """
    Safely serialize an attribute to ensure JSON compatibility.
    Handles dates, relationships, and other non-serializable types.
    """
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    elif hasattr(value, "__dict__"):
        # Attempt to serialize as a dictionary, excluding private attributes
        return {k: v for k, v in value.__dict__.items() if not k.startswith("_")}
    elif isinstance(value, list):
        # Serialize each item in the list
        return [serialize_attribute(item) for item in value]
    elif isinstance(value, dict):
        # Serialize each key-value pair in the dictionary
        return {k: serialize_attribute(v) for k, v in value.items()}
    else:
        return str(value)  # Fallback to string representation

def log_activity_event(mapper, connection, target, action):
    """
    Automatically logs activity based on SQLAlchemy events.
    """
    # Skip logging if the affected table is 'activity_logs', 'logs', or 'file_contents'
    if not hasattr(target, "__tablename__") or target.__tablename__ in ["activity_logs", "logs", "file_contents", "delivery_files", "pre_processing_file_json"]:
        return

    # Get session info
    user_id = user_session.get("user_id")

    # Prepare details for the log entry
    details = {}
    try:
        if action == "UPDATE":
            # Capture changes for UPDATE
            for attr in mapper.attrs:
                hist = get_history(target, attr.key)
                if hist.has_changes():
                    details[attr.key] = {
                        "old": serialize_attribute(hist.deleted[0]) if hist.deleted else None,
                        "new": serialize_attribute(hist.added[0]) if hist.added else None,
                    }
        elif action == "CREATE":
            # Capture initial values for CREATE
            details = {attr.key: serialize_attribute(getattr(target, attr.key)) for attr in mapper.column_attrs}
        elif action == "DELETE":
            # Capture final state for DELETE
            details = {attr.key: serialize_attribute(getattr(target, attr.key)) for attr in mapper.column_attrs}

        # Ensure details are JSON serializable
        details = json.loads(json.dumps(details, default=serialize_datetime))
    except Exception as e:
        import traceback
        print(f"Error serializing details: {e}")
        traceback.print_exc()
        details = {"error": f"Failed to serialize details: {e}"}

    # Create the log entry
    log_entry = ActivityLog(
        user_id=user_id,
        action=action,
        resource=target.__tablename__,
        resource_id=str(getattr(target, "id", None)),
        details=details,
    )

    # Use the same connection to insert into the activity_logs table
    try:
        with Session(bind=connection) as session:
            session.add(log_entry)
            session.commit()
    except Exception as e:
        print(f"Error logging to database: {e}")


# Register listeners
def setup_activity_logging():
    """
    Attach listeners for all models inheriting from Base.
    """
    for mapper in Base.registry.mappers:
        model = mapper.class_
        if hasattr(model, "__tablename__") and model.__tablename__ not in ["activity_logs", "logs", "file_contents", "delivery_files", "pre_processing_file_json"]:
            listen(model, "after_insert", log_after_insert)
            listen(model, "after_update", log_after_update)
            listen(model, "after_delete", log_after_delete)

def log_after_insert(mapper, connection, target):
    log_activity_event(mapper, connection, target, "CREATE")

def log_after_update(mapper, connection, target):
    log_activity_event(mapper, connection, target, "UPDATE")

def log_after_delete(mapper, connection, target):
    log_activity_event(mapper, connection, target, "DELETE")