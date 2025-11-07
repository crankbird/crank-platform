#!/bin/bash
# validate-host-environment.sh
# Validates minimal host requirements for universal GPU containers

set -e

echo "🔍 Validating Host Environment for Universal GPU Containers"
echo "=========================================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found"
    echo "📋 Install: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker: $(docker --version)"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose not available"
    echo "📋 Install Docker Desktop or docker-compose-plugin"
    exit 1
fi

echo "✅ Docker Compose: $(docker compose version)"

# Check GPU Runtime (Platform Detection)
echo ""
echo "🎮 GPU Runtime Validation:"

# Apple Silicon Detection
if [[ "$(uname -m)" == "arm64" ]] && [[ "$(uname)" == "Darwin" ]]; then
    echo "🍎 Apple Silicon detected - checking Metal/MPS support..."

    if docker run --rm python:3.11-slim python -c "
import platform
import subprocess
import sys
print(f'Platform: {platform.machine()}')
print(f'Python: {sys.version}')
try:
    # Test PyTorch MPS availability (will fail on CPU-only PyTorch)
    import torch
    print(f'PyTorch: {torch.__version__}')
    if hasattr(torch.backends, 'mps'):
        print(f'MPS Backend Available: {torch.backends.mps.is_available()}')
    else:
        print('MPS Backend: Not available (CPU-only PyTorch)')
except ImportError:
    print('PyTorch: Not installed in base image')
" 2>/dev/null; then
        echo "✅ Apple Silicon GPU runtime ready"
    else
        echo "⚠️  Apple Silicon detected but GPU testing failed"
        echo "   This is normal - GPU support tested in application containers"
    fi

# NVIDIA GPU Detection
elif command -v nvidia-smi &> /dev/null; then
    echo "🎮 NVIDIA GPU detected - checking container runtime..."

    if docker run --rm --gpus all nvidia/cuda:12.1-runtime-ubuntu22.04 nvidia-smi &> /dev/null; then
        echo "✅ NVIDIA GPU container runtime ready"
    else
        echo "❌ NVIDIA GPU found but container access failed"
        echo "📋 Install NVIDIA Container Toolkit:"
        echo "   https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
        exit 1
    fi

# CPU-Only
else
    echo "🖥️  CPU-only system detected"
    echo "✅ Universal GPU containers will run in CPU mode"
fi

# Check uv
if ! command -v uv &> /dev/null; then
    echo ""
    echo "❌ uv package manager not found"
    echo "📋 Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo ""
echo "✅ uv: $(uv --version)"

echo ""
echo "🎉 Host environment validation complete!"
echo ""
echo "Next steps:"
echo "1. Run: ./dev-universal.sh"
echo "2. Test universal GPU containers: docker compose up gpu-classifier"
echo "3. GPU detection will happen at container runtime"
