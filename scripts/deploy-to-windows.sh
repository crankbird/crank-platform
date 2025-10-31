#!/bin/bash
# Deploy AI/ML containers to Windows Docker Desktop from WSL control plane

set -euo pipefail

# Configuration
DOCKER_HOST_WINDOWS="npipe:////./pipe/docker_engine"
COMPOSE_FILE="docker-compose.windows.yml"
SERVICE_NAME="aiml-dev"
GPU_ENABLED=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --gpu)
            GPU_ENABLED=true
            shift
            ;;
        --service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --compose-file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🚀 Deploying to Windows Docker Desktop..."
echo "Service: $SERVICE_NAME"
echo "GPU: $GPU_ENABLED"
echo "Compose: $COMPOSE_FILE"

# Check if Docker Desktop is running on Windows
if ! docker -H "$DOCKER_HOST_WINDOWS" version >/dev/null 2>&1; then
    echo "❌ Cannot connect to Windows Docker Desktop"
    echo "Please ensure Docker Desktop is running on Windows host"
    exit 1
fi

# Set Docker context to Windows host
export DOCKER_HOST="$DOCKER_HOST_WINDOWS"

# Deploy using compose
if [[ "$GPU_ENABLED" == "true" ]]; then
    echo "🎮 Deploying with GPU support..."
    docker-compose -f "$COMPOSE_FILE" up -d "$SERVICE_NAME-gpu"
else
    echo "💻 Deploying CPU-only..."
    docker-compose -f "$COMPOSE_FILE" up -d "$SERVICE_NAME-cpu"
fi

# Show status
echo ""
echo "📊 Container Status:"
docker-compose -f "$COMPOSE_FILE" ps

echo ""
echo "🌐 Access URLs:"
echo "Jupyter: http://localhost:8888"
echo "TensorBoard: http://localhost:6006"

echo ""
echo "✅ Deployment complete!"
echo "Monitor with: ./scripts/monitor-workloads.sh --platform windows"