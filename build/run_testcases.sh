#!/bin/sh

# Exit on any error
set -e

# Get the directory of the script and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Script directory: $SCRIPT_DIR"
PROJECT_ROOT="$SCRIPT_DIR/.."  # Use the local directory structure

export PROJECT_ROOT
echo "PROJECT_ROOT is set to: $PROJECT_ROOT"

# Load environment variables from .env file
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

# Check if the directory exists
if [ -d "./test/IntegrationTests" ]; then
    py -m unittest discover -s ./test/IntegrationTests || exit 1
else
    echo "No tests found in ./test/IntegrationTests. Skipping test execution..."
fi