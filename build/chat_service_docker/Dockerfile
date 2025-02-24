# Single-stage Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install curl and necessary build dependencies for healthcheck and Python packages
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean

# Copy requirements and install dependencies
COPY ./src/backend/lib/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Expose the chat service port using the environment variable
EXPOSE ${CHAT_SERVICE_PORT}

# Start the FastAPI server using the environment variable
CMD ["sh", "-c", "uvicorn src.backend.main.main:main_app --host 0.0.0.0 --port ${CHAT_SERVICE_PORT}"]
