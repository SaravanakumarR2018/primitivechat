#!/bin/bash

# Detect OS
OS="$(uname)"

# Function to find the Git root directory
find_git_root() {
  dir=$(pwd)
  while [ "$dir" != "/" ] && [ "$dir" != "" ]; do
    if [ -d "$dir/.git" ]; then
      echo "$dir"
      return
    fi
    dir=$(dirname "$dir")
  done
  echo "" # Return empty if not found
}

# Function to store credentials securely
store_credentials() {
  echo "🔑 Enter your GitHub username:"
  read -r GITHUB_USER
  echo "🔑 Enter your GitHub PAT (Personal Access Token):"
  stty -echo   # Disable terminal echo
  read -r GITHUB_PAT
  stty echo    # Re-enable terminal echo
  echo         # Print a newline to maintain formatting
  

  if [ "$OS" = "Darwin" ] || [ "$OS" = "Linux" ]; then
    CREDENTIALS_FILE="$HOME/.github_credentials"
  else
    CREDENTIALS_FILE="$USERPROFILE/.github_credentials"
  fi

  echo "GITHUB_USER=$GITHUB_USER" > "$CREDENTIALS_FILE"
  echo "GITHUB_PAT=$GITHUB_PAT" >> "$CREDENTIALS_FILE"
  

  chmod 600 "$CREDENTIALS_FILE"
  echo "✅ Credentials saved securely!"
}

# Function to load stored credentials
load_credentials() {
  if [ "$OS" = "Darwin" ] || [ "$OS" = "Linux" ]; then
    CREDENTIALS_FILE="$HOME/.github_credentials"
  else
    CREDENTIALS_FILE="$USERPROFILE/.github_credentials"
  fi

  if [ -f "$CREDENTIALS_FILE" ]; then
    . "$CREDENTIALS_FILE"
  else
    store_credentials
  fi
}

# Function to copy .env.local from private repo
copy_env_file() {
  ENV_REPO="https://$GITHUB_USER:$GITHUB_PAT@github.com/SaravanakumarR2018/primitivechatenv.git"
  if [ "$OS" = "Linux" ] || [ "$OS" = "Darwin" ]; then
    TEMP_DIR=$(mktemp -d)
  else
    TEMP_DIR=$(mktemp -d 2>/dev/null || echo "$USERPROFILE\\AppData\\Local\\Temp\\env_clone")
    mkdir -p "$TEMP_DIR"
  fi

  echo "🔄 Cloning private env repo..."
  if git clone --depth 1 "$ENV_REPO" "$TEMP_DIR"; then
    mv "$TEMP_DIR/.env.local" "$FRONTEND_DIR/.env.local"
    echo "✅ .env.local copied to $FRONTEND_DIR"
    rm -rf "$TEMP_DIR"
  else
    echo "❌ Authentication failed. Please check your GitHub username or PAT."
    echo "🔍 Try searching 'GitHub authentication issues' in ChatGPT for help."
    echo "🗑️ Deleting stored credentials to prompt re-authentication next time."
    rm -f "$CREDENTIALS_FILE"
    exit 1
  fi
}

append_env_file() {
    SOURCE_FILE="$GIT_ROOT/src/backend/.env"
    TARGET_FILE="$GIT_ROOT/src/frontend/.env.local"

    if [ ! -f "$SOURCE_FILE" ]; then
        echo "Error: Source file does not exist: $SOURCE_FILE"
        exit 1
    fi

    echo "Processing variables from $SOURCE_FILE..."

    while IFS='=' read -r key value; do
        # Skip empty lines or lines without a key
        if [ -z "$key" ] || [[ "$key" =~ ^# ]]; then
            continue
        fi

        # Remove trailing spaces
        key=$(echo "$key" | tr -d ' ')
        value=$(echo "$value" | tr -d ' ')

        # Ensure the key is not empty before appending
        if [ -n "$key" ]; then
            if grep -q "^$key=" "$TARGET_FILE"; then
                if grep -q "^$key=$value$" "$TARGET_FILE"; then
                    echo "No modification required: $key"
                else
                    echo "Modified variable: $key"
                    sed -i "s|^$key=.*|$key=$value|" "$TARGET_FILE"
                fi
            else
                echo "Newly added variable: $key"
                echo "$key=$value" >> "$TARGET_FILE"
            fi
        fi
    done < "$SOURCE_FILE"

    if [ $? -eq 0 ]; then
        echo "Success: Copied from $SOURCE_FILE to $TARGET_FILE"
    else
        echo "Error: Failed to copy from $SOURCE_FILE to $TARGET_FILE"
        exit 1
    fi
}

### 🚀 Main Execution ###
GIT_ROOT=$(find_git_root)
if [ -z "$GIT_ROOT" ]; then
  echo "❌ Error: Not inside a Git repository. Run this script inside your project folder."
  exit 1
fi

FRONTEND_DIR="$GIT_ROOT/src/frontend"
if [ ! -d "$FRONTEND_DIR" ]; then
  echo "❌ Error: 'src/frontend' directory not found in the Git root."
  exit 1
fi
echo "GIT_ROOT: $GIT_ROOT"
echo "FRONTEND_DIR: $FRONTEND_DIR"
echo "$HOME/.github_credentials"
load_credentials
copy_env_file
append_env_file

