#!/bin/bash
# Deploy AI/ML containers to Mac Docker Desktop from WSL control plane

set -euo pipefail

# Configuration
DOCKER_HOST_MAC="ssh://user@mac-host"  # Configure your Mac connection
COMPOSE_FILE="docker-compose.mac.yml"
SERVICE_NAME="aiml-dev"
METAL_ENABLED=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --metal)
            METAL_ENABLED=true
            shift
            ;;
        --service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --mac-host)
            DOCKER_HOST_MAC="ssh://$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🍎 Deploying to Mac Docker Desktop..."
echo "Service: $SERVICE_NAME"
echo "Metal GPU: $METAL_ENABLED"
echo "Mac Host: $DOCKER_HOST_MAC"

# Check if Mac Docker is accessible
if ! docker -H "$DOCKER_HOST_MAC" version >/dev/null 2>&1; then
    echo "❌ Cannot connect to Mac Docker Desktop"
    echo "Please configure SSH access to Mac or update --mac-host"
    exit 1
fi

# Set Docker context to Mac
export DOCKER_HOST="$DOCKER_HOST_MAC"

# Deploy using compose
if [[ "$METAL_ENABLED" == "true" ]]; then
    echo "🔗 Deploying with Metal Performance Shaders..."
    docker-compose -f "$COMPOSE_FILE" up -d "$SERVICE_NAME-metal"
else
    echo "💻 Deploying CPU-only..."
    docker-compose -f "$COMPOSE_FILE" up -d "$SERVICE_NAME-cpu"
fi

# Show status
echo ""
echo "📊 Container Status:"
docker-compose -f "$COMPOSE_FILE" ps

echo ""
echo "✅ Deployment complete!"
echo "Monitor with: ./scripts/monitor-workloads.sh --platform mac"