#!/bin/bash

# 🚢 Port Configuration Test Script
# Tests the new environment-based port allocation

set -e

echo "🚢 Crank Platform - Port Configuration Test"
echo "============================================="

# Copy environment template if .env doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env from template..."
    cp .env.template .env
    echo "✅ Created .env file with default ports"
else
    echo "📋 Using existing .env file"
fi

# Show current port allocation
echo ""
echo "🔍 Current Port Allocation:"
echo "├── Platform:           ${PLATFORM_PORT:-8000} (HTTP), ${PLATFORM_HTTPS_PORT:-8443} (HTTPS)"
echo "├── Doc Converter:      ${DOC_CONVERTER_PORT:-8100} (HTTP), ${DOC_CONVERTER_HTTPS_PORT:-8101} (HTTPS)"
echo "├── Email Classifier:   ${EMAIL_CLASSIFIER_PORT:-8200} (HTTP), ${EMAIL_CLASSIFIER_HTTPS_PORT:-8201} (HTTPS)"
echo "├── Email Parser:       ${EMAIL_PARSER_PORT:-8300} (HTTP), ${EMAIL_PARSER_HTTPS_PORT:-8301} (HTTPS)"
echo "├── Image Classifier:   ${IMAGE_CLASSIFIER_PORT:-8400} (HTTP), ${IMAGE_CLASSIFIER_HTTPS_PORT:-8401} (HTTPS)"
echo "└── Streaming Service:  ${STREAMING_PORT:-8500} (HTTP)"

# Check for port conflicts
echo ""
echo "🔍 Checking for Port Conflicts..."

# Function to check if port is in use
check_port() {
    local port=$1
    local service=$2
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        echo "⚠️  WARNING: Port $port ($service) is already in use!"
        return 1
    else
        echo "✅ Port $port ($service) is available"
        return 0
    fi
}

# Check all default ports
conflicts=0
check_port "${PLATFORM_PORT:-8000}" "Platform HTTP" || ((conflicts++))
check_port "${PLATFORM_HTTPS_PORT:-8443}" "Platform HTTPS" || ((conflicts++))
check_port "${DOC_CONVERTER_PORT:-8100}" "Doc Converter" || ((conflicts++))
check_port "${EMAIL_CLASSIFIER_PORT:-8200}" "Email Classifier" || ((conflicts++))
check_port "${EMAIL_PARSER_PORT:-8300}" "Email Parser" || ((conflicts++))
check_port "${IMAGE_CLASSIFIER_PORT:-8400}" "Image Classifier" || ((conflicts++))
check_port "${STREAMING_PORT:-8500}" "Streaming Service" || ((conflicts++))

if [ $conflicts -eq 0 ]; then
    echo ""
    echo "🎉 No port conflicts detected! Ready to deploy."
else
    echo ""
    echo "🚨 Found $conflicts port conflicts. Please update .env file."
    echo "💡 TIP: Use different ports or stop conflicting services."
fi

# Test Docker Compose validation
echo ""
echo "🐳 Testing Docker Compose Configuration..."
if docker-compose -f docker-compose.multi-worker.yml config >/dev/null 2>&1; then
    echo "✅ Docker Compose configuration is valid"
else
    echo "❌ Docker Compose configuration has errors"
    echo "🔍 Running validation with details..."
    docker-compose -f docker-compose.multi-worker.yml config
    exit 1
fi

# Show next steps
echo ""
echo "🚀 Next Steps:"
echo "1. Review/edit .env file if needed:     nano .env"
echo "2. Start services:                      docker-compose -f docker-compose.multi-worker.yml up"
echo "3. Test with custom ports:              EMAIL_CLASSIFIER_PORT=8287 docker-compose up"
echo "4. Check service health:                curl http://localhost:\${PLATFORM_PORT:-8000}/health"

echo ""
echo "🎯 Port Configuration Test Complete!"

# Optional: Show which services would start with current config
echo ""
echo "📋 Services that would start:"
echo "Platform:         http://localhost:${PLATFORM_PORT:-8000}"
echo "Doc Converter:    http://localhost:${DOC_CONVERTER_PORT:-8100}"  
echo "Email Classifier: http://localhost:${EMAIL_CLASSIFIER_PORT:-8200}"
echo "Email Parser:     http://localhost:${EMAIL_PARSER_PORT:-8300}"
echo "Image Classifier: http://localhost:${IMAGE_CLASSIFIER_PORT:-8400}"
echo "Streaming:        http://localhost:${STREAMING_PORT:-8500}"