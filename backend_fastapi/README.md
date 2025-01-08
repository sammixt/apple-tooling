# FastAPI Project

This project is a FastAPI application configured to run inside a Docker container. It includes Redis as a caching mechanism and connects to a PostgreSQL database.

## Prerequisites
- **Docker**: Ensure Docker is installed on your system. You can check by running `docker --version`.
- **Docker Compose (optional)**: For multi-container applications, consider using Docker Compose.

## Build and Run

### Step 1: Build the Docker Image

To build the Docker image, navigate to the project directory and run:

```bash
docker build -t fastapi-app .
```

### Step 2: Run the Docker Container

To run the container and map the FastAPI app to your local machine's port:

```bash
docker run -p 5001:5000 fastapi-app
```

### Accessing the Application

Once the container is running, access the FastAPI application at [http://localhost:5000](http://localhost:5000).

---

## Additional Information

### Environment Variables
- Configure any required environment variables, such as database URLs, in a `.env` file in the root directory.
- For example:
  ```plaintext
  DATABASE_URL=postgresql://user:password@host:port/dbname
  REDIS_HOST=localhost
  REDIS_PORT=6379
  AWS_ROLE_ARN=arn:aws:iam::ACCOUNT_ID:role/turing-data-drops-role
  AWS_ACCESS_KEY_ID=
  AWS_SECRET_ACCESS_KEY=
  AWS_BUCKET_NAME=og82-drop-turing
  ```

### Create Database Migrations
```
alembic-autogen-check || alembic revision --autogenerate -m "comment"
```

### Running Database Migrations
- The `Dockerfile` automatically runs Alembic migrations (`alembic upgrade head`) before starting the application.
- **Note**: Ensure the Alembic configurations (`alembic.ini` and `env.py`) are correctly set up to point to your database URL.

### Redis and Database Configuration
- Redis and PostgreSQL connections are configured in the FastAPI app. Ensure the correct URLs are used in the `.env` file.
- If running Redis and PostgreSQL outside of Docker, adjust the connection strings in your environment accordingly.

### Common Commands
- **To Rebuild** the image after code changes:
  ```bash
  docker build -t fastapi-app .
  ```
- **To Stop the Running Container**:
  ```bash
  docker ps   # to list running containers and get the container ID
  docker stop <container_id>
  ```
- **To Run Worker**:
  ```bash
  python -m app.jobs.worker
  ```

