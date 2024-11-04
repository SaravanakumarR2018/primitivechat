#!/bin/sh

# Exit on any error
set -e

# Get the directory of the script and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Script directory: $SCRIPT_DIR"

# Initialize PROJECT_ROOT and TEMP_DIR for GitHub Actions
if [ "${GITHUB_ACTIONS}" = "true" ]; then
 # Print GitHub environment variables
    export PR_BRANCH="${GITHUB_HEAD_REF}"
    export COMMIT_SHA="${GITHUB_SHA}"
    export GITHUB_REPOSITORY="${GITHUB_REPOSITORY}"
    export PROJECT_ROOT="${GITHUB_WORKSPACE}"
    export PR_NUMBER="${PR_NUMBER}"


    echo "GitHub environment variables:"
    echo " PR_BRANCH = $PR_BRANCH"
    echo " COMMIT_SHA = $COMMIT_SHA"
    echo " GITHUB_REPOSITORY = $GITHUB_REPOSITORY"
    echo " GITHUB_WORKSPACE = $GITHUB_WORKSPACE"
    echo " PR_NUMBER = $PR_NUMBER"

    # Define the command with variables expanded
    GIT_COMMAND="apt-get update && \
    apt-get install -y git && \
    cd /app && \
    git clone https://github.com/${GITHUB_REPOSITORY}.git && \
    cd primitivechat && \
    git fetch origin pull/${PR_NUMBER}/head:${PR_BRANCH} && \
    git checkout ${PR_BRANCH} && \
    cp -R /app/primitivechat/* /app && \
    cd /app"

    # Output the command for verification
    echo "GIT_COMMAND is set to: $GIT_COMMAND"
    # Move to the backend directory
    cd "$PROJECT_ROOT/src/backend" || exit 1
    # Run sed command to replace placeholder in docker-compose.yml
    echo "First docker-compose.yml contents:"
    cat docker-compose.yml
    GIT_COMMAND_ESCAPED=$(echo "$GIT_COMMAND" | sed 's/&/\\&/g')
    echo "GIT_COMMAND_ESCAPED is set to: $GIT_COMMAND_ESCAPED"
    sed -i "s|pwd|${GIT_COMMAND_ESCAPED}|g" docker-compose.yml
    echo "Modified docker-compose.yml contents:"
    cat docker-compose.yml

else
    PROJECT_ROOT="$SCRIPT_DIR/.."  # Use the local directory structure
fi

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
