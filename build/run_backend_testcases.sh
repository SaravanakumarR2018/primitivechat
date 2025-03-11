#!/bin/bash
set -e  # Stop execution if any command fails

# Help function
help() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -f <pattern>  Run tests only for files matching the pattern (e.g., 'test_*.py', 'test_database.py')."
  echo "  -h            Show this help message."
  echo ""
  echo "Example:"
  echo "  $0 -f test_database.py"
  echo "  $0 -h"
}

# Find the project root directory
echo "Finding project root directory..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Script directory: $SCRIPT_DIR"
PROJECT_ROOT="$SCRIPT_DIR/.."  # Use the local directory structure

echo "Project root directory: $PROJECT_ROOT"
TEST_DIR="${PROJECT_ROOT}/test/IntegrationTests"

# Default test pattern (run all tests)
TEST_PATTERN="test_*.py"
echo "Default test pattern: $TEST_PATTERN"

# Define the desired values for the environment variables
CHAT_SERVICE_HOST="chat_service"
OLLAMA_SERVICE_HOST="ollama"

# Process command-line arguments
echo "Processing command-line arguments..."
while getopts "f:h" opt; do
  case $opt in
    f)
      TEST_PATTERN="$OPTARG"
      echo "Using test pattern: $TEST_PATTERN"
      ;;
    h)
      help
      exit 0
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      help
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      help
      exit 1
      ;;
  esac
done
echo "Finished processing command-line arguments."

# Define Dockerfile path
DOCKERFILE_DIR="${PROJECT_ROOT}/build/test_docker"
DOCKERFILE="${DOCKERFILE_DIR}/Dockerfile"
echo "Dockerfile path: $DOCKERFILE"

# Check if Dockerfile exists
echo "Checking if Dockerfile exists..."
if [ ! -f "$DOCKERFILE" ]; then
  echo "Error: Dockerfile not found at $DOCKERFILE"
  exit 1
fi
echo "Dockerfile exists."

# Build the Docker image
IMAGE_NAME="primitivechat_test_image"
echo "Building Docker image..."
docker build -t "$IMAGE_NAME" "$PROJECT_ROOT" -f "$DOCKERFILE"
echo "Docker image built with name: $IMAGE_NAME"

# Create a temporary env file
TEMP_ENV_FILE=$(mktemp)
echo "Creating temporary env file: $TEMP_ENV_FILE"

# Copy the original .env file to the temporary file
cp "$PROJECT_ROOT/src/backend/.env" "$TEMP_ENV_FILE"

# Replace the environment variables in the temporary file
sed -i "s/^CHAT_SERVICE_HOST=.*/CHAT_SERVICE_HOST=$CHAT_SERVICE_HOST/" "$TEMP_ENV_FILE"
sed -i "s/^OLLAMA_SERVICE_HOST=.*/OLLAMA_SERVICE_HOST=$OLLAMA_SERVICE_HOST/" "$TEMP_ENV_FILE"

# Construct the test command to run inside the container
TEST_COMMAND=("bash" "-c" "echo CHAT_SERVICE_HOST=$CHAT_SERVICE_HOST && echo OLLAMA_SERVICE_HOST=$OLLAMA_SERVICE_HOST && python3 -m unittest discover -s /app/test/IntegrationTests -p \"$TEST_PATTERN\"")
echo "Container test command: ${TEST_COMMAND[@]}"

# Run the tests inside the Docker container, mounting the project directory
echo "Running tests inside Docker container..."
docker run --rm --network=primitivechat_network -v "$PROJECT_ROOT:/app" --env-file "$TEMP_ENV_FILE" "$IMAGE_NAME" "${TEST_COMMAND[@]}"
echo "Tests finished running inside Docker container."

# Get the exit code from the docker container
TEST_EXIT_CODE=$?
echo "Test exit code: $TEST_EXIT_CODE"

# Clean up the temporary env file
echo "Cleaning up temporary env file..."
rm "$TEMP_ENV_FILE"

# Exit with the test result status
echo "Exiting with test result status: $TEST_EXIT_CODE"
exit $TEST_EXIT_CODE