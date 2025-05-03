#!/bin/bash

# Exit on any error
set -e

# Get the directory of the script and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Script directory: $SCRIPT_DIR"
PROJECT_ROOT="$SCRIPT_DIR/.."  # Use the local directory structure

# Detect macOS and setup docker buildx for amd64 emulation
IS_MAC=false
if [ "$(uname -s)" = "Darwin" ]; then
    IS_MAC=true
    echo "Detected macOS system. Setting up buildx for amd64 emulation..."
    docker buildx create --use --name multiarch-builder 2>/dev/null || docker buildx use multiarch-builder
fi


export PROJECT_ROOT
echo "PROJECT_ROOT is set to: $PROJECT_ROOT"

# Load environment variables from .env file
if [ -f "$PROJECT_ROOT/src/backend/.env" ]; then
    echo "Loading environment variables from .env file..."

    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        case "$key" in
            \#*|"") continue ;;
        esac

        # Trim whitespace from key and value
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)

        # Check if the key is not empty
        if [[ -n "$key" ]]; then
            # Strip quotes around the value if present
            value=$(echo "$value" | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/")
            export "$key=$value"
        else
            echo "Skipping invalid line: $key=$value"
        fi
    done < "$PROJECT_ROOT/src/backend/.env"

    echo "Exported environment variables:"
    while IFS='=' read -r key value; do
        case "$key" in
            \#*|"") continue ;;
        esac
        echo "$key=$(eval echo \$$key)"  # Print variable name and its value
    done < "$PROJECT_ROOT/src/backend/.env"
else
    echo ".env file not found in $PROJECT_ROOT/src/backend/. Exiting..."
    exit 1
fi

# Move to the backend directory
cd "$PROJECT_ROOT/src/backend" || exit 1
echo "Changed directory to src/backend"

# Call the get_env_file.sh script from the root of the project
echo "Calling get_env_file.sh script..."
$PROJECT_ROOT/src/frontend/scripts/get_env_file.sh

# Check if the get_env_file.sh script executed successfully
if [ $? -ne 0 ]; then
    echo "get_env_file.sh script failed. Exiting..."
    exit 1
fi

$PROJECT_ROOT/build/kill_server.sh

# Check if the kill_server.sh script executed successfully
if [ $? -ne 0 ]; then
    echo "kill_server.sh script failed. Exiting..."
    exit 1
fi

#Start Docker build command
echo "Building Docker image chat_service_image"
if [ "$IS_MAC" = true ]; then
    docker buildx build \
        --platform linux/amd64 \
        -t chat_service_image:latest \
        -f "$PROJECT_ROOT/build/chat_service_docker/Dockerfile" \
        "$PROJECT_ROOT" --load
else
    docker build -t chat_service_image:latest -f "$PROJECT_ROOT/build/chat_service_docker/Dockerfile" "$PROJECT_ROOT"
fi

if [ $? -ne 0 ]; then
  echo "Docker build failed. Exiting..."
  exit 1
fi

# Start Docker containers in detached mode
echo "Starting Docker containers in detached mode..."
docker-compose up -d

# Path for the log file (create it in the build directory with a timestamp)
LOG_FILE="$PROJECT_ROOT/build/docker_logs_$(date +"%Y-%m-%d_%H-%M-%S").log"
echo "Logs will be saved to: $LOG_FILE"

# Start Docker containers in detached mode
echo "Starting Docker containers in detached mode..."
docker-compose up -d

### --- 🛠️ MySQL Database Restoration --- ###
echo "Waiting for MySQL to become available..."
until docker exec mysql_db mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "SELECT 1;" &>/dev/null; do
    echo "MySQL is not ready yet. Sleeping for 5 seconds..."
    sleep 5
done
echo "✅ MySQL is up and running."

# Check for table presence instead of entire DB
TABLES_TO_CHECK=("tickets" "ticket_comments" "chat_messages" "custom_fields" "custom_field_values" )  # Add all relevant tables here
RESTORE_NEEDED=false

for table in "${TABLES_TO_CHECK[@]}"; do
    echo "Checking if table '$table' is empty..."
    ROW_COUNT=$(docker exec mysql_db mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -D "${MYSQL_DATABASE}" -N -e "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "0")
    if [[ "$ROW_COUNT" -eq 0 ]]; then
        echo "⚠️ Table '$table' is empty. Restoration needed."
        RESTORE_NEEDED=true
        break
    else
        echo "✅ Table '$table' has data. Skipping restoration."
    fi
done

if [ "$RESTORE_NEEDED" = true ]; then
    echo "⏳ Restoring database from snapshot..."
    SANITIZED_SQL="/tmp/sanitized_snapshot.sql"
    grep -v -i -E 'DROP TABLE|DROP DATABASE|USE `' "$PROJECT_ROOT/test/db_snapshot/db_snapshot.sql" > "$SANITIZED_SQL"

    docker cp "$SANITIZED_SQL" mysql_db:/tmp/sanitized_snapshot.sql
    docker exec mysql_db mysql -u root -p"${MYSQL_ROOT_PASSWORD}" "${MYSQL_DATABASE}" < /tmp/sanitized_snapshot.sql
    echo "✅ Database restoration completed (safely merged)."
else
    echo "✅ All necessary tables contain data. Skipping restoration."
fi

# Print logs to a file immediately after starting, appending with timestamps
echo "Printing logs from Docker containers to $LOG_FILE..."
docker-compose logs -f > "$LOG_FILE" &

# Save the process ID of the logs command so it can be killed when the script ends
LOG_PID=$!

# Ensure logs are captured until the script ends
trap 'kill $LOG_PID 2>/dev/null' EXIT

# Check if the Ollama server is up by hitting the health endpoint
URL="http://localhost:${OLLAMA_PORT}/"
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

# Check if the model was successfully pulled by generating a response
echo "Checking if model is working by generating a response..."
GEN_RESPONSE=$(curl -s -w "%{http_code}" http://localhost:${OLLAMA_PORT}/api/generate -d "{
  \"model\": \"${OLLAMA_MODEL}\",
  \"prompt\": \"What is the capital of France in one sentence?\",
  \"stream\": false
}")
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
# Check if the server is up (replace http://localhost:${CHAT_SERVICE_PORT} with the actual URL if needed)
URL="http://localhost:${CHAT_SERVICE_PORT}"  # Updated URL to localhost
EXPECTED_OUTPUT='{"message":"The server is up and running!"}'
MAX_WAIT_TIME=4300  # 70 minutes
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
