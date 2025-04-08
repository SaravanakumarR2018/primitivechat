# Single-stage Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install curl and necessary build dependencies for healthcheck and Python packages
RUN apt-get update && \
    apt-get install -y curl default-mysql-client libmagic1 libmagic-dev tesseract-ocr && \
    apt-get clean

# Install hf_xet to speed up model downloads from Hugging Face
RUN pip install --no-cache-dir "huggingface_hub[hf_xet]"

# Copy requirements and install dependencies
COPY ./src/backend/lib/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set environment variable for model directory
ENV MODEL_DIR=/models

# Create the model directory
RUN mkdir -p $MODEL_DIR

# Download and save the Sentence Transformer model in the directory
RUN python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); model.save('$MODEL_DIR')"

# Download the Spacy model during the build
RUN python -m spacy download en_core_web_sm

# Copy supervisord configuration
COPY ./src/backend/supervisord.conf /etc/supervisor/supervisord.conf

# Expose the chat service port using the environment variable
EXPOSE ${CHAT_SERVICE_PORT}

# Start the uvicorn and file_vectorize server using supervisord
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
