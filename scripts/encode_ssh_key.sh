#!/bin/bash

# Helper script to encode SSH private key for GitHub Secrets
# Usage: ./scripts/encode_ssh_key.sh path/to/your/private_key.pem

if [ -z "$1" ]; then
    echo "Usage: $0 <path-to-private-key>"
    echo "Example: $0 ~/.ssh/deploy_key.pem"
    exit 1
fi

KEY_FILE="$1"

if [ ! -f "$KEY_FILE" ]; then
    echo "Error: File '$KEY_FILE' not found"
    exit 1
fi

echo "Encoding SSH key from: $KEY_FILE"
echo ""
echo "Copy the following base64-encoded key and paste it as the AWS_PRIVATE_KEY secret in GitHub:"
echo "========================================"
base64 -i "$KEY_FILE"
echo "========================================"
echo ""
echo "Steps to add this to GitHub:"
echo "1. Go to your repository on GitHub"
echo "2. Click Settings → Secrets and variables → Actions"
echo "3. Click 'New repository secret' (or update existing AWS_PRIVATE_KEY)"
echo "4. Name: AWS_PRIVATE_KEY"
echo "5. Value: Paste the base64 string above"
echo "6. Click 'Add secret'"
