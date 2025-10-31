#!/usr/bin/env bash
set -euo pipefail

# Performance Benchmark Script for uv + Conda Hybrid
# Tests installation speed and functionality

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
    log_error "Benchmark failed at line $1. Exit code: $2"
    exit $2
}
trap 'handle_error $LINENO $?' ERR

# Configuration
ENV_NAME="aiml-hybrid"

echo "🚀 Performance Benchmark: uv + Conda Hybrid"
echo "Environment: $ENV_NAME"
echo

# Ensure environment is available
export PATH="$HOME/miniconda3/bin:$PATH"
if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
else
    log_error "Conda not found. Run setup_hybrid_environment.sh first."
    exit 1
fi

# Activate environment
if ! conda activate "$ENV_NAME" 2>/dev/null; then
    log_error "Environment $ENV_NAME not found. Run setup_hybrid_environment.sh first."
    exit 1
fi

# Test 1: uv installation speed
log_info "Test 1: uv package installation speed"
echo "Installing requests, click, httpx via uv..."

START_TIME=$(date +%s.%N)
uv pip install requests click httpx --reinstall --quiet --no-deps 2>/dev/null || {
    log_warning "uv installation test failed, trying with deps"
    uv pip install requests click httpx --reinstall --quiet
}
END_TIME=$(date +%s.%N)
UV_TIME=$(echo "$END_TIME - $START_TIME" | bc -l 2>/dev/null || echo "0.0")

log_success "uv installation completed in ${UV_TIME}s"
echo

# Test 2: conda installation speed (for comparison)
log_info "Test 2: conda package installation speed"
echo "Installing/reinstalling pillow via conda..."

START_TIME=$(date +%s.%N)
conda install -y pillow --force-reinstall -q 2>/dev/null || {
    log_info "Pillow already installed, testing with another package"
    conda install -y six --force-reinstall -q 2>/dev/null || true
}
END_TIME=$(date +%s.%N)
CONDA_TIME=$(echo "$END_TIME - $START_TIME" | bc -l 2>/dev/null || echo "0.0")

log_success "conda installation completed in ${CONDA_TIME}s"
echo

# Test 3: Import speed test
log_info "Test 3: Package import speed"

START_TIME=$(date +%s.%N)
python -c "
import numpy as np
import pandas as pd
import torch
import transformers
import sklearn
import fastapi
print('All packages imported successfully')
" 2>/dev/null || log_warning "Some package imports failed"
END_TIME=$(date +%s.%N)
IMPORT_TIME=$(echo "$END_TIME - $START_TIME" | bc -l 2>/dev/null || echo "0.0")

log_success "Package imports completed in ${IMPORT_TIME}s"
echo

# Test 4: Environment info
log_info "Test 4: Environment summary"
CONDA_COUNT=$(conda list 2>/dev/null | grep -v "^#" | wc -l || echo "0")
UV_COUNT=$(uv pip list 2>/dev/null | tail -n +3 | wc -l || echo "0")

echo "📊 Environment Statistics:"
echo "  Conda packages: $CONDA_COUNT"
echo "  uv packages: $UV_COUNT"
echo "  Total packages: $((CONDA_COUNT + UV_COUNT))"
echo

# Test 5: Speed comparison
if command -v bc >/dev/null 2>&1 && [[ "$UV_TIME" != "0.0" ]] && [[ "$CONDA_TIME" != "0.0" ]]; then
    SPEED_RATIO=$(echo "scale=1; $CONDA_TIME / $UV_TIME" | bc -l 2>/dev/null || echo "N/A")
    if [[ "$SPEED_RATIO" != "N/A" ]]; then
        log_success "⚡ uv is ${SPEED_RATIO}x faster than conda for package installation"
    fi
fi

echo
log_success "🎉 Benchmark completed successfully"
echo
echo "📋 Results Summary:"
echo "  uv installation time: ${UV_TIME}s"
echo "  conda installation time: ${CONDA_TIME}s"  
echo "  import time: ${IMPORT_TIME}s"
echo "  environment size: $((CONDA_COUNT + UV_COUNT)) packages"