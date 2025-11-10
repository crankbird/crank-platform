#!/bin/bash
# Generate test certificate fixtures using mkcert
# Purpose: Create valid and invalid certificate bundles for CertificateBundle testing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALID_DIR="$SCRIPT_DIR/valid"
INVALID_DIR="$SCRIPT_DIR/invalid"

echo "🔐 Generating certificate test fixtures..."

# Create directories
mkdir -p "$VALID_DIR"
mkdir -p "$INVALID_DIR"

# Check for mkcert
if ! command -v mkcert &> /dev/null; then
    echo "⚠️  mkcert not found. Installing via homebrew..."
    brew install mkcert
fi

# Generate valid certificates
cd "$VALID_DIR"

echo "📜 Creating CA certificate..."
mkcert -cert-file ca.crt -key-file ca.key "CrankPlatformTestCA"

echo "📜 Creating platform certificate..."
mkcert -cert-file platform.crt -key-file platform.key "localhost" "127.0.0.1" "::1" "*.crank.local"

echo "📜 Creating client certificate..."
mkcert -cert-file client.crt -key-file client.key "test-client"

# Generate invalid/malformed certificates
cd "$INVALID_DIR"

echo "🔥 Creating truncated certificate..."
head -n 5 "$VALID_DIR/platform.crt" > truncated-cert.pem

echo "🔥 Creating corrupted key..."
{
    echo "-----BEGIN PRIVATE KEY-----"
    echo "CORRUPTED_DATA_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    echo "MORE_CORRUPTED_DATA_YYYYYYYYYYYYYYYYYYYYYYYYYYYYYY"
    echo "-----END PRIVATE KEY-----"
} > corrupted-key.pem

echo "🔥 Creating wrong format file..."
echo "This is not a PEM file at all!" > wrong-format.txt

echo "🔥 Creating missing header file..."
{
    echo "MIIDXTCCAkWgAwIBAgIUXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    echo "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    echo "-----END CERTIFICATE-----"
} > missing-header.pem

echo "🔥 Creating empty PEM file..."
{
    echo "-----BEGIN CERTIFICATE-----"
    echo "-----END CERTIFICATE-----"
} > empty-cert.pem

# Set permissions
chmod 644 "$VALID_DIR"/*.crt
chmod 600 "$VALID_DIR"/*.key
chmod 644 "$INVALID_DIR"/*

echo "✅ Certificate fixtures generated successfully!"
echo ""
echo "Valid certificates:"
ls -lh "$VALID_DIR"
echo ""
echo "Invalid certificates:"
ls -lh "$INVALID_DIR"
