from datetime import datetime, timezone
from sqlalchemy import select, delete
from app.db.models import Log
from app.db.database import SessionLocal

def cleanup_old_logs():
    """
    Celery task to clean up logs in the database.
    Removes logs exceeding 500 entries, keeping the most recent 500.
    """
    try:
        # Count total logs
        db = SessionLocal()
        count_query = select(Log.id)
        result = db.execute(count_query)
        log_ids = list(result.scalars().all())
        
        if len(log_ids) > 500:
            print(f"Log count exceeded 500. Deleting {len(log_ids) - 500} oldest logs.")
            
            # Delete oldest logs
            delete_query = (
                delete(Log)
                .where(Log.id.in_(log_ids[: len(log_ids) - 500]))
            )
            db.execute(delete_query)
            db.commit()
            print("Log cleanup completed successfully.")
    except Exception as e:
        print(f"Error during log cleanup: {e}")
        
    return "Log cleanup task completed"