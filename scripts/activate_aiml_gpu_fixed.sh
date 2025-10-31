#!/bin/bash
# Updated activation script with WSL2 CUDA environment variables

echo "🚀 GPU-enabled AI/ML hybrid environment activated"

# Set WSL2 CUDA environment
export PATH="$HOME/miniconda3/bin:/usr/lib/wsl/lib:$PATH"
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:$LD_LIBRARY_PATH"
export CUDA_PATH="/usr/lib/wsl/lib"

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate aiml-hybrid-gpu

# Show environment info
echo "📦 Conda packages: $(conda list | wc -l) packages"
echo "Using Python $(python --version 2>&1 | cut -d' ' -f2) environment at: $(conda info --envs | grep '*' | awk '{print $NF}' | sed 's|.*/||')"
echo "⚡ uv packages: $(uv pip list | tail -n +3 | wc -l) packages"

# Show CUDA environment
echo "🔧 CUDA_PATH: $CUDA_PATH"
echo "🔧 LD_LIBRARY_PATH includes WSL: $(echo $LD_LIBRARY_PATH | grep -o '/usr/lib/wsl/lib' || echo 'not found')"

# GPU detection
if command -v nvidia-smi >/dev/null 2>&1; then
    echo "🎮 GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
else
    echo "🎮 GPU: nvidia-smi not found in PATH, trying full path..."
    if [ -f /usr/lib/wsl/lib/nvidia-smi ]; then
        echo "🎮 GPU: $(/usr/lib/wsl/lib/nvidia-smi --query-gpu=name --format=csv,noheader)"
    else
        echo "🎮 GPU: nvidia-smi not found"
    fi
fi

# Test PyTorch CUDA
echo -n "🔥 PyTorch CUDA: "
python -c "import torch; print(torch.cuda.is_available())" 2>/dev/null || echo "PyTorch not available"