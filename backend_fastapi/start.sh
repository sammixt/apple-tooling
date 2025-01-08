#!/bin/bash

# Function to check if Redis is installed
check_redis_installed() {
    if ! command -v redis-server &> /dev/null; then
        echo "Redis is not installed. Installing Redis..."
        # Update package index and install Redis
        sudo apt update
        sudo apt install -y redis-server
    else
        echo "Redis is already installed."
    fi
}

# Function to install PostgreSQL development libraries
install_postgres_libs() {
    echo "Installing PostgreSQL development libraries..."
    sudo apt install -y libpq-dev build-essential
}

# Function to start Redis service
start_redis() {
    echo "Starting Redis service..."
    sudo systemctl start redis-server
    # Optional: enable Redis to start on boot
    sudo systemctl enable redis-server
}

# Check and install Redis if not installed
check_redis_installed

# Install PostgreSQL development libraries
install_postgres_libs

# Start Redis service
start_redis

# Install Python dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head
python -m app.scripts.seed_manager

# Start FastAPI application
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
