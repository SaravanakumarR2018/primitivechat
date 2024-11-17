#!/bin/bash

# Exit on any error
set -e

# Get the directory of the script and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Script directory: $SCRIPT_DIR"
PROJECT_ROOT="$SCRIPT_DIR/.."  # Use the local directory structure

export PROJECT_ROOT
echo "PROJECT_ROOT is set to: $PROJECT_ROOT"

# Move to the backend directory
cd "$PROJECT_ROOT/src/backend" || exit 1
echo "Changed directory to src/backend"

$PROJECT_ROOT/build/kill_server.bash

# Start Docker containers in detached mode
echo "Starting Docker containers in detached mode..."
docker-compose up -d

# Path for the log file (create it in the build directory with a timestamp)
LOG_FILE="$PROJECT_ROOT/build/docker_logs_$(date +"%Y-%m-%d_%H-%M-%S").log"
echo "Logs will be saved to: $LOG_FILE"

# Start Docker containers in detached mode
echo "Starting Docker containers in detached mode..."
docker-compose up -d

# Print logs to a file immediately after starting, appending with timestamps
echo "Printing logs from Docker containers to $LOG_FILE..."
docker-compose logs -f > "$LOG_FILE" &

# Save the process ID of the logs command so it can be killed when the script ends
LOG_PID=$!

# Ensure logs are captured until the script ends
trap 'kill $LOG_PID 2>/dev/null' EXIT

# Check if the Ollama server is up by hitting the health endpoint
URL="http://localhost:11434/"
MAX_WAIT_TIME=1200  # 20 minutes
CHECK_INTERVAL=5    # 5 seconds
elapsed_time=0

while [ "$elapsed_time" -lt "$MAX_WAIT_TIME" ]; do
    echo "Checking Ollama server status at $URL..."

    # Capture the response and status code from curl
    RESPONSE=$(curl -s -w "%{http_code}" "$URL")

    # Check if the response code is 200 (successful)
    HTTP_CODE="${RESPONSE: -3}"
    BODY="${RESPONSE%${HTTP_CODE}}"

    # Print the full response
    echo "Response Body: $BODY"
    echo "HTTP Status Code: $HTTP_CODE"

    if [ "$HTTP_CODE" -eq 200 ]; then
        echo "Ollama server is up and running!"
        break
    else
        echo "Server is not up yet. Response code: $HTTP_CODE. Checking again in $CHECK_INTERVAL seconds..."
    fi

    remaining_time=$((MAX_WAIT_TIME - elapsed_time))
    echo "Remaining time: $remaining_time seconds"
    sleep "$CHECK_INTERVAL"
    elapsed_time=$((elapsed_time + CHECK_INTERVAL))
done

if [ "$elapsed_time" -ge "$MAX_WAIT_TIME" ]; then
    echo "Ollama server did not come up within the expected time. Exiting..."
    exit 1
fi

# Pull the model (llama3.2:3b) once the server is up
echo "Pulling the llama3.2:3b model..."
PULL_RESPONSE=$(curl -s -w "%{http_code}" http://localhost:11434/api/pull -d '{
  "name": "llama3.2:3b"
}')

PULL_HTTP_CODE="${PULL_RESPONSE: -3}"
PULL_BODY="${PULL_RESPONSE%${PULL_HTTP_CODE}}"

# Print the full pull response
echo "Response Body: $PULL_BODY"
echo "HTTP Status Code: $PULL_HTTP_CODE"

if [ "$PULL_HTTP_CODE" -eq 200 ]; then
  echo "Model llama3.2:3b pulled successfully."
else
  echo "Failed to pull model. Response code: $PULL_HTTP_CODE"
  exit 1
fi

# Check if the model was successfully pulled by generating a response
echo "Checking if model is working by generating a response..."
GEN_RESPONSE=$(curl -s -w "%{http_code}" http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Is the sky blue? Give one word as an answer. Answer as either True or False.",
  "stream": false
}')

GEN_HTTP_CODE="${GEN_RESPONSE: -3}"
GEN_BODY="${GEN_RESPONSE%${GEN_HTTP_CODE}}"

# Print the full generate response
echo "Response Body: $GEN_BODY"
echo "HTTP Status Code: $GEN_HTTP_CODE"

if [ "$GEN_HTTP_CODE" -eq 200 ]; then
  echo "Ollama server is working fine. Model generated a response. Now checking HTTP Server..."
else
  echo "Ollama server failed to generate a response. Response code: $GEN_HTTP_CODE"
  exit 1
fi
# Check if the server is up (replace http://localhost:8000 with the actual URL if needed)
URL="http://localhost:8000"  # Updated URL to localhost
EXPECTED_OUTPUT='{"message":"The server is up and running!"}'
MAX_WAIT_TIME=1200  # 20 minutes
CHECK_INTERVAL=5    # 5 seconds
elapsed_time=0

while [ "$elapsed_time" -lt "$MAX_WAIT_TIME" ]; do
    echo "Checking server status at $URL..."

    # Capture the response from curl
    RESPONSE=$(curl -s "$URL" || echo "curl failed")

    # Check if the response matches the expected output
    if [ "$RESPONSE" = "$EXPECTED_OUTPUT" ]; then
        echo "Docker logs: $LOG_FILE"
        echo "Server is up and running!"
        echo "Server is up: $URL"
        exit 0
    else
        echo "Server response does not match expected output. Received: $RESPONSE"
        echo "Server is not up yet. Checking again in $CHECK_INTERVAL seconds..."
    fi

    remaining_time=$((MAX_WAIT_TIME - elapsed_time))
    echo "Remaining time: $remaining_time seconds"
    sleep "$CHECK_INTERVAL"
    elapsed_time=$((elapsed_time + CHECK_INTERVAL))
done

echo "Docker logs: $LOG_FILE"
echo "Server did not come up within the expected time. Exiting..."
exit 1
