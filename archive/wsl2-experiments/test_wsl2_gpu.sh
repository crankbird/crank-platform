#!/bin/bash
# WSL2 GPU Test Script - updated with WSL2 CUDA paths

echo "Testing updated WSL2 GPU environment with CUDA paths..."

# Set WSL2 CUDA environment
export PATH="$HOME/miniconda3/bin:/usr/lib/wsl/lib:$PATH"
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:$LD_LIBRARY_PATH"
export CUDA_PATH="/usr/lib/wsl/lib"

# Activate environment
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate aiml-hybrid-gpu

echo "Environment activated with CUDA paths:"
echo "PATH includes: $(echo $PATH | grep -o '/usr/lib/wsl/lib')"
echo "LD_LIBRARY_PATH includes: $(echo $LD_LIBRARY_PATH | grep -o '/usr/lib/wsl/lib')"
echo "CUDA_PATH: $CUDA_PATH"

# Test nvidia-smi
echo ""
echo "Testing nvidia-smi..."
if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader
else
    echo "nvidia-smi not found, trying full path..."
    /usr/lib/wsl/lib/nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader
fi

# Test PyTorch CUDA
echo ""
echo "Testing PyTorch CUDA availability..."
python -c "
import torch
print(f'PyTorch CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA device count: {torch.cuda.device_count()}')
    print(f'Current device: {torch.cuda.current_device()}')
    print(f'Device name: {torch.cuda.get_device_name()}')
else:
    print('CUDA not available - checking paths...')
    import os
    print(f'CUDA_PATH: {os.environ.get(\"CUDA_PATH\", \"Not set\")}')
    print(f'LD_LIBRARY_PATH: {os.environ.get(\"LD_LIBRARY_PATH\", \"Not set\")}')
"

echo ""
echo "Test complete."