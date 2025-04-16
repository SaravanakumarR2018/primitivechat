#!/bin/bash

# Get the Git root directory
GIT_ROOT_DIR=$(git rev-parse --show-toplevel)

# Change to the Git root directory
cd "$GIT_ROOT_DIR"

# Get the directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

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
done  # Removed the 'shift' here

# Check if ORG_ID is provided
if [ -z "$ORG_ID" ]; then
    echo "Error: Organization ID is required."
    display_help
    exit 1
fi

# Check if ORG_ROLE is valid
if [[ ! " org:admin org:member org:user org:super_admin " =~ " $ORG_ROLE " ]]; then
    echo "Error: Invalid organization role."
    display_help
    exit 1
fi

# Always build the Docker image
echo "Building the Docker image..."
docker build -t generate-token-image -f build/generate_token/Dockerfile .

# Run the Docker container to generate the token
docker run --rm -e ORG_ID="$ORG_ID" -e ORG_ROLE="$ORG_ROLE" -v "$GIT_ROOT_DIR":/app -w /app generate-token-image python -c "import sys; from test.IntegrationTests.utils.api_utils import create_test_token; print(create_test_token(sys.argv[1], sys.argv[2]))" "$ORG_ID" "$ORG_ROLE" 