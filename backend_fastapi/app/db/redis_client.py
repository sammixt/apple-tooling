import os
import redis
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Create a Redis connection using environment variables
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = os.getenv('REDIS_PORT', 6379)
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

# Optionally, you can check the connection
try:
    redis_client.ping()
    print("Connected to Redis!")
except redis.ConnectionError:
    print("Could not connect to Redis.")
