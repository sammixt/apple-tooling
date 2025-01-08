# Add all the common data base exceptions

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    print(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Database error occurred. Please try again later."},
    )
