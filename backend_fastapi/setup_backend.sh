#!/bin/bash

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check for Docker installation
if ! command -v docker &> /dev/null; then
    log "Docker is not installed. Please install Docker and try again."
    exit 1
fi

# Check for Docker Compose installation
if ! command -v docker-compose &> /dev/null; then
    log "Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Check if the PostgreSQL image exists locally
POSTGRES_IMAGE="postgres:13"
if docker image ls | grep -q "$POSTGRES_IMAGE"; then
    log "PostgreSQL image '$POSTGRES_IMAGE' is already available locally."
else
    log "PostgreSQL image '$POSTGRES_IMAGE' not found locally. Pulling the image..."
    docker pull "$POSTGRES_IMAGE"
    log "PostgreSQL image pulled successfully."
fi

# Log the services being started
log "Starting backend services using Docker Compose..."

# Start the services
docker-compose up -d --build

# Wait for the database service to initialize
log "Waiting for PostgreSQL to initialize..."
sleep 10

# Display running services and configurations
log "Services are running. Here are the details:"
docker ps --filter "name=fastapi_app"
docker ps --filter "name=postgres_db"

log "Configuration details:"
log "  - App: http://localhost:5000"
log "  - PostgreSQL: postgresql://postgres:postgres@localhost:5432/apple-s3"