#!/bin/bash

# Exit immediately on error
set -e

# Get the script directory and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."

export PROJECT_ROOT
echo "PROJECT_ROOT is set to: $PROJECT_ROOT"

# Load environment variables from .env file (unchanged as per your request)
if [ -f "$PROJECT_ROOT/src/backend/.env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' "$PROJECT_ROOT/src/backend/.env" | xargs)

    echo "Exported environment variables:"
    while IFS='=' read -r key value; do
        [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue  # Skip comments and empty lines
        echo "$key=${!key}"  # Print the variable name and its value
    done < <(grep -v '^#' "$PROJECT_ROOT/src/backend/.env" | xargs -n1 echo)

else
    echo ".env file not found in $PROJECT_ROOT/src/backend/. Exiting..."
    exit 1
fi

# Move to the backend directory
cd "$PROJECT_ROOT/src/backend" || exit 1
echo "Changed directory to src/backend"

# Execute get_env_file.sh script
echo "Running get_env_file.sh script..."
"$PROJECT_ROOT/src/frontend/scripts/get_env_file.sh" || { echo "❌ get_env_file.sh failed! Exiting..."; exit 1; }

# Kill any existing servers
"$PROJECT_ROOT/build/kill_server.sh" || { echo "❌ kill_server.sh failed! Exiting..."; exit 1; }

# Build the Docker image
echo "Building Docker image chat_service_image..."
docker build -t chat_service_image:latest -f "${PROJECT_ROOT}/build/chat_service_docker/Dockerfile" "${PROJECT_ROOT}" || { echo "❌ Docker build failed! Exiting..."; exit 1; }

# Start Docker containers
echo "Starting Docker containers..."
docker-compose up -d

# Path for log file
LOG_FILE="$PROJECT_ROOT/build/docker_logs_$(date +"%Y-%m-%d_%H-%M-%S").log"
echo "Logging Docker output to: $LOG_FILE"
docker-compose logs -f > "$LOG_FILE" &

# Capture the logs process ID to kill it on exit
LOG_PID=$!
trap 'kill $LOG_PID 2>/dev/null' EXIT

### --- 🛠️ MySQL Database Restoration --- ###
echo "Waiting for MySQL to become available..."
until docker exec mysql_db mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "SELECT 1;" &>/dev/null; do
    echo "MySQL is not ready yet. Sleeping for 5 seconds..."
    sleep 5
done
echo "✅ MySQL is up and running."

# Check if MySQL has existing data
echo "Checking if MySQL database is empty..."
MYSQL_DATA_COUNT=$(docker exec mysql_db mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -D "${MYSQL_DATABASE}" -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${MYSQL_DATABASE}';" | tail -n 1)

if [ "$MYSQL_DATA_COUNT" -eq 0 ]; then
    echo "⚠️ No data found in MySQL. Restoring database from snapshot..."
    docker exec -i mysql_db mysql -u root -p"${MYSQL_ROOT_PASSWORD}" "${MYSQL_DATABASE}" < "$PROJECT_ROOT/test/db_snapshot/db_snapshot.sql"
    echo "✅ Database restoration complete."
else
    echo "✅ Existing MySQL data found. Skipping restoration."
fi

### --- 🛠️ Check Ollama Server --- ###
URL="http://localhost:${OLLAMA_PORT}/"
MAX_WAIT_TIME=1200  # 20 minutes
CHECK_INTERVAL=5    # 5 seconds
elapsed_time=0

while [ "$elapsed_time" -lt "$MAX_WAIT_TIME" ]; do
    echo "Checking Ollama server status at $URL..."
    RESPONSE=$(curl -s -w "%{http_code}" "$URL")
    HTTP_CODE="${RESPONSE: -3}"

    if [ "$HTTP_CODE" -eq 200 ]; then
        echo "✅ Ollama server is up and running!"
        break
    else
        echo "⏳ Ollama server not up yet. Response code: $HTTP_CODE. Retrying in $CHECK_INTERVAL seconds..."
    fi

    sleep "$CHECK_INTERVAL"
    elapsed_time=$((elapsed_time + CHECK_INTERVAL))
done

if [ "$elapsed_time" -ge "$MAX_WAIT_TIME" ]; then
    echo "❌ Ollama server did not start in time. Exiting..."
    exit 1
fi

# Pull the model (llama3.2:3b)
echo "Pulling the llama3.2:3b model..."
PULL_RESPONSE=$(curl -s -w "%{http_code}" http://localhost:${OLLAMA_PORT}/api/pull -d '{"name": "llama3.2:3b"}')
PULL_HTTP_CODE="${PULL_RESPONSE: -3}"

if [ "$PULL_HTTP_CODE" -eq 200 ]; then
    echo "✅ Model llama3.2:3b pulled successfully."
else
    echo "❌ Failed to pull model. Response code: $PULL_HTTP_CODE"
    exit 1
fi

### --- 🛠️ Check Chat Server --- ###
URL="http://localhost:${CHAT_SERVICE_PORT}"
EXPECTED_OUTPUT='{"message":"The server is up and running!"}'
MAX_WAIT_TIME=4300  # 70 minutes
CHECK_INTERVAL=5    # 5 seconds
elapsed_time=0

while [ "$elapsed_time" -lt "$MAX_WAIT_TIME" ]; do
    echo "Checking Chat Service status at $URL..."
    RESPONSE=$(curl -s "$URL" || echo "curl failed")

    if [ "$RESPONSE" = "$EXPECTED_OUTPUT" ]; then
        echo "✅ Chat Service is up and running!"
        echo "🔗 Server URL: $URL"
        exit 0
    else
        echo "⏳ Chat Service not up yet. Retrying in $CHECK_INTERVAL seconds..."
    fi

    sleep "$CHECK_INTERVAL"
    elapsed_time=$((elapsed_time + CHECK_INTERVAL))
done

echo "❌ Chat Service did not start in time. Check logs at: $LOG_FILE"
exit 1
