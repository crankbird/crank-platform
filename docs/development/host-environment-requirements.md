# Host Environment Requirements for Universal GPU Containers

> **⚠️ JEMM Violation Notice**: This document defines host-level dependencies that violate the "minimal host dependencies" principle. This is temporary technical debt and should be extracted to [`crank-infrastructure`](https://github.com/crankbird/crank-infrastructure) repository when that layer matures.
>
> **Extraction Tracking**: See Issue #26 for migration planning.

## Philosophy: Minimal Host, Maximum Container

The Crank Platform follows a **container-first development philosophy** where:
- **Host environment**: Only essential tooling for container orchestration
- **Development environment**: Lives entirely within containers
- **GPU abstraction**: Runtime detection within containers, not host configuration

## Required Host Dependencies

### 1. Container Runtime
**Requirement**: Docker or Podman with compose support
**Rationale**: Universal container orchestration

```bash
# Validation
docker --version
docker compose version
```

### 2. GPU Runtime Support (Platform-Specific)

#### Apple Silicon (M4 Mac Mini)
**Requirement**: Docker Desktop with Apple Silicon GPU passthrough
**Configuration**: None required - Metal/MPS handled by container runtime

```bash
# Validation
docker run --rm pytorch/pytorch:latest python -c "import torch; print(f'MPS: {torch.backends.mps.is_available()}')"
```

#### NVIDIA GPU Systems
**Requirement**: NVIDIA Container Toolkit
**Configuration**: GPU device passthrough for Docker

```bash
# Installation (Ubuntu/Debian)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Validation
docker run --rm --gpus all nvidia/cuda:12.1-runtime-ubuntu22.04 nvidia-smi
```

#### CPU-Only Systems
**Requirement**: Standard Docker installation
**Configuration**: None required

### 3. Package Manager
**Requirement**: uv (for any host-level tooling)
**Rationale**: Consistency with container tooling

```bash
# Installation
curl -LsSf https://astral.sh/uv/install.sh | sh

# Validation
uv --version
```

## Host Environment Validation Script

```bash
#!/bin/bash
# validate-host-environment.sh
# Validates minimal host requirements for universal GPU containers

set -e

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
    echo "🍎 Apple Silicon detected - checking Metal/MPS support..."

    if docker run --rm python:3.11-slim python -c "
import platform
import subprocess
import sys
print(f'Platform: {platform.machine()}')
print(f'Python: {sys.version}')
try:
    # Test PyTorch MPS availability (will fail on CPU-only PyTorch)
    import torch
    print(f'PyTorch: {torch.__version__}')
    if hasattr(torch.backends, 'mps'):
        print(f'MPS Backend Available: {torch.backends.mps.is_available()}')
    else:
        print('MPS Backend: Not available (CPU-only PyTorch)')
except ImportError:
    print('PyTorch: Not installed in base image')
" 2>/dev/null; then
        echo "✅ Apple Silicon GPU runtime ready"
    else
        echo "⚠️  Apple Silicon detected but GPU testing failed"
        echo "   This is normal - GPU support tested in application containers"
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
```

## Container-First Development Workflow

### Development Environment Setup
```bash
# 1. Validate host environment
./scripts/validate-host-environment.sh

# 2. Start container-based development
./dev-universal.sh

# 3. GPU services automatically detect runtime capabilities
docker compose up gpu-classifier
```

### No Host Python Environment Required
- **❌ No conda/pip on host**
- **❌ No CUDA toolkit installation**
- **❌ No PyTorch host dependencies**
- **✅ Everything in containers**
- **✅ GPU detection at runtime**

## Extraction Plan for crank-infrastructure

When migrating this to the `crank-infrastructure` repository:

### 1. Files to Extract
- `scripts/validate-host-environment.sh` → `crank-infrastructure/scripts/`
- This documentation → `crank-infrastructure/docs/host-requirements.md`
- Platform-specific setup scripts → `crank-infrastructure/setup/`

### 2. Interface Design
```bash
# Future crank-infrastructure interface
cd ../crank-infrastructure
./setup.sh --environment gpu-development --platform mac-m4

# Validates and configures:
# - Docker with GPU support
# - Platform-specific optimizations
# - Host environment validation
```

### 3. Platform-Specific Modules
```
crank-infrastructure/
├── setup/
│   ├── macos-apple-silicon.sh      # M4 Mac Mini setup
│   ├── ubuntu-nvidia.sh            # NVIDIA GPU setup
│   ├── windows-wsl2.sh             # WSL2 + Docker Desktop
│   └── cloud-instances.sh          # AWS/Azure/GCP setup
└── validation/
    └── gpu-runtime-test.sh         # Universal GPU validation
```

## Why This is Technical Debt

This host environment complexity violates **JEMM principles**:
- **Monolith-first**: Should be in main platform until extraction is justified
- **Just enough**: Adding infrastructure complexity before it's needed
- **Premature optimization**: Separating concerns before constraints are clear

**Resolution**: Track extraction with Issue #26 and extract when:
1. Multiple repositories need the same host setup
2. Team size justifies infrastructure specialization  
3. Host environment complexity reaches maintainability threshold

---

**Next Action**: Move this to `crank-infrastructure` when infrastructure layer justification becomes clear, not before.
