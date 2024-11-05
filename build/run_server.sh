#!/bin/sh

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

# Start Docker containers in detached mode
echo "Starting Docker containers in detached mode..."
docker-compose up -d

## Print logs to console immediately after starting
echo "Printing logs from Docker containers:"
docker-compose logs -f &
LOG_PID=$!

trap 'kill $LOG_PID 2>/dev/null' EXIT
# Check if the server is up (replace http://localhost:8000 with the actual URL if needed)
URL="http://localhost:8000"  # Updated URL to localhost
EXPECTED_OUTPUT='{"message":"The server is up and running!"}'
MAX_WAIT_TIME=120  # 2 minutes
CHECK_INTERVAL=5    # 5 seconds
elapsed_time=0

while [ "$elapsed_time" -lt "$MAX_WAIT_TIME" ]; do
    echo "Checking server status at $URL..."

    # Capture the response from curl
    RESPONSE=$(curl -s "$URL" || echo "curl failed")

    # Check if the response matches the expected output
    if [ "$RESPONSE" = "$EXPECTED_OUTPUT" ]; then
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

echo "Server did not come up within the expected time. Exiting..."
exit 1
