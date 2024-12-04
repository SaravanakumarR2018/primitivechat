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

# Set fallback values for critical environment variables
export CHAT_SERVICE_PORT=${CHAT_SERVICE_PORT:-8000}
export DB_USER=${DB_USER:-root}
export DB_PASSWORD=${DB_PASSWORD:-admin123}
export DB_HOST=${DB_HOST:-mysql_db}
export MYSQL_DATABASE=${MYSQL_DATABASE:-mydatabase}
export MYSQL_PORT=${MYSQL_PORT:-3306}
export MINIO_ROOT_USER=${MINIO_ROOT_USER:-minioadmin}
export MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD:-minioadmin}
export MINIO_CONSOLE_PORT=${MINIO_CONSOLE_PORT:-9001}
export MINIO_SERVER_PORT=${MINIO_SERVER_PORT:-9000}
export WEAVIATE_PORT=${WEAVIATE_PORT:-8080}
export WEAVIATE_GRPC_PORT=${WEAVIATE_GRPC_PORT:-50051}
export OLLAMA_PORT=${OLLAMA_PORT:-11434}

# Display the loaded environment variables (optional, for debugging)
echo "Loaded environment variables:"
echo "CHAT_SERVICE_PORT=$CHAT_SERVICE_PORT"
echo "DB_USER=$DB_USER"
echo "DB_PASSWORD=$DB_PASSWORD"
echo "DB_HOST=$DB_HOST"
echo "MYSQL_DATABASE=$MYSQL_DATABASE"
echo "MYSQL_PORT=$MYSQL_PORT"
echo "MINIO_ROOT_USER=$MINIO_ROOT_USER"
echo "MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD"
echo "MINIO_CONSOLE_PORT=$MINIO_CONSOLE_PORT"
echo "MINIO_SERVER_PORT=$MINIO_SERVER_PORT"
echo "WEAVIATE_PORT=$WEAVIATE_PORT"
echo "WEAVIATE_GRPC_PORT=$WEAVIATE_GRPC_PORT"
echo "OLLAMA_PORT=$OLLAMA_PORT"

# Move to src/backend directory
cd "$PROJECT_ROOT/src/backend" || exit 1
echo "Bringing Docker down"
docker-compose down

# Pull required images
echo "Pulling required Docker images..."
docker-compose pull mysql_db
docker-compose pull minio
docker-compose pull ollama

# Pull weaviate image with retry
echo "Pulling weaviate image..."
for i in {1..5}; do
  docker-compose pull weaviate
  if [ $? -eq 0 ]; then
    break
  fi
  echo "Pull failed, retrying in 10 seconds..."
  sleep 10
done

echo "All required Docker images pulled successfully."