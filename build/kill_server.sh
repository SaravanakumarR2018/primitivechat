#!/bin/bash

# Exit on any error
set -e

# Get the directory of the script and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Script directory: $SCRIPT_DIR"
PROJECT_ROOT="$SCRIPT_DIR/.."
echo "Project root: $PROJECT_ROOT"
cd $PROJECT_ROOT/src/backend
echo "Bringing docker down"
docker-compose down
