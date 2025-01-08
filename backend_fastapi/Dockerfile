# Use official Python image as base
FROM python:3.12.3

# Install system dependencies including Redis, gcc, and libpq-dev for PostgreSQL
RUN apt-get update && \
    apt-get install -y redis-server gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project to the working directory
COPY . .

# Expose the port your FastAPI app runs on
EXPOSE 5000

# Use bash instead of sh for process management
SHELL ["/bin/bash", "-c"]

# Run Redis, migrations, and both uvicorn and celery processes
CMD redis-server --daemonize yes && \
    #alembic upgrade head && \
    python -m app.scripts.seed_manager && \
    uvicorn app.main:app --host 0.0.0.0 --port 5000 & \
    celery -A app.jobs.celery_task.celery_app beat --loglevel=info & \
    celery -A app.jobs.celery_task.celery_app worker --loglevel=info -E --concurrency=3 & \
    wait