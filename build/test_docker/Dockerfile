FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install curl and necessary build dependencies for Python packages
RUN apt-get update && \
    apt-get install -y curl default-mysql-client libmagic1 libmagic-dev tesseract-ocr && \
    apt-get clean

# Copy the requirements file and install dependencies
COPY build/test_docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variable for model directory
ENV MODEL_DIR=/models

# Create the model directory
RUN mkdir -p $MODEL_DIR

# Download and save the Sentence Transformer model in the directory
RUN python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); model.save('$MODEL_DIR')"

# Create the folder and add the test file
RUN mkdir -p /app/test/IntegrationTests && \
    echo "import unittest\n\nclass TestSample(unittest.TestCase):\n    def test_success(self):\n        print('testcase succeeds')\n        self.assertTrue(True)\n\nif __name__ == '__main__':\n    unittest.main()" > /app/test/IntegrationTests/test_sample.py

# Command to run the tests
CMD ["python", "-m", "unittest", "discover", "-s", "test", "-p", "test_*.py"]
