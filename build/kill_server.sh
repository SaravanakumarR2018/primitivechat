#!/bin/sh

# Exit on any error
set -e

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Script directory: $SCRIPT_DIR"

# Determine the PROJECT_ROOT based on the environment
if [ "${GITHUB_ACTIONS}" = "true" ]; then
    PROJECT_ROOT="${GITHUB_WORKSPACE}"  # Use the GitHub workspace in GitHub Actions
else
    PROJECT_ROOT="$SCRIPT_DIR/.."  # Use the local directory structure
fi

echo "Project root: $PROJECT_ROOT"
export PROJECT_ROOT
echo "PROJECT_ROOT is set to: $PROJECT_ROOT"

# Move to src/backend directory
cd "$PROJECT_ROOT/src/backend" || exit 1
echo "Bringing Docker down"
docker-compose down
