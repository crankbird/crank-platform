# ADR-0021: Support macOS, Linux, and Windows (WSL) Local Development

**Status**: Accepted
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Developer Experience & CI/CD](../planning/adr-backlog-2025-11-16.md#developer-experience--ci-cd)

## Context and Problem Statement

Developers work on different platforms (macOS, Linux, Windows). The platform uses GPU workers, containers, native executables, and Python dependencies. How should we support diverse development environments while maintaining consistency?

## Decision Drivers

- Platform diversity: macOS, Linux, Windows developers
- GPU support: macOS Metal, NVIDIA CUDA, AMD ROCm
- Consistency: Same workflow across platforms
- Hybrid deployment: Containers + native (for GPU)
- Tool availability: uv, Docker, Python
- Developer experience: Easy setup

## Considered Options

- **Option 1**: Support macOS, Linux, Windows (WSL) with hybrid deployment - Accepted
- **Option 2**: Docker-only development (all platforms)
- **Option 3**: Native-only development (no containers)

## Decision Outcome

**Chosen option**: "macOS, Linux, Windows (WSL) with hybrid deployment", because it supports GPU acceleration on all platforms while maintaining containerization for CPU workers. macOS uses Metal natively, Linux/Windows use GPU passthrough in containers.

### Positive Consequences

- All platforms supported
- GPU acceleration everywhere
- Consistent development workflow
- Container portability for CPU workers
- Native performance for GPU workloads
- uv/conda handles Python dependencies

### Negative Consequences

- Platform-specific GPU setup (Metal vs CUDA/ROCm)
- WSL required for Windows (not native Windows)
- Hybrid deployment complexity
- Different paths for GPU workers

## Pros and Cons of the Options

### Option 1: macOS, Linux, Windows (WSL) with Hybrid Deployment

Support all platforms with containers + native GPU workers.

**Pros:**
- Universal support
- GPU acceleration
- Container portability
- Native GPU performance
- Consistent workflow

**Cons:**
- Platform-specific setup
- WSL requirement
- Hybrid complexity

### Option 2: Docker-Only Development

All development in containers.

**Pros:**
- Consistent environment
- Easy setup
- No platform differences

**Cons:**
- GPU passthrough complexity
- macOS Docker performance issues
- Limited Metal support in containers
- Slower development cycle

### Option 3: Native-Only Development

No containers, all native execution.

**Pros:**
- Fast development
- Direct GPU access
- Simple debugging

**Cons:**
- Environment inconsistencies
- Dependency conflicts
- No deployment parity
- Platform-specific bugs

## Links

- [Related to] ADR-0009 (Separate CPU/GPU workers)
- [Related to] ADR-0010 (Containers primary deployment)
- [Related to] ADR-0020 (Git-based CI pipelines)
- [Implements] `scripts/dev-universal.sh`
- [Implements] `docs/development/UNIVERSAL_GPU_ENVIRONMENT.md`

## Implementation Notes

**Platform Support Matrix**:

| Platform | CPU Workers | GPU Workers | GPU Tech | Container Runtime |
|----------|-------------|-------------|----------|-------------------|
| macOS (arm64) | Docker | Native | Metal | Docker Desktop |
| macOS (x64) | Docker | Native | Metal | Docker Desktop |
| Linux (x64) | Docker | Docker | CUDA/ROCm | Docker Engine |
| Windows (WSL2) | Docker | Docker | CUDA | Docker Desktop |

**Universal Setup Script**:

```bash
#!/usr/bin/env bash
# scripts/dev-universal.sh - Platform-agnostic setup

set -euo pipefail

detect_platform() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if grep -qi microsoft /proc/version 2>/dev/null; then
            echo "wsl"
        else
            echo "linux"
        fi
    else
        echo "unknown"
    fi
}

setup_python() {
    echo "Setting up Python environment..."

    # Install uv if missing
    if ! command -v uv &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi

    # Sync dependencies
    uv sync --all-extras

    # Editable install
    uv pip install -e .
}

setup_docker() {
    local platform=$1

    echo "Checking Docker..."

    if ! command -v docker &> /dev/null; then
        case $platform in
            macos)
                echo "Install Docker Desktop: https://www.docker.com/products/docker-desktop"
                ;;
            linux)
                echo "Installing Docker Engine..."
                curl -fsSL https://get.docker.com | sh
                sudo usermod -aG docker $USER
                ;;
            wsl)
                echo "Install Docker Desktop for Windows with WSL2 backend"
                ;;
        esac
        exit 1
    fi
}

setup_gpu() {
    local platform=$1

    case $platform in
        macos)
            echo "GPU: Metal (native) - No additional setup needed"
            ;;
        linux)
            echo "GPU: Checking for NVIDIA CUDA..."
            if command -v nvidia-smi &> /dev/null; then
                # Install nvidia-container-toolkit
                distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
                curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | \
                    sudo apt-key add -
                curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
                    sudo tee /etc/apt/sources.list.d/nvidia-docker.list
                sudo apt-get update
                sudo apt-get install -y nvidia-container-toolkit
                sudo systemctl restart docker
            else
                echo "No NVIDIA GPU detected, CPU-only mode"
            fi
            ;;
        wsl)
            echo "GPU: CUDA via WSL2 - Ensure NVIDIA drivers installed on Windows host"
            ;;
    esac
}

setup() {
    local platform=$(detect_platform)

    echo "Platform detected: $platform"

    setup_docker "$platform"
    setup_python
    setup_gpu "$platform"

    # Initialize certificates
    python scripts/initialize-certificates.py

    echo "Setup complete! Platform: $platform"
}

case "${1:-}" in
    setup) setup ;;
    platform) detect_platform ;;
    *) echo "Usage: $0 {setup|platform}"; exit 1 ;;
esac
```

**macOS GPU Development**:

```bash
# Run GPU workers natively (Metal)
make worker-install WORKER=image_classifier
make worker-run WORKER=image_classifier

# CPU workers in containers
docker-compose up streaming document_conversion
```

**Linux GPU Development**:

```bash
# All workers in containers (GPU passthrough)
docker-compose -f docker-compose.gpu-dev.yml up

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

**Windows (WSL2) Development**:

```powershell
# In PowerShell: Ensure WSL2 + Docker Desktop
wsl --install
wsl --set-default-version 2

# In WSL2 Ubuntu:
cd /mnt/c/Projects/crank-platform
./scripts/dev-universal.sh setup
docker-compose -f docker-compose.gpu-dev.yml up
```

**Platform-Specific Considerations**:

**macOS**:
- Metal for GPU (PyTorch MPS backend)
- Docker Desktop VM overhead
- Hybrid deployment recommended
- Native GPU workers for performance

**Linux**:
- CUDA/ROCm in containers via GPU passthrough
- Docker Engine (no VM overhead)
- All workers can be containerized
- Nvidia Container Toolkit required

**Windows (WSL2)**:
- WSL2 required (not native Windows Python)
- CUDA support via WSL2
- Docker Desktop with WSL2 backend
- GPU passthrough to containers

**Makefile Platform Detection**:

```makefile
# Detect platform
UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

ifeq ($(UNAME_S),Darwin)
    PLATFORM := macos
    GPU_MODE := native
endif
ifeq ($(UNAME_S),Linux)
    PLATFORM := linux
    GPU_MODE := docker
    # Check for WSL
    ifeq ($(shell grep -qi microsoft /proc/version && echo wsl),wsl)
        PLATFORM := wsl
    endif
endif

worker-gpu-run:  ## Run GPU worker (platform-aware)
ifeq ($(GPU_MODE),native)
 # macOS: Run natively
 python -m services.crank_$(WORKER)
else
 # Linux/WSL: Run in container with GPU
 docker run --rm --gpus all crank-$(WORKER):latest
endif
```

## Review History

- 2025-11-16 - Initial decision (formalizing existing multi-platform support)
