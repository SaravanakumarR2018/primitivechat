#!/bin/bash

# Default values
ORG_ID="org_2wxyzABCdEfGHIjkLmnotw"
ORG_ROLE="org:admin"

# Function to display help
function display_help() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -i, --org-id      Organization ID (required)"
    echo "  -r, --org-role    Organization role (default: org:admin)"
    echo "  -h, --help        Display this help message"
}

# Parse CLI arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -i|--org-id)
            ORG_ID="$2"
            shift 2
            ;;
        -r|--org-role)
            ORG_ROLE="$2"
            shift 2
            ;;
        -h|--help)
            display_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            display_help
            exit 1
            ;;
    esac
done

# Validate ORG_ID
if [ -z "$ORG_ID" ]; then
    echo "Error: Organization ID is required."
    display_help
    exit 1
fi

# Validate ORG_ROLE
if [[ ! " org:admin org:member org:user org:super_admin " =~ " $ORG_ROLE " ]]; then
    echo "Error: Invalid organization role."
    display_help
    exit 1
fi

# Resolve script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Try to get Git root directory
GIT_ROOT_DIR=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null)
if [ -z "$GIT_ROOT_DIR" ]; then
    echo "Error: Could not determine Git root. Make sure this script is inside a Git repo."
    exit 1
fi

echo "Building the Docker image..."
docker build -t generate-token-image -f "$SCRIPT_DIR/Dockerfile" "$SCRIPT_DIR"
if [ $? -ne 0 ]; then
    echo "Docker build failed."
    exit 1
fi

echo "Running Docker container to generate token..."
docker run --rm \
    -e ORG_ID="$ORG_ID" \
    -e ORG_ROLE="$ORG_ROLE" \
    -v "$GIT_ROOT_DIR":/app \
    -w /app \
    generate-token-image \
    python -c "import sys; from test.IntegrationTests.utils.api_utils import create_test_token; print(create_test_token(sys.argv[1], sys.argv[2]))" "$ORG_ID" "$ORG_ROLE"

