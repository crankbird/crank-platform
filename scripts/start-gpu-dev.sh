#!/bin/bash
# GPU Development Starter for WSL2/Docker Desktop
# Starts the GPU service with proper --gpus all access

set -e

echo "🎮 Starting Crank Platform with GPU support for WSL2/Docker Desktop"
echo "=================================================================="

# Stop any existing GPU container
echo "Stopping existing GPU container..."
docker-compose -f docker-compose.development.yml stop crank-image-classifier-gpu-dev || true
docker-compose -f docker-compose.development.yml rm -f crank-image-classifier-gpu-dev || true

# Start the rest of the services without GPU service
echo "Starting platform services (without GPU service)..."
docker-compose -f docker-compose.development.yml up -d --scale crank-image-classifier-gpu-dev=0

# Wait for platform to be ready
echo "Waiting for platform to be ready..."
sleep 10

# Start GPU service with proper GPU access
echo "Starting GPU service with proper GPU access..."
docker run -d \
  --name crank-image-classifier-gpu-dev \
  --network crank-local-network \
  --gpus all \
  -p 8400:8400 \
  -v "$(pwd)/services:/app/services:ro" \
  -v "$(pwd)/shared:/app/shared:ro" \
  -e CRANK_ENVIRONMENT=development \
  -e LOG_LEVEL=DEBUG \
  -e IMAGE_CLASSIFIER_HTTPS_PORT=8400 \
  -e IMAGE_CLASSIFIER_SERVICE_NAME=crank-image-classifier-gpu-dev \
  -e CUDA_VISIBLE_DEVICES=all \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
  -e CA_SERVICE_URL=https://crank-cert-authority-dev:9090 \
  -e HTTPS_ONLY=true \
  -e PLATFORM_URL=https://crank-platform-dev:8443 \
  -e PLATFORM_AUTH_TOKEN=local-dev-key \
  --restart unless-stopped \
  crank-crank-image-classifier-gpu-dev

echo "✅ GPU service started with proper GPU access!"
echo "Testing GPU functionality..."

# Test GPU access
sleep 5
if docker exec crank-image-classifier-gpu-dev python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())" | grep -q "True"; then
    echo "🎉 SUCCESS! GPU is working in container!"
else
    echo "❌ GPU test failed"
    exit 1
fi

echo "🚀 Platform ready with GPU support!"
echo "GPU Service: https://localhost:8400/health"
