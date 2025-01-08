from functools import wraps
from fastapi import HTTPException
from psutil import virtual_memory
import logging

logger = logging.getLogger(__name__)


def memory_check_middleware(min_memory_gb: float = 4.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            memory = virtual_memory()
            available_gb = memory.available / 1024**3

            if available_gb < min_memory_gb:
                logger.error(f"Insufficient memory! Available: {available_gb:.2f}GB, Required: {min_memory_gb}GB")
                raise HTTPException(
                    status_code=503,
                    detail=f"Our servers are currently experiencing heavy traffic. Please try again in a few minutes. We apologize for the inconvenience!",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
