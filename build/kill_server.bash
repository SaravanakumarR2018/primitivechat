#!/bin/bash

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

# Move to src/backend directory
cd "$PROJECT_ROOT/src/backend" || exit 1
echo "Bringing Docker down"
docker-compose down
