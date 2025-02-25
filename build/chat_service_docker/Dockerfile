# Single-stage Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install curl and necessary build dependencies for healthcheck and Python packages
RUN apt-get update && \
    apt-get install -y curl && libmagic1 libmagic-dev tesseract-ocr \
    apt-get clean

# Copy requirements and install dependencies
COPY ./src/backend/lib/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Download and cache the Sentence Transformer model during the build
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Download the Spacy model during the build
RUN python -m spacy download en_core_web_sm

# Copy supervisord configuration
COPY ./src/backend/supervisord.conf /etc/supervisor/supervisord.conf

# Expose the chat service port using the environment variable
EXPOSE ${CHAT_SERVICE_PORT}

# Start the uvicorn and file_vectorize server using supervisord
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
