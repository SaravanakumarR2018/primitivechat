#!/bin/sh

# Exit on any error
set -e

# Get the directory of the script and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Script directory: $SCRIPT_DIR"
PROJECT_ROOT="$SCRIPT_DIR/.."
echo "Project root: $PROJECT_ROOT"
LOG_DIR="$PROJECT_ROOT/log/backend"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/backend_log_${TIMESTAMP}.log"
echo "Log file will be created at: $LOG_FILE"

# Move to src/backend directory
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
echo "To bring down the Docker containers, run the following command:"
echo "cd $PROJECT_ROOT/src/backend; docker-compose down;"
