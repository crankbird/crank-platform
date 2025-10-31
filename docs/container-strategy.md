# Container Strategy for GPU Development

## Decision: Docker Desktop for Local GPU Development

After testing WSL2 GPU environments, we've decided to use Docker Desktop for local GPU development due to:

### Benefits
- **Simplified GPU Access**: Native `--gpus all` support
- **Clean Networking**: Predictable port mapping without virtualization complexity
- **Reproducible Environments**: Container isolation with consistent behavior
- **Production Alignment**: Same runtime as production deployments

### Architecture
```
Host (Windows/WSL2) → Docker Desktop → GPU-enabled Container
```

## Implementation Plan

### 1. Base Hybrid Environment (Validated)
- `setup_hybrid_environment.sh` - Production-ready hybrid package management
- Conda for system dependencies, uv for Python packages (41x speed improvement)
- Bash-safe output, proper error handling, TOS acceptance

### 2. Docker GPU Container
- Adapt `setup_hybrid_environment_gpu.sh` for container use
- Base image: `nvidia/cuda:12.2-devel-ubuntu22.04`
- NVIDIA Container Runtime for GPU access

### 3. Development Workflow
```bash
# Build GPU container
docker build -t aiml-hybrid-gpu .

# Run with GPU access
docker run --gpus all -p 8888:8888 -v $(pwd):/workspace aiml-hybrid-gpu

# Or use Docker Compose for complex setups
docker-compose up gpu-dev
```

## WSL2 Experiments (Archive)

### What Worked
- ✅ Fresh WSL2 instance creation via PowerShell
- ✅ Hybrid package installation (465 conda + 263 uv packages)
- ✅ nvidia-smi detection at `/usr/lib/wsl/lib/nvidia-smi`
- ✅ SSH access configuration

### What Was Complex
- ❌ Network IP address management (bridged vs mirrored)
- ❌ Custom SSH ports (2222) and connection issues
- ❌ WSL2-specific CUDA library paths
- ❌ PyTorch CUDA detection requiring custom environment variables

### Lessons Learned
- Virtualization layers add unnecessary complexity for development
- Docker Desktop provides better abstraction for GPU workloads
- Container isolation is preferable to VM/WSL2 combinations

## Next Steps
1. Archive WSL2 scripts as reference
2. Create Dockerfile based on validated hybrid scripts
3. Test Docker GPU workflow
4. Update dotfiles integration