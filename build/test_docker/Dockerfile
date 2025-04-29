FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY build/test_docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables (if needed)
# ENV ...

COPY . .

# Command to run the tests (this will be overridden by the script)
CMD ["python", "-m", "unittest", "discover", "-s", "test", "-p", "test_*.py"]