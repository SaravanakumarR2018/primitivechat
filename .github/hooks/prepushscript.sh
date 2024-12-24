#!/bin/bash

# Get the directory of the script and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."  # Adjust this based on your directory structure

# Change to the project root directory
cd "$PROJECT_ROOT" || exit 1

echo "Starting pre-push checks..."

# Start the server
echo "Running server..."
"$PROJECT_ROOT/build/run_server.sh"
if [ $? -ne 0 ]; then
    echo "Error: Failed to start the server. Aborting push."
    exit 1
fi

# Run test cases
echo "Running test cases..."
"$PROJECT_ROOT/build/run_testcases.sh"
if [ $? -ne 0 ]; then
    echo "Error: Test cases failed. Killing server and aborting push."
    "$PROJECT_ROOT/build/kill_server.sh"
    exit 1
fi

# Stop the server
echo "Stopping server..."
"$PROJECT_ROOT/build/kill_server.sh"
if [ $? -ne 0 ]; then
    echo "Warning: Failed to kill the server. Please stop it manually."
    exit 1
fi

echo "All pre-push checks passed. Proceeding with push."
exit 0