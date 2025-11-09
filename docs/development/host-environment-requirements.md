# Host Environment Requirements for Universal GPU Containers

> **⚠️ JEMM Violation Notice**: This document defines host-level dependencies that violate the "minimal host dependencies" principle. This is temporary technical debt and should be extracted to [`crank-infrastructure`](https://github.com/crankbird/crank-infrastructure) repository when that layer matures.
>
> **Extraction Tracking**: See Issue #26 for migration planning.

## Philosophy: Minimal Host, Maximum Container

The platform follows a **container-first development philosophy** where:

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

The platform includes a comprehensive validation script to check all host requirements:

**Script**: [`scripts/validate-host-environment.sh`](../../scripts/validate-host-environment.sh)

**Usage**:

```bash
# Run validation

./scripts/validate-host-environment.sh

# Example output for M4 Mac Mini

# ✅ Docker: Docker version 24.0.7

# ✅ Docker Compose: Docker Compose version 2.23.0

# 🍎 Apple Silicon detected - checking Metal/MPS support...

# ✅ Apple Silicon GPU runtime ready

# ✅ uv: uv 0.1.23

# 🎉 Host environment validation complete!

```

**What it validates**:

- Docker and Docker Compose installation

- Platform-specific GPU runtime (NVIDIA Container Toolkit, Apple Silicon Metal)

- uv package manager availability

- GPU container access validation

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

# Validates and configures

# - Docker with GPU support

# - Platform-specific optimizations

# - Host environment validation

```

### 3. Platform-Specific Modules

```text
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
