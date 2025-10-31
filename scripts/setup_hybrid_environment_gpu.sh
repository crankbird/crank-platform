#!/usr/bin/env bash
set -euo pipefail

# GPU-Enabled uv + Conda Hybrid Environment Setup Script
# Optimized for WSL2 with NVIDIA GPU support

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1...${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Error handling
handle_error() {
    log_error "Setup failed at line $1. Exit code: $2"
    log_info "Check the output above for details"
    exit $2
}
trap 'handle_error $LINENO $?' ERR

# Configuration
ENV_NAME="aiml-hybrid-gpu"
MINICONDA_VERSION="latest"
PYTHON_VERSION="3.11"

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if we're in WSL2
    if ! grep -qi microsoft /proc/version; then
        log_warning "This script is optimized for WSL2. Continuing anyway..."
    fi
    
    # Check for NVIDIA GPU - look for WSL2 GPU device first
    if [[ -e "/dev/dxg" ]]; then
        log_success "WSL2 GPU device detected (/dev/dxg)"
        
        # Install NVIDIA drivers and tools if not present
        if ! command -v nvidia-smi >/dev/null 2>&1; then
            log_info "Installing NVIDIA drivers and tools"
            sudo apt update -qq
            
            # Add NVIDIA container toolkit repository
            curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
            curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
                sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
                sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
            
            sudo apt update -qq
            sudo apt install -y nvidia-container-toolkit nvidia-utils-525 || {
                log_warning "Failed to install nvidia-utils-525, trying nvidia-utils"
                sudo apt install -y nvidia-container-toolkit nvidia-utils || {
                    log_warning "NVIDIA tools installation failed, continuing without nvidia-smi"
                }
            }
        fi
        
        # Test nvidia-smi if available
        if command -v nvidia-smi >/dev/null 2>&1; then
            echo "GPU detected:"
            nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits | \
                awk -F, '{printf "   GPU: %s (%s MB VRAM, Driver: %s)\n", $1, $2, $3}'
            echo
        else
            log_warning "nvidia-smi not available, GPU packages will be installed but monitoring limited"
        fi
        
    elif nvidia-smi >/dev/null 2>&1; then
        log_success "NVIDIA GPU detected via nvidia-smi"
        # Display GPU info if nvidia-smi works
        echo "GPU detected:"
        nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits | \
            awk -F, '{printf "   GPU: %s (%s MB VRAM, Driver: %s)\n", $1, $2, $3}'
        echo
    else
        log_error "No NVIDIA GPU detected. Make sure WSL2 has GPU access enabled"
        exit 1
    fi
    
    # Check for curl
    if ! command -v curl >/dev/null 2>&1; then
        log_info "Installing curl..."
        sudo apt update -qq
        sudo apt install -y curl
    fi
    
    log_success "Prerequisites checked"
}

# Install Miniconda
install_miniconda() {
    if [[ -d "$HOME/miniconda3" ]]; then
        log_info "Miniconda already installed, skipping..."
        return 0
    fi
    
    log_info "Installing Miniconda..."
    
    cd /tmp
    curl -fsSLO "https://repo.anaconda.com/miniconda/Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh"
    bash "Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh" -b -p "$HOME/miniconda3"
    rm -f "Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh"
    
    # Initialize conda
    export PATH="$HOME/miniconda3/bin:$PATH"
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    conda config --set auto_activate_base false
    
    log_success "Miniconda installed"
}

# Create conda environment
create_conda_environment() {
    log_info "Creating conda environment '$ENV_NAME'"
    
    export PATH="$HOME/miniconda3/bin:$PATH"
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    
    # Accept conda Terms of Service automatically for all channels
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main || true
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r || true
    
    # Create environment
    conda create -n "$ENV_NAME" python="$PYTHON_VERSION" -y -q || {
        log_warning "Environment may already exist, continuing..."
    }
    
    conda activate "$ENV_NAME"
    log_success "Conda environment created and activated"
}

# Install conda packages (GPU-enabled versions)
install_conda_packages() {
    log_info "Installing conda packages (GPU-enabled)..."
    
    export PATH="$HOME/miniconda3/bin:$PATH"
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    conda activate "$ENV_NAME"
    
    # Accept Terms of Service for all channels
    echo "yes" | conda config --add channels conda-forge || true
    echo "yes" | conda config --add channels pytorch || true
    echo "yes" | conda config --add channels nvidia || true
    
    # Scientific computing stack
    log_info "Installing scientific computing stack..."
    conda install -y \
        numpy pandas scipy matplotlib seaborn \
        scikit-learn statsmodels patsy \
        openblas nomkl
    
    # Jupyter ecosystem
    log_info "Installing Jupyter..."
    conda install -y -c conda-forge \
        jupyter jupyterlab ipykernel
    
    # GPU-enabled PyTorch with CUDA
    log_info "Installing PyTorch with CUDA support..."
    conda install -y pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
    
    # Computer Vision with GPU support
    log_info "Installing OpenCV with GPU support..."
    conda install -y -c conda-forge opencv
    
    log_success "Conda packages installed"
}

# Install uv in conda environment
install_uv() {
    log_info "Installing uv in conda environment..."
    
    export PATH="$HOME/miniconda3/bin:$PATH"
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    conda activate "$ENV_NAME"
    
    pip install uv
    log_success "uv installed in conda environment"
}

# Install pure Python packages via uv
install_uv_packages() {
    log_info "Installing pure Python packages via uv..."
    
    export PATH="$HOME/miniconda3/bin:$PATH"
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    conda activate "$ENV_NAME"
    
    # HuggingFace ecosystem (pure Python, fast installation)
    log_info "Installing HuggingFace ecosystem..."
    uv pip install transformers datasets accelerate diffusers tokenizers
    
    # Machine Learning tools
    log_info "Installing ML tools..."
    uv pip install scikit-learn xgboost lightgbm optuna wandb mlflow
    
    # Development tools
    log_info "Installing development tools..."
    uv pip install black isort flake8 pytest ipywidgets tqdm rich
    
    # API and web frameworks
    log_info "Installing web frameworks..."
    uv pip install fastapi uvicorn requests httpx
    
    # AI/LLM tools
    log_info "Installing AI tools..."
    uv pip install openai anthropic langchain ultralytics
    
    # Data processing
    log_info "Installing data tools..."
    uv pip install polars duckdb sqlalchemy alembic
    
    # GPU-specific packages
    log_info "Installing GPU-specific packages..."
    uv pip install nvidia-ml-py3 gputil cupy-cuda12x
    
    log_success "uv packages installed"
}

# Export environment specifications
export_environment() {
    log_info "Exporting environment specifications..."
    
    export PATH="$HOME/miniconda3/bin:$PATH"
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    conda activate "$ENV_NAME"
    
    # Export conda environment
    conda env export > environment-gpu.yml
    log_success "Conda environment exported to environment-gpu.yml"
    
    # Export uv packages
    uv pip freeze > requirements-uv-gpu.txt
    log_success "uv packages exported to requirements-uv-gpu.txt"
    
    # Create combined requirements for pip fallback
    pip freeze > requirements-all-gpu.txt
    log_success "All packages exported to requirements-all-gpu.txt"
}

# Test the installation with GPU
test_installation() {
    log_info "Testing GPU-enabled installation..."
    
    # Test basic imports with proper error handling
    "$HOME/miniconda3/envs/$ENV_NAME/bin/python" -c "
import sys
print(f'Python: {sys.version}')

# Test conda packages
try:
    import numpy as np
    import pandas as pd
    import torch
    print(f'NumPy: {np.__version__}')
    print(f'Pandas: {pd.__version__}')
    print(f'PyTorch: {torch.__version__}')
    
    # Test GPU/CUDA availability
    print(f'CUDA available: {torch.cuda.is_available()}')
    if torch.cuda.is_available():
        print(f'CUDA device count: {torch.cuda.device_count()}')
        print(f'Current CUDA device: {torch.cuda.current_device()}')
        print(f'CUDA device name: {torch.cuda.get_device_name()}')
        print(f'CUDA capability: {torch.cuda.get_device_capability()}')
        print(f'CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')
        
        # Test a simple GPU operation
        x = torch.randn(1000, 1000).cuda()
        y = torch.matmul(x, x.t())
        print(f'GPU tensor test: {y.shape} (device: {y.device})')
    else:
        print('⚠️  CUDA not available - check GPU drivers and PyTorch installation')
except ImportError as e:
    print(f'Error importing conda packages: {e}')
    sys.exit(1)

# Test uv packages
try:
    import transformers
    import fastapi
    import sklearn
    print(f'Transformers: {transformers.__version__}')
    print(f'FastAPI: {fastapi.__version__}')
    print(f'Scikit-learn: {sklearn.__version__}')
except ImportError as e:
    print(f'Error importing uv packages: {e}')
    sys.exit(1)

# Test GPU-specific packages
try:
    import cupy
    import nvidia_ml_py3 as nvml
    print(f'CuPy: {cupy.__version__}')
    
    # NVIDIA Management Library info
    nvml.nvmlInit()
    handle = nvml.nvmlDeviceGetHandleByIndex(0)
    name = nvml.nvmlDeviceGetName(handle)
    memory_info = nvml.nvmlDeviceGetMemoryInfo(handle)
    print(f'NVML GPU: {name.decode(\"utf-8\")}')
    print(f'GPU Memory: {memory_info.used/1e6:.0f}MB / {memory_info.total/1e6:.0f}MB used')
except ImportError as e:
    print(f'Warning: GPU packages not fully available: {e}')
except Exception as e:
    print(f'Warning: GPU monitoring error: {e}')

print()
print('✅ All packages imported successfully')
" || {
        log_error "Package import test failed"
        return 1
    }
    
    log_success "GPU installation test completed successfully"
}

# Detect package conflicts
check_conflicts() {
    log_info "Checking for package conflicts..."
    
    export PATH="$HOME/miniconda3/bin:$PATH"
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    conda activate "$ENV_NAME"
    
    # Create temporary files for package lists
    TEMP_DIR=$(mktemp -d)
    CONDA_PACKAGES="$TEMP_DIR/conda_packages.txt"
    UV_PACKAGES="$TEMP_DIR/uv_packages.txt"
    
    # Get package lists with error handling
    conda list 2>/dev/null | grep -v "^#" | awk '{print $1}' | sort > "$CONDA_PACKAGES" || {
        log_warning "Could not get conda package list"
        rm -rf "$TEMP_DIR"
        return 0
    }
    
    uv pip list 2>/dev/null | tail -n +3 | awk '{print $1}' | sort > "$UV_PACKAGES" || {
        log_warning "Could not get uv package list"
        rm -rf "$TEMP_DIR"
        return 0
    }
    
    # Find overlapping packages
    CONFLICTS=$(comm -12 "$CONDA_PACKAGES" "$UV_PACKAGES" 2>/dev/null || true)
    
    if [ -n "$CONFLICTS" ] && [ "$CONFLICTS" != "" ]; then
        log_warning "Found overlapping packages (potential conflicts):"
        echo "$CONFLICTS" | head -10  # Limit output
        if [ $(echo "$CONFLICTS" | wc -l) -gt 10 ]; then
            echo "... and $(( $(echo "$CONFLICTS" | wc -l) - 10 )) more"
        fi
        echo
        log_info "These conflicts are usually harmless as both managers can coexist"
        log_info "To resolve conflicts manually:"
        echo "  conda remove <package>  # Remove from conda"
        echo "  uv pip uninstall <package>  # Remove from uv"
    else
        log_success "No package conflicts detected"
    fi
    
    # Cleanup
    rm -rf "$TEMP_DIR"
}

# Setup convenient aliases
setup_aliases() {
    log_info "Setting up convenient aliases..."
    
    # Create activation script with WSL2 CUDA paths
    cat > ~/activate_aiml_gpu.sh << 'EOF'
#!/bin/bash
# Set WSL2 CUDA environment
export PATH="$HOME/miniconda3/bin:/usr/lib/wsl/lib:$PATH"
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:$LD_LIBRARY_PATH"
export CUDA_PATH="/usr/lib/wsl/lib"

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate aiml-hybrid-gpu
echo "🚀 GPU-enabled AI/ML hybrid environment activated"
echo "📦 Conda packages: $(conda list | wc -l) packages"
echo "⚡ uv packages: $(uv pip list | tail -n +3 | wc -l) packages"

# GPU detection
if command -v nvidia-smi >/dev/null 2>&1; then
    echo "🎮 GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
else
    echo "🎮 GPU: nvidia-smi not found in PATH"
fi

# Test PyTorch CUDA
python -c "import torch; print(f'🔥 PyTorch CUDA: {torch.cuda.is_available()}')" 2>/dev/null || echo "⚠️ PyTorch not available"
EOF
    chmod +x ~/activate_aiml_gpu.sh
    
    # Add aliases to bashrc
    if ! grep -q "# uv+conda GPU aliases" ~/.bashrc; then
        cat >> ~/.bashrc << 'EOF'

# uv+conda GPU aliases
alias aiml-gpu='source ~/activate_aiml_gpu.sh'
alias conda-export-gpu='conda env export > environment-gpu.yml'
alias uv-export-gpu='uv pip freeze > requirements-uv-gpu.txt'
alias gpu-status='nvidia-smi'
alias check-conflicts='comm -12 <(conda list | awk "{print \$1}" | sort) <(uv pip list | tail -n +3 | awk "{print \$1}" | sort)'
EOF
        log_success "GPU aliases added to ~/.bashrc"
    fi
}

# Main installation function
main() {
    log_info "Starting GPU-enabled uv + Conda hybrid installation..."
    echo
    
    check_prerequisites
    install_miniconda
    create_conda_environment
    install_conda_packages
    install_uv
    install_uv_packages
    export_environment
    test_installation
    check_conflicts
    setup_aliases
    
    echo
    log_success "🎉 GPU-enabled uv + Conda hybrid environment setup complete"
    echo
    echo "Next steps:"
    echo "1. Activate the environment:"
    echo "   source ~/activate_aiml_gpu.sh"
    echo "   # or just: aiml-gpu"
    echo
    echo "2. Test GPU functionality:"
    echo "   python -c 'import torch; print(f\"CUDA: {torch.cuda.is_available()}\")'"
    echo
    echo "3. Environment files created:"
    echo "   - environment-gpu.yml (conda packages)"
    echo "   - requirements-uv-gpu.txt (uv packages)"  
    echo "   - requirements-all-gpu.txt (all packages)"
    echo
    echo "4. Useful aliases:"
    echo "   - aiml-gpu: activate environment"
    echo "   - gpu-status: show GPU information"
    echo "   - conda-export-gpu: export conda packages"
    echo "   - uv-export-gpu: export uv packages"
    echo "   - check-conflicts: find overlapping packages"
}

# Run main function
main "$@"