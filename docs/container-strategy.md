# Container Strategy for Cross-Platform AI/ML Development

## Architecture Decision: Control Plane + Host Container Execution

After exploring WSL2 and virtualization approaches, we've settled on a clean separation:

### New Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Host Platform                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │ Docker Desktop  │  │ Docker Desktop  │  │ Cloud       │  │
│  │ (Windows)       │  │ (Mac)           │  │ Containers  │  │
│  │ GPU: CUDA       │  │ GPU: Metal      │  │ GPU: Various│  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              WSL2 Control Plane                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │ Orchestration   │  │ Deployment      │  │ Monitoring  │  │
│  │ Scripts         │  │ Automation      │  │ & Logging   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Benefits
- **Platform Agnostic**: Same containers work on Windows, Mac, Cloud
- **GPU Optimization**: Native Docker Desktop GPU support on each platform
- **Lightweight WSL**: Only automation and control logic, not heavy workloads
- **Migration Ready**: Easy movement between development environments

## Implementation Plan

### 1. WSL Control Plane Scripts
- `scripts/deploy-to-windows.sh` - Deploy containers to Windows Docker Desktop
- `scripts/deploy-to-mac.sh` - Deploy containers to Mac Docker Desktop  
- `scripts/deploy-to-cloud.sh` - Deploy to cloud container platforms
- `scripts/monitor-workloads.sh` - Monitor container status across platforms

### 2. Host Platform Containers
- **Windows**: Docker Desktop with CUDA support
- **Mac**: Docker Desktop with Metal Performance Shaders
- **Cloud**: Azure Container Apps, AWS ECS, Google Cloud Run

### 3. Development Workflow
```bash
# From WSL control plane
./scripts/deploy-to-windows.sh --gpu --service aiml-dev
./scripts/monitor-workloads.sh --platform windows
./scripts/deploy-to-cloud.sh --provider azure --region eastus
```

### 4. Cross-Platform Container Definitions
- `docker-compose.windows.yml` - Windows-specific GPU configuration
- `docker-compose.mac.yml` - Mac Metal GPU configuration  
- `docker-compose.cloud.yml` - Cloud provider configurations

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