#!/bin/bash
# install-gpu-dependencies.sh
# Automated installation of Universal GPU service dependencies

set -e

echo "🔧 Installing Universal GPU Service Dependencies"
echo "=============================================="

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# Check for uv vs pip
if command -v uv &> /dev/null; then
    INSTALLER="uv pip"
    echo "⚡ Using uv for fast installation"
else
    INSTALLER="pip"
    echo "🐌 Using pip (consider installing uv for speed)"
fi

echo ""
echo "1️⃣ Installing Core PyTorch Dependencies..."
echo "----------------------------------------"

# PyTorch installation with platform detection
if [[ "$(uname)" == "Darwin" ]] && [[ "$(uname -m)" == "arm64" ]]; then
    echo "🍎 Apple Silicon detected - installing MPS-compatible PyTorch"
    $INSTALLER install torch torchvision torchaudio
elif command -v nvidia-smi &> /dev/null; then
    echo "🎮 NVIDIA GPU detected - installing CUDA PyTorch"
    $INSTALLER install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
else
    echo "💻 CPU-only installation"
    $INSTALLER install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

echo ""
echo "2️⃣ Installing ML and GPU Libraries..."
echo "------------------------------------"

$INSTALLER install \
    ultralytics \
    GPUtil \
    opencv-python \
    psutil \
    pillow \
    numpy

echo ""
echo "3️⃣ Validating Installation..."
echo "----------------------------"

python3 -c "
import sys
import torch

print(f'✅ PyTorch {torch.__version__} imported successfully')

# Test GPU detection
if torch.cuda.is_available():
    print(f'🎮 CUDA available: {torch.cuda.device_count()} GPU(s)')
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    print(f'🍎 Metal Performance Shaders (MPS) available')
else:
    print(f'💻 CPU-only mode')

# Test ML library imports
try:
    from ultralytics import YOLO
    print('✅ ultralytics imported successfully')
except ImportError as e:
    print(f'❌ ultralytics import failed: {e}')
    sys.exit(1)

try:
    import GPUtil
    print('✅ GPUtil imported successfully')
except ImportError as e:
    print(f'❌ GPUtil import failed: {e}')
    sys.exit(1)

try:
    import cv2
    print('✅ opencv-python imported successfully')
except ImportError as e:
    print(f'❌ opencv-python import failed: {e}')
    sys.exit(1)

print('')
print('🎯 All dependencies installed and validated!')
"

echo ""
echo "✅ Universal GPU dependencies installed successfully!"
echo "🚀 Ready for UniversalGPUManager integration"
