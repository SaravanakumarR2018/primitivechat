#!/bin/bash

# Exit on any error
set -e

# Function to kill a process and wait for it to restart
restart_process() {
    local container_name=$1
    local process_name=$2

    echo "🔄 Restarting process: $process_name in container: $container_name"

    # Get the process ID of the process before restart
    ATTEMPTS=0
    MAX_ATTEMPTS=10
    while true; do
        PROCESS_INFO_BEFORE=$(docker exec "$container_name" ps -eo pid,etime,start,comm,cmd | grep "$process_name" || true)
        if [ -n "$PROCESS_INFO_BEFORE" ]; then
            break
        fi
        ATTEMPTS=$((ATTEMPTS + 1))
        if [ "$ATTEMPTS" -ge "$MAX_ATTEMPTS" ]; then
            echo -e "\033[31m❌ Process $process_name not found after 20 seconds. Exiting. (Line $LINENO)\033[0m"
            exit 1
        fi
        echo "⚠️ Process info is empty. Retrying in 2 seconds... (Line $LINENO)"
        sleep 2
    done
    if [ -n "$PROCESS_INFO_BEFORE" ]; then
        PID_BEFORE=$(echo "$PROCESS_INFO_BEFORE" | awk '{print $1}')
        echo "🆔 Process ID of $process_name before restart: $PID_BEFORE"
    else
        echo "⚠️ $process_name is not running before restart."
    fi

    # Kill the process
    docker exec "$container_name" pkill -9 -f "$process_name" || echo -e "\033[31m⚠️ Process $process_name not running. Skipping kill step. (Line $LINENO)\033[0m"

    # Wait for the process to restart
    echo "⏳ Waiting for $process_name to restart..."
    ATTEMPTS=0
    MAX_ATTEMPTS=10
    while true; do
        echo "🔍 Checking process info for $process_name..."
        PROCESS_INFO=$(docker exec "$container_name" ps -eo pid,etime,start,comm,cmd | grep "$process_name" || true)
        if [ -n "$PROCESS_INFO" ]; then
            PID_AFTER=$(echo "$PROCESS_INFO" | awk '{print $1}')
            echo "🆔 Process ID of $process_name after restart: $PID_AFTER"
            if [ "$PID_AFTER" != "$PID_BEFORE" ]; then
                echo "✅ $process_name has restarted with a new process ID."
                echo "🎉 Restart of $process_name was successful."
                break
            else
                echo -e "\033[31m❌ Process ID is still the same after restart. Restart failed. (Line $LINENO)\033[0m"
                echo -e "\033[31m\033[1mFAIL\033[0m"
                exit 1
            fi
        else
            echo "⚠️ Process info is empty. Retrying in 2 seconds... (Line $LINENO)"
        fi

        ATTEMPTS=$((ATTEMPTS + 1))
        if [ "$ATTEMPTS" -ge "$MAX_ATTEMPTS" ]; then
            echo -e "\033[31m❌ Process $process_name failed to restart after 20 seconds. Exiting. (Line $LINENO)\033[0m"
            echo -e "\033[31m\033[1mFAIL\033[0m"
            exit 1
        fi
        sleep 2
    done

    echo "✅ Successfully restarted $process_name process."
}

# Function to display help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --restart-chat_service     Restart the chat_service process." # Updated option
    echo "  --restart-filevectorizer   Restart the file_vectorizer process."
    echo "  -h, --help                 Display this help message."
    exit 0
}

# Main script
CONTAINER_NAME="chat_service"
RESTART_CHAT_SERVICE=false # Updated variable name
RESTART_FILEVECTORIZER=false

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --restart-chat_service) RESTART_CHAT_SERVICE=true ;; # Updated variable name
        --restart-filevectorizer) RESTART_FILEVECTORIZER=true ;;
        -h|--help) show_help ;;
        *) echo "❌ Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Restart chat_service process if specified
if [ "$RESTART_CHAT_SERVICE" = true ]; then # Updated variable name
    restart_process "$CONTAINER_NAME" "uvicorn"
fi

# Restart file_vectorizer process if specified
if [ "$RESTART_FILEVECTORIZER" = true ]; then
    restart_process "$CONTAINER_NAME" "file_vectorizer_main"
fi

# If no arguments are passed, restart chat_service by default
if [ "$RESTART_CHAT_SERVICE" = false ] && [ "$RESTART_FILEVECTORIZER" = false ]; then # Updated variable name
    restart_process "$CONTAINER_NAME" "uvicorn"
fi

echo "🎉 ✅ Fastload script completed successfully."
