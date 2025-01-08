from fastapi import FastAPI, Depends
from app.db.exceptions import sqlalchemy_exception_handler
from app.routers import (
    external,
    user,
    role,
    s3file,
    stat,
    file_content,
    file_validation,
    pre_processing,
    logs,
    auth_router, 
    configs,
    convert,
    webhooks,
    git_processing
)
from app.db.redis_client import redis_client
from sqlalchemy.exc import SQLAlchemyError
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from app.db.logging_handler import setup_logging
import logging
from app.auth.dependencies import get_current_user, has_permission
from app.db.database import engine, Base
from app.db.activity_listener import setup_activity_logging
import psutil
from slowapi.middleware import SlowAPIMiddleware
from app.middleware.limiter import init_limiter


setup_logging()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="S3 Dashboard",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)


app.add_middleware(SlowAPIMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://apple-dashboard.turing.com",
        "http://localhost:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods.
    allow_headers=["*"],  # Allows all HTTP headers.
)

# Initialize the database
Base.metadata.create_all(bind=engine)

# Setup activity logging listeners
setup_activity_logging()

@app.on_event("startup")
async def startup_event():
    configs.validate_config()


@app.get("/")
async def read_root():
    # Example of using the redis_client
    logging.info("Root endpoint accessed.")
    redis_client.set("key", "Hello, Redis!")
    value = redis_client.get("key")
    return {"message": value.decode("utf-8")}


# Register Router
app.include_router(user.router, prefix="/api", tags=["users"], dependencies=[Depends(has_permission("user_management"))])
app.include_router(role.router, prefix="/api", tags=["roles"], dependencies=[Depends(has_permission("user_management"))])
app.include_router(s3file.router, prefix="/api", tags=["s3files"], dependencies=[Depends(get_current_user)])
app.include_router(stat.router, prefix="/api", tags=["stats"], dependencies=[Depends(get_current_user)])
app.include_router(file_content.router, prefix="/api", tags=["file_contents"], dependencies=[Depends(get_current_user)])
app.include_router(file_validation.router, prefix="/api", tags=["file_validations"], dependencies=[Depends(get_current_user)])
app.include_router(
    pre_processing.router, prefix="/api/processor", tags=["Pre Processing"], dependencies=[Depends(get_current_user)]
)
app.include_router(logs.router, prefix="/api", tags=["Logs"], dependencies=[Depends(has_permission("logs"))])
app.include_router(configs.router, prefix="/api", tags=["Configs"])

# Auth Routes
app.include_router(auth_router.router, prefix="/api", tags=["Auth"])

app.include_router(webhooks.router, prefix="/api", tags=["Webhooks"])

# Convert Routes
app.include_router(convert.router, prefix="/api", tags=["convert"], dependencies=[Depends(get_current_user)])

#Git Route
app.include_router(git_processing.router, prefix="/api", tags=["git"])

add_pagination(app)

# Register custom exception handlers
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

init_limiter(app)
