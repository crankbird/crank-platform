#!/bin/bash
# 🚀 Confidence Test Runner
# ========================
# 
# Runs comprehensive validation of the HTTPS-only containerized platform
#

set -e

echo "🚀 Crank Platform - Confidence Test Runner"
echo "=========================================="

# Check if httpx is installed
echo "📦 Checking dependencies..."
if ! python3 -c "import httpx" 2>/dev/null; then
    echo "⚠️  Missing httpx dependency. Installing..."
    pip install httpx
fi

echo "✅ Dependencies ready"
echo ""

# Check if services are running
echo "🔍 Checking service status..."
if ! docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "crank.*healthy"; then
    echo "⚠️  Services don't appear to be running. Starting them..."
    docker-compose -f docker-compose.development.yml up -d
    echo "⏳ Waiting for services to become healthy..."
    sleep 30
fi

echo "✅ Services appear to be running"
echo ""

# Run the confidence test suite
echo "🧪 Running Confidence Test Suite..."
echo "======================================"
python3 tests/confidence_test_suite.py

echo ""
echo "🎯 Test run complete!"