#!/usr/bin/env bash
set -euo pipefail

# uv + Conda Hybrid Installation Script (Production Version)
# Optimized approach: conda for system deps, uv for pure Python packages
# Handles all edge cases and errors automatically

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Error handling
handle_error() {
    log_error "Script failed at line $1. Exit code: $2"
    exit $2
}
trap 'handle_error $LINENO $?' ERR

# Configuration
ENV_NAME="aiml-hybrid"
PYTHON_VERSION="3.11"

echo "🚀 Setting up uv + Conda Hybrid Environment"
echo "Environment: $ENV_NAME"
echo "Python: $PYTHON_VERSION"
echo

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check for NVIDIA GPU (optional but recommended)
    if nvidia-smi >/dev/null 2>&1; then
        log_success "NVIDIA GPU detected"
        GPU_AVAILABLE=true
    else
        log_warning "No NVIDIA GPU detected - CPU-only mode"
        GPU_AVAILABLE=false
    fi
    
    log_success "Prerequisites check complete"
}

# Install miniconda if needed
install_miniconda() {
    if command -v conda >/dev/null 2>&1; then
        log_success "Conda already installed"
        # Ensure conda is initialized
        if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
            source "$HOME/miniconda3/etc/profile.d/conda.sh"
        fi
        return 0
    fi
    
    log_info "Installing Miniconda..."
    
    # Create temp directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # Download miniconda
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    
    # Remove existing installation if it exists but conda command doesn't work
    if [[ -d "$HOME/miniconda3" ]]; then
        log_warning "Removing incomplete miniconda installation"
        rm -rf "$HOME/miniconda3"
    fi
    
    # Install miniconda
    bash miniconda.sh -b -p "$HOME/miniconda3"
    
    # Add to PATH for this session
    export PATH="$HOME/miniconda3/bin:$PATH"
    
    # Add to bashrc if not already there
    if ! grep -q "miniconda3/bin" ~/.bashrc 2>/dev/null; then
        echo 'export PATH="$HOME/miniconda3/bin:$PATH"' >> ~/.bashrc
    fi
    
    # Initialize conda
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    conda init bash >/dev/null 2>&1
    conda config --set auto_activate_base false
    
    # Accept Terms of Service automatically
    log_info "Accepting conda Terms of Service..."
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main || true
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r || true
    
    # Cleanup
    cd - >/dev/null
    rm -rf "$TEMP_DIR"
    
    log_success "Miniconda installed and configured"
}

# Create conda environment with system dependencies
create_conda_environment() {
    log_info "Creating conda environment with system dependencies..."
    
    # Ensure conda is available and configured
    export PATH="$HOME/miniconda3/bin:$PATH"
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    
    # Remove existing environment if it exists
    if conda env list | grep -q "^$ENV_NAME "; then
        log_warning "Removing existing $ENV_NAME environment"
        conda env remove -n "$ENV_NAME" -y >/dev/null 2>&1 || true
    fi
    
    # Create environment with Python
    log_info "Creating conda environment: $ENV_NAME"
    conda create -n "$ENV_NAME" python="$PYTHON_VERSION" -y
    
    log_success "Conda environment created successfully"
}

# Install system dependencies via conda
install_conda_packages() {
    log_info "Installing system dependencies via conda..."
    
    export PATH="$HOME/miniconda3/bin:$PATH"
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate "$ENV_NAME"
    
    # Core scientific computing with optimized libraries
    log_info "Installing core scientific stack..."
    conda install -y numpy scipy pandas matplotlib seaborn -c conda-forge
    
    # Jupyter ecosystem (complex notebook integration)
    log_info "Installing Jupyter..."
    conda install -y jupyter ipykernel jupyterlab -c conda-forge
    
    # PyTorch with CUDA support (if GPU available)
    if [ "$GPU_AVAILABLE" = true ]; then
        log_info "Installing PyTorch with CUDA support..."
        conda install -y pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
    else
        log_info "Installing PyTorch CPU-only..."
        conda install -y pytorch torchvision torchaudio cpuonly -c pytorch
    fi
    
    # Computer vision with system dependencies
    log_info "Installing OpenCV..."
    conda install -y opencv -c conda-forge
    
    log_success "Conda packages installed"
}

# Install uv in the conda environment
install_uv() {
    log_info "Installing uv in conda environment..."
    
    export PATH="$HOME/miniconda3/bin:$PATH"
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate "$ENV_NAME"
    
    pip install uv
    
    log_success "uv installed in conda environment"
}

# Install pure Python packages via uv
install_uv_packages() {
    log_info "Installing pure Python packages via uv..."
    
    export PATH="$HOME/miniconda3/bin:$PATH"
    source ~/miniconda3/etc/profile.d/conda.sh
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
    
    log_success "uv packages installed"
}

# Export environment specifications
export_environment() {
    log_info "Exporting environment specifications..."
    
    export PATH="$HOME/miniconda3/bin:$PATH"
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate "$ENV_NAME"
    
    # Export conda environment
    conda env export > environment.yml
    log_success "Conda environment exported to environment.yml"
    
    # Export uv packages
    uv pip freeze > requirements-uv.txt
    log_success "uv packages exported to requirements-uv.txt"
    
    # Create combined requirements for pip fallback
    pip freeze > requirements-all.txt
    log_success "All packages exported to requirements-all.txt"
}

# Test the installation
test_installation() {
    log_info "Testing installation..."
    
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
    
    # Test CUDA if available
    if torch.cuda.is_available():
        print(f'CUDA available: True')
        print(f'CUDA device: {torch.cuda.get_device_name()}')
        print(f'CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')
    else:
        print('CUDA available: False (CPU-only mode)')
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

print()
print('✅ All packages imported successfully')
" || {
        log_error "Package import test failed"
        return 1
    }
    
    log_success "Installation test completed successfully"
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
        log_success "No significant package conflicts detected"
    fi
    
    # Cleanup
    rm -rf "$TEMP_DIR"
}

# Setup aliases and environment activation
setup_aliases() {
    log_info "Setting up convenient aliases..."
    
    # Create activation script
    cat > ~/activate_aiml.sh << 'EOF'
#!/bin/bash
export PATH="$HOME/miniconda3/bin:$PATH"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate aiml-hybrid
echo "🚀 AI/ML hybrid environment activated"
echo "📦 Conda packages: $(conda list | wc -l) packages"
echo "⚡ uv packages: $(uv pip list | tail -n +3 | wc -l) packages"
EOF
    chmod +x ~/activate_aiml.sh
    
    # Add aliases to bashrc
    if ! grep -q "# uv+conda aliases" ~/.bashrc; then
        cat >> ~/.bashrc << 'EOF'

# uv+conda aliases
alias aiml='source ~/activate_aiml.sh'
alias conda-export='conda env export > environment.yml'
alias uv-export='uv pip freeze > requirements-uv.txt'
alias check-conflicts='comm -12 <(conda list | awk "{print \$1}" | sort) <(uv pip list | tail -n +3 | awk "{print \$1}" | sort)'
EOF
        log_success "Aliases added to ~/.bashrc"
    fi
}

# Main installation function
main() {
    log_info "Starting uv + Conda hybrid installation..."
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
    log_success "🎉 uv + Conda hybrid environment setup complete"
    echo
    echo "Next steps:"
    echo "1. Activate the environment:"
    echo "   source ~/activate_aiml.sh"
    echo "   # or just: aiml"
    echo
    echo "2. Test the installation:"
    echo "   python -c 'import torch; print(torch.cuda.is_available())'"
    echo
    echo "3. Environment files created:"
    echo "   - environment.yml (conda packages)"
    echo "   - requirements-uv.txt (uv packages)"  
    echo "   - requirements-all.txt (all packages)"
    echo
    echo "4. Useful aliases:"
    echo "   - aiml: activate environment"
    echo "   - conda-export: export conda packages"
    echo "   - uv-export: export uv packages"
    echo "   - check-conflicts: find overlapping packages"
}

# Run main function
main "$@"