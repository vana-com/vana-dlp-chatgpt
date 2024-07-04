#!/bin/bash

set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if GPG is installed
if ! command_exists gpg; then
    echo "Error: GPG is not installed on your system."
    echo "Please install GPG and try again."
    echo ""
    echo "Installation instructions:"
    echo "- On macOS (using Homebrew): brew install gnupg"
    echo "- On Ubuntu/Debian: sudo apt-get update && sudo apt-get install gnupg"
    echo "- On other systems, please refer to your package manager or https://gnupg.org"
    exit 1
fi

# Function to prompt for input with a default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local response

    read -p "$prompt [$default]: " response
    echo "${response:-$default}"
}

# Detect operating system
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
else
    echo "Unsupported operating system: $OSTYPE"
    exit 1
fi

# Function to create a temporary directory
create_temp_dir() {
    if [[ "$OS" == "macOS" ]]; then
        mktemp -d -t gpg_temp
    else
        mktemp -d
    fi
}

# Function to base64 encode
base64_encode() {
    if [[ "$OS" == "macOS" ]]; then
        base64 -i "$1" -o "$2"
    else
        base64 -w 0 "$1" > "$2"
    fi
}

# Prompt for user information
NAME=$(prompt_with_default "Enter your name" "Vana DLP Validator")
EMAIL=$(prompt_with_default "Enter your email" "validator@example.com")
EXPIRE=$(prompt_with_default "Enter key expiration in days (0 for no expiration)" "0")

# Create a temporary GPG home directory
GNUPGHOME=$(create_temp_dir)
export GNUPGHOME
trap 'rm -rf "$GNUPGHOME"' EXIT

# Generate GPG key
echo "Generating GPG key..."
gpg --batch --gen-key <<EOF
%echo Generating a basic OpenPGP key
Key-Type: RSA
Key-Length: 3072
Subkey-Type: RSA
Subkey-Length: 3072
Name-Real: $NAME
Name-Email: $EMAIL
Expire-Date: $EXPIRE
%no-protection
%commit
%echo done
EOF

# Export public key
echo "Exporting public key..."
gpg --armor --export "$EMAIL" > public_key.asc

# Export private key
echo "Exporting private key..."
gpg --armor --export-secret-keys "$EMAIL" > private_key.asc

# Check if the files were created and have content
if [ ! -s public_key.asc ]; then
    echo "Error: public_key.asc is empty or was not created."
    exit 1
fi

if [ ! -s private_key.asc ]; then
    echo "Error: private_key.asc is empty or was not created."
    exit 1
fi

# Base64 encode public key
echo "Base64 encoding public key..."
base64_encode public_key.asc public_key_base64.asc

# Base64 encode private key
echo "Base64 encoding private key..."
base64_encode private_key.asc private_key_base64.asc

echo "Done. Keys have been generated and exported."
echo "Public key: public_key.asc"
echo "Private key: private_key.asc"
echo "Base64 encoded public key: public_key_base64.asc"
echo "Base64 encoded private key: private_key_base64.asc"

echo "Please copy the contents of private_key_base64.asc to your .env file under PRIVATE_FILE_ENCRYPTION_PUBLIC_KEY_BASE64"

# Display the contents of public_key.asc
echo "Contents of public_key.asc:"
cat public_key.asc
