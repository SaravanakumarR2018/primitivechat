#!/bin/sh

# Exit on any error
set -e

# Get the directory of the script and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Script directory: $SCRIPT_DIR"
PROJECT_ROOT="$SCRIPT_DIR/.."  # Use the local directory structure

export PROJECT_ROOT
echo "PROJECT_ROOT is set to: $PROJECT_ROOT"

# Run tests in Docker container
docker run --rm \
    --add-host=host.docker.internal:host-gateway \
    -v "$PROJECT_ROOT:/app" \
    -w /app \
    --env-file "$PROJECT_ROOT/src/backend/.env" \
    python:3.9-slim sh -c "
    set -e
    pip install requests

    # Create a temporary directory for test files
    echo 'Copying test files into a temporary directory...'
    mkdir -p /tmp/test_copy
    cp -r ./test/IntegrationTests /tmp/test_copy/

    # Replace localhost with host.docker.internal in the copied files
    echo 'Modifying copied test files...'
    find /tmp/test_copy -type f -name '*.py' -exec sed -i 's|http://localhost|http://host.docker.internal|g' {} +
   

    # Run tests from the copied directory
    echo 'Running tests...'
    python -m unittest discover -s /tmp/test_copy/IntegrationTests  -p "test_*.py"
"

