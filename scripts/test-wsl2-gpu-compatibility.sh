#!/bin/bash
# WSL2 GPU Docker Compatibility Test Script
# Tests the CUDA_VISIBLE_DEVICES vs NVIDIA_VISIBLE_DEVICES environment variable issue
# See: docs/WSL2-GPU-CUDA-COMPATIBILITY.md

set -e

echo "🧪 WSL2 GPU Docker Compatibility Test"
echo "======================================="

# Detect WSL2 environment
if uname -r | grep -q -i microsoft; then
    echo "✅ WSL2 Environment Detected"
    WSL2=true
else
    echo "ℹ️  Native Linux Environment"
    WSL2=false
fi

# Check if DirectX Graphics device exists (WSL2-specific)
if [ -e "/dev/dxg" ]; then
    echo "✅ DirectX Graphics Device Found (/dev/dxg) - WSL2 GPU Mode"
else
    echo "ℹ️  No DirectX Graphics Device - Traditional NVIDIA Mode"
fi

# Check for GPU runtime
if ! docker info | grep -q nvidia; then
    echo "❌ Docker NVIDIA runtime not available"
    echo "   Install: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
    exit 1
fi

echo "✅ Docker NVIDIA runtime available"

# Check if our local GPU container image exists
if ! docker image inspect crank-crank-image-classifier-gpu-dev >/dev/null 2>&1; then
    echo "❌ Local GPU container image not found"
    echo "   Run: docker compose -f docker-compose.development.yml up crank-image-classifier-gpu-dev -d"
    exit 1
fi

echo "✅ Using existing crank-image-classifier-gpu-dev container"

# Test problematic configuration
echo ""
echo "🔴 Testing PROBLEMATIC configuration (CUDA_VISIBLE_DEVICES=all):"
echo "   Expected Result: PyTorch CUDA should be FALSE in WSL2"

CUDA_RESULT=$(docker run --rm --gpus all \
    -e CUDA_VISIBLE_DEVICES=all \
    crank-crank-image-classifier-gpu-dev \
    python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null || echo "FAILED")

echo "   Result: CUDA Available = $CUDA_RESULT"

if [ "$WSL2" = true ] && [ "$CUDA_RESULT" = "False" ]; then
    echo "   ✅ Expected behavior: WSL2 incompatibility confirmed"
elif [ "$WSL2" = true ] && [ "$CUDA_RESULT" = "True" ]; then
    echo "   ⚠️  Unexpected: WSL2 issue may be resolved upstream!"
elif [ "$WSL2" = false ] && [ "$CUDA_RESULT" = "True" ]; then
    echo "   ✅ Expected behavior: Native Linux working normally"
else
    echo "   ❌ Unexpected result in native Linux"
fi

# Test working configuration
echo ""
echo "🟢 Testing WORKING configuration (NVIDIA_VISIBLE_DEVICES=all):"
echo "   Expected Result: PyTorch CUDA should be TRUE"

NVIDIA_RESULT=$(docker run --rm --gpus all \
    -e NVIDIA_VISIBLE_DEVICES=all \
    crank-crank-image-classifier-gpu-dev \
    python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null || echo "FAILED")

echo "   Result: CUDA Available = $NVIDIA_RESULT"

if [ "$NVIDIA_RESULT" = "True" ]; then
    echo "   ✅ Working correctly"
else
    echo "   ❌ GPU access failed - check Docker GPU setup"
fi

# Test nvidia-smi (should work in both cases)
echo ""
echo "🔧 Testing nvidia-smi availability (should work regardless):"

SMI_RESULT=$(docker run --rm --gpus all \
    -e CUDA_VISIBLE_DEVICES=all \
    crank-crank-image-classifier-gpu-dev \
    nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || echo "FAILED")

echo "   nvidia-smi GPU: $SMI_RESULT"

# Summary
echo ""
echo "📊 SUMMARY:"
echo "=========="
echo "Environment: $(if [ "$WSL2" = true ]; then echo "WSL2"; else echo "Native Linux"; fi)"
echo "CUDA_VISIBLE_DEVICES=all:    PyTorch CUDA = $CUDA_RESULT"
echo "NVIDIA_VISIBLE_DEVICES=all:  PyTorch CUDA = $NVIDIA_RESULT"
echo "nvidia-smi:                  $SMI_RESULT"

if [ "$WSL2" = true ] && [ "$CUDA_RESULT" = "False" ] && [ "$NVIDIA_RESULT" = "True" ]; then
    echo ""
    echo "🎯 CONFIRMED: WSL2 CUDA_VISIBLE_DEVICES incompatibility detected"
    echo "   📖 See docs/WSL2-GPU-CUDA-COMPATIBILITY.md for full details"
    echo "   🔧 Use NVIDIA_VISIBLE_DEVICES=all in Docker Compose files"
elif [ "$WSL2" = true ] && [ "$CUDA_RESULT" = "True" ]; then
    echo ""
    echo "🎉 WSL2 CUDA compatibility may be fixed upstream!"
    echo "   📖 Consider updating docs/WSL2-GPU-CUDA-COMPATIBILITY.md"
    echo "   🧪 Test with multiple PyTorch versions to confirm"
fi

echo ""
echo "✅ Test completed"
