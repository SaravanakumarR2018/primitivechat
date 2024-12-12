#!/bin/sh

# Exit on any error
set -e

echo "Running kill_server.sh to bring down all docker containers"
# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Script directory: $SCRIPT_DIR"
PROJECT_ROOT="$SCRIPT_DIR/.."  # Use the local directory structure

echo "Project root: $PROJECT_ROOT"
export PROJECT_ROOT
echo "PROJECT_ROOT is set to: $PROJECT_ROOT"

# Load environment variables from .env file
if [ -f "$PROJECT_ROOT/src/backend/.env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' "$PROJECT_ROOT/src/backend/.env" | xargs)
else
    echo ".env file not found in $PROJECT_ROOT/src/backend/. Exiting..."
    exit 1
fi

# Move to src/backend directory
cd "$PROJECT_ROOT/src/backend" || exit 1
echo "Bringing Docker down"
docker-compose down