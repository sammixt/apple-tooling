import logging
import traceback
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from contextlib import contextmanager
from app.db.database import SessionLocal
from app.db.models import Log

class LoggingHandler(logging.Handler):
    def __init__(self, db_session_factory):
        super().__init__()
        self.db_session_factory = db_session_factory

    def emit(self, record):
        session: Session = self.db_session_factory()
        try:
            # Format the log message
            log_message = self.format(record)

            # Create a new log entry
            log_entry = Log(
                log_level=record.levelname,
                log_message=log_message,
                created_at=datetime.utcnow(),
            )
            session.add(log_entry)
            session.commit()
        except SQLAlchemyError as e:
            print(f"Error logging to database: {e}")
            session.rollback()
        finally:
            session.close()
            
def setup_logging():
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Add SQLAlchemy handler
    db_handler = LoggingHandler(SessionLocal)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    db_handler.setFormatter(formatter)
    logger.addHandler(db_handler)

    # Optionally, add console handler for debugging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)