# Development Environment Setup

**Status**: Active  
**Type**: Setup Guide  
**Last Updated**: 2025-11-10  
**Owner**: Platform Team  
**Purpose**: Unified guide for setting up development environments across all platforms

---

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/crankbird/crank-platform.git
cd crank-platform

# 2. Verify Docker is installed
docker --version
docker compose version

# 3. Run development environment
./dev-local.sh  # For local development
# OR
./dev-universal.sh  # For universal GPU development
```

## Philosophy: Container-First Development

The Crank Platform follows a **container-first development philosophy**:

- **Host environment**: Only essential tooling for container orchestration (Docker/Podman)
- **Development environment**: Lives entirely within containers
- **GPU abstraction**: Runtime detection within containers, not host configuration
- **Minimal host dependencies**: Aligns with JEMM principle

See `.vscode/AGENT_CONTEXT.md` for full architectural context.

## Platform-Specific Setup

### macOS (Apple Silicon)

**Requirements**:
- Docker Desktop 4.0+ (includes Apple Silicon support)
- Xcode Command Line Tools (for git)

```bash
# Install Docker Desktop
brew install --cask docker

# Install UV for Python package management
curl -LsSf https://astral.sh/uv/install.sh | sh

# Start development
./dev-universal.sh  # Uses MPS (Metal Performance Shaders) for GPU
```

**GPU Support**: Automatic MPS (Metal Performance Shaders) detection for Apple Silicon GPUs.

See [mac-mini-development-strategy.md](mac-mini-development-strategy.md) for detailed Mac Mini setup.

### Linux (NVIDIA GPU)

**Requirements**:
- Docker Engine 20.10+
- NVIDIA Container Toolkit (for GPU support)

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Start development
./dev-universal.sh  # Detects CUDA automatically
```

**GPU Support**: Automatic CUDA detection for NVIDIA GPUs.

### Windows (WSL2)

**Requirements**:
- Windows 11 or Windows 10 (version 2004+)
- WSL2 enabled
- Docker Desktop for Windows

```bash
# Enable WSL2 (PowerShell as Administrator)
wsl --install

# Install Docker Desktop for Windows
# Download from https://www.docker.com/products/docker-desktop

# In WSL2 Ubuntu terminal
cd /mnt/c/Users/YourUsername/Projects
git clone https://github.com/crankbird/crank-platform.git
cd crank-platform

# Start development
./dev-local.sh
```

**GPU Support**: CUDA passthrough available via WSL2 + Docker Desktop integration.

See [WSL2-GPU-CUDA-COMPATIBILITY.md](WSL2-GPU-CUDA-COMPATIBILITY.md) for WSL2-specific GPU setup.

See [windows-agent-instructions.md](windows-agent-instructions.md) for Windows development details.

## Development Workflows

### Local CPU Development (No GPU)

Best for:
- Service development (FastAPI workers)
- Platform controller development
- Testing non-GPU features

```bash
./dev-local.sh
```

Services start on:
- Platform: https://localhost:8443
- Document Converter: https://localhost:8101
- Email Classifier: https://localhost:8201
- Email Parser: https://localhost:8301
- Streaming Service: https://localhost:8501

### Universal GPU Development

Best for:
- ML model development
- GPU-accelerated services
- Image classification
- Cross-platform GPU testing

```bash
./dev-universal.sh
```

Additional GPU services:
- Image Classifier (CPU): https://localhost:8401
- Image Classifier (GPU): https://localhost:8402

**GPU Detection**: Automatic runtime detection of CUDA (NVIDIA), MPS (Apple Silicon), or CPU fallback.

See [universal-gpu-environment.md](universal-gpu-environment.md) for GPU environment details.

### Hybrid Development (uv + conda)

For specialized ML development requiring both fast package management and conda-specific packages:

```bash
# Use uv for general dependencies (fast)
uv pip install fastapi uvicorn

# Use conda for ML-specific packages (comprehensive)
conda install pytorch torchvision -c pytorch
```

See [uv-conda-hybrid-strategy.md](uv-conda-hybrid-strategy.md) for hybrid workflow details.

## Development Tools

### Code Quality

All code quality tools are configured in `.vscode/settings.json`:

- **Linter**: Ruff (Python)
- **Type Checker**: Pylance (strict mode)
- **Formatter**: Ruff (auto-format on save)

See [code-quality-strategy.md](code-quality-strategy.md) for three-ring type safety architecture.

See [LINTING_AND_TYPE_CHECKING.md](LINTING_AND_TYPE_CHECKING.md) for linting configuration.

See [pylance-ml-configuration.md](pylance-ml-configuration.md) for ML-specific type checking.

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov-report=html

# Run specific test
pytest tests/test_platform.py::test_health_check
```

See [testing-strategy.md](testing-strategy.md) for testing architecture.

### Docker Configuration

See [DOCKER_CONFIGS.md](DOCKER_CONFIGS.md) for Docker Compose configuration details.

## Environment Variables

Required environment variables are defined in:
- `.env` (git-ignored, create from `.env.example`)
- `docker-compose.*.yml` files

Key variables:
```bash
# Certificate paths
CERT_PATH=/certs
CA_CERT_PATH=/certs/ca.crt

# Service ports
PLATFORM_PORT=8443
DOC_CONVERTER_PORT=8101
EMAIL_CLASSIFIER_PORT=8201

# GPU configuration (auto-detected)
PYTORCH_ENABLE_MPS_FALLBACK=1  # macOS only
CUDA_VISIBLE_DEVICES=0         # Linux NVIDIA
```

## Troubleshooting

### Certificate Issues

```bash
# Regenerate certificates
./scripts/generate-production-certs.sh

# Verify certificate permissions
ls -la certs/
# Should show worker:worker ownership
```

### GPU Not Detected

```bash
# Check GPU availability in container
docker run --rm --gpus all python:3.12-slim python -c "import torch; print(torch.cuda.is_available())"

# macOS: Check MPS
docker run --rm python:3.12-slim python -c "import torch; print(torch.backends.mps.is_available())"
```

See [universal-gpu-environment.md](universal-gpu-environment.md) for GPU troubleshooting.

### Port Conflicts

```bash
# Check what's using ports
lsof -i :8443  # macOS/Linux
netstat -ano | findstr :8443  # Windows

# Kill process on port
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### Docker Issues

```bash
# Reset Docker environment
docker compose down -v
docker system prune -a

# Rebuild all images
docker compose build --no-cache

# Check Docker logs
docker compose logs -f platform
```

## CI/CD Environment

GitHub Actions environments are defined in `.github/workflows/`:

- **security-scan.yml**: Trivy, gitleaks, hadolint, lockfile checks
- Tests run in Docker containers matching production environment
- GPU tests run on self-hosted runners with NVIDIA GPUs

See `.github/workflows/security-scan.yml` for CI configuration.

## Next Steps

After environment setup:

1. **Read architecture**: [docs/ARCHITECTURE.md](../ARCHITECTURE.md)
2. **Understand mascots**: [docs/ARCHITECTURAL_MENAGERIE_GUIDE.md](../ARCHITECTURAL_MENAGERIE_GUIDE.md)
3. **Review agent context**: `.vscode/AGENT_CONTEXT.md`
4. **Check security**: [docs/security/README.md](../security/README.md)
5. **Start developing**: Pick a service in `services/` and dive in!

## Related Documentation

- [code-quality-strategy.md](code-quality-strategy.md) — Three-ring type safety
- [testing-strategy.md](testing-strategy.md) — Testing architecture
- [ml-development-guide.md](ml-development-guide.md) — ML-specific development
- [error-suppression-strategy.md](error-suppression-strategy.md) — Error handling patterns
- [../security/README.md](../security/README.md) — Security architecture
- [../operations/DEPLOYMENT_STRATEGY.md](../operations/DEPLOYMENT_STRATEGY.md) — Production deployment
