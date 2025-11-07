#!/bin/bash
# validate-host-environment.sh
# Validates minimal host requirements for universal GPU containers

set -euo pipefail

FULL_TEST=false

# Simple args: --full to run heavier platform checks (may pull large images)
while [[ $# -gt 0 ]]; do
    case "$1" in
        --full)
            FULL_TEST=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--full]"
            echo "  --full   Run full platform checks (may pull large Docker images)"
            exit 0
            ;;
        *)
            echo "Unknown arg: $1"
            echo "Usage: $0 [--full]"
            exit 2
            ;;
    esac
done

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
    echo "🍎 Apple Silicon detected - checking Docker Desktop..."

    # Check Docker Desktop is installed (required for Apple Silicon)
    if docker info | grep -q "Operating System.*Docker Desktop"; then
        echo "✅ Docker Desktop detected"

        # Quick platform test (skip heavy MPS testing by default)
        if docker run --rm --platform linux/arm64 hello-world >/dev/null 2>&1; then
            echo "✅ ARM64 container support working"
        else
            echo "⚠️  ARM64 container support may have issues"
        fi

        if [[ "$FULL_TEST" == "true" ]]; then
            echo "🔎 Running full Apple Silicon GPU runtime check (may pull large images)"
            echo "ℹ️  This may take a while and consume bandwidth. Press Ctrl+C to cancel."
            # Attempt to run a PyTorch image that reports MPS availability. This is optional and
            # may fail on some configurations; it's gated behind --full.
            if docker run --rm --platform linux/arm64 pytorch/pytorch:latest \
                python -c "import torch, sys; print('MPS:', getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available())"; then
                echo "✅ Full MPS check completed (see output above)"
            else
                echo "⚠️  Full MPS check failed or timed out"
                echo "   This does not necessarily indicate a problem; full MPS checks are best run inside dev containers."
            fi
        else
            echo "ℹ️  Note: MPS/Metal GPU testing will happen in application containers"
            echo "   (Docker containers can't access macOS Metal directly)"
        fi
    else
        echo "❌ Docker Desktop not detected"
        echo "📋 Install Docker Desktop for macOS with Apple Silicon support"
        exit 1
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
