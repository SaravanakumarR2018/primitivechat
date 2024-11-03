#!/bin/sh

# Exit on any error
set -e

# Get the directory of the script and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Script directory: $SCRIPT_DIR"

# Initialize PROJECT_ROOT and TEMP_DIR for GitHub Actions
if [ "${GITHUB_ACTIONS}" = "true" ]; then
    PROJECT_ROOT="${GITHUB_WORKSPACE}"  # Use the GitHub workspace in GitHub Actions
    TEMP_DIR="$(pwd)/temp_src"           # Define the temporary directory
    mkdir -p "$TEMP_DIR"                  # Create the temporary directory
    cp -r "$PROJECT_ROOT/src/"* "$TEMP_DIR"  # Copy src files to the temporary directory
    echo "List the temp directory files"
    find "$TEMP_DIR"
    # Update docker-compose.yml to use TEMP_DIR instead of PROJECT_ROOT
    echo "Updating docker-compose.yml to use temporary directory..."
    sed -i "s|${PROJECT_ROOT}/src|$TEMP_DIR|g" "$PROJECT_ROOT/docker-compose.yml"
    echo "Updated docker-compose.yml:"
    cat "$PROJECT_ROOT/docker-compose.yml"
else
    PROJECT_ROOT="$SCRIPT_DIR/.."  # Use the local directory structure
fi

echo "Project root: $PROJECT_ROOT"
export PROJECT_ROOT
echo "PROJECT_ROOT is set to: $PROJECT_ROOT"

LOG_DIR="$PROJECT_ROOT/log/backend"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/backend_log_${TIMESTAMP}.log"
echo "Log file will be created at: $LOG_FILE"

# Move to the backend directory
cd "$PROJECT_ROOT/src/backend" || exit 1
echo "Changed directory to src/backend"

# Ensure log directory exists
mkdir -p "$LOG_DIR" && echo "Ensured log directory exists at: $LOG_DIR"

# Start Docker containers in detached mode
echo "Starting Docker containers in detached mode..."
docker-compose up -d

# Capture logs in the background
echo "Capturing logs in log file $LOG_FILE"
touch "$LOG_FILE"
docker-compose logs -f >> "$LOG_FILE" &

echo "Capturing new logs for 30 seconds..."
tail -n 100000 -f "$LOG_FILE" &
TAIL_PID=$!

sleep 30
echo "Stopping log printing after 30 seconds..."
kill "$TAIL_PID"

echo "Initial logs captured. For additional logs, check the log file: $LOG_FILE"
