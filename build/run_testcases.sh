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

    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        case "$key" in
            \#*|"") continue ;;
        esac

        # Trim whitespace from key and value
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)

        # Check if the key is not empty
        if [[ -n "$key" ]]; then
            # Strip quotes around the value if present
            value=$(echo "$value" | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/")
            export "$key=$value"
        else
            echo "Skipping invalid line: $key=$value"
        fi
    done < "$PROJECT_ROOT/src/backend/.env"

    echo "Exported environment variables:"
    while IFS='=' read -r key value; do
        case "$key" in
            \#*|"") continue ;;
        esac
        echo "$key=$(eval echo \$$key)"  # Print variable name and its value
    done < "$PROJECT_ROOT/src/backend/.env"
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