FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY build/test_docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y docker.io

# Create the folder and add the test file
RUN mkdir -p /app/test/IntegrationTests && \
    echo "import unittest\n\nclass TestSample(unittest.TestCase):\n    def test_success(self):\n        print('testcase succeeds')\n        self.assertTrue(True)\n\nif __name__ == '__main__':\n    unittest.main()" > /app/test/IntegrationTests/test_sample.py

# Command to run the tests
CMD ["python", "-m", "unittest", "discover", "-s", "test", "-p", "test_*.py"]
