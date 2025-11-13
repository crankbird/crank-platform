# Current Working Environment Baseline

## System Information

- Date: October 31, 2025

- OS: Ubuntu 22.04 (WSL2)

- Architecture: x86_64

- GPU: NVIDIA GeForce RTX 4070 Mobile (8GB VRAM)

## CUDA Installation

**Source**: NVIDIA apt repository
**Version**: CUDA 12.6
**Repository**: `https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64`

### CUDA Packages (42 total)

```
cuda-cccl-12-6                  12.6.77-1
cuda-command-line-tools-12-6    12.6.3-1  
cuda-compiler-12-6              12.6.3-1
cuda-crt-12-6                   12.6.85-1
cuda-cudart-12-6                12.6.77-1
cuda-cudart-dev-12-6            12.6.77-1
cuda-cuobjdump-12-6             12.6.77-1
cuda-cupti-12-6                 12.6.80-1
cuda-cupti-dev-12-6             12.6.80-1
cuda-cuxxfilt-12-6              12.6.77-1
cuda-documentation-12-6         12.6.77-1
cuda-driver-dev-12-6            12.6.77-1
cuda-gdb-12-6                   12.6.77-1
cuda-keyring                    1.1-1
cuda-libraries-12-6             12.6.3-1
cuda-libraries-dev-12-6         12.6.3-1
cuda-nsight-12-6                12.6.77-1
cuda-nsight-compute-12-6        12.6.3-1
cuda-nsight-systems-12-6        12.6.3-1
cuda-nvcc-12-6                  12.6.85-1
[... and 22 more packages]

```

## GPU Status

```
NVIDIA-SMI 580.102.01
Driver Version: 581.57
CUDA Version: 13.0
GPU: NVIDIA GeForce RTX 4070 Mobile
Memory: 339MiB / 8188MiB used

```

## Python Environment

**Current Status**: No conda installed, minimal uv environment
**Packages**: Only pip (25.2) and setuptools (80.9.0)
**Previous Setup**: Had conda + PyTorch, removed during troubleshooting

## Package Management History

1. **Original**: Ansible setup (interrupted/killed)

2. **Conda period**: Miniconda with PyTorch CUDA support

3. **Troubleshooting**: Removed conda due to uv/conda conflicts

4. **Current**: Pure uv approach with system CUDA

5. **Next**: Test hybrid uv+conda approach

## Environment Variables

- CUDA toolkit via apt provides system-wide CUDA

- No conda initialization in current shell

- PATH clean of conda references (miniconda removed)

## Testing Goal

Validate that hybrid approach (conda for system deps + uv for pure Python) provides:

1. Reproducible environment setup

2. Faster package installation than pure conda

3. Proper CUDA integration without conflicts

4. Clean separation of responsibilities
