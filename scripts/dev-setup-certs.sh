#!/usr/bin/env bash
#
# Development Certificate Setup Helper
#
# This script helps set up certificates for local development without requiring root access.
# It exports CERT_DIR=./certs and initializes the certificate directory.
#
# Usage:
#   source scripts/dev-setup-certs.sh    # Sets CERT_DIR for current shell
#   ./scripts/dev-setup-certs.sh         # Just creates ./certs directory
#

# Only set strict mode if running as script (not sourced)
# This prevents polluting the caller's shell environment
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    set -euo pipefail
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEV_CERT_DIR="$HOME/.crank/certs"

echo "🔐 Crank Platform - Development Certificate Setup"
echo ""
echo "Production default: /etc/certs (requires root or Docker mounts)"
echo "Development default: CERT_DIR=$DEV_CERT_DIR (user-writable)"
echo ""

# Create development cert directory
if [ ! -d "$DEV_CERT_DIR" ]; then
    echo "📁 Creating development certificate directory: $DEV_CERT_DIR"
    mkdir -p "$DEV_CERT_DIR"
else
    echo "✅ Development certificate directory exists: $DEV_CERT_DIR"
fi

# Export CERT_DIR for development
export CERT_DIR="$DEV_CERT_DIR"

echo ""
echo "To use development certificates in your shell, run:"
echo "  export CERT_DIR=$DEV_CERT_DIR"
echo ""
echo "Or source this script:"
echo "  source scripts/dev-setup-certs.sh"
echo ""
echo "Then run certificate initialization:"
echo "  python scripts/initialize-certificates.py"
echo ""

# If sourced, the export will persist in the calling shell
# If executed, it only prints instructions
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    echo "⚠️  Note: Script was executed (not sourced), so CERT_DIR is not exported."
    echo "   Run: source scripts/dev-setup-certs.sh"
fi
