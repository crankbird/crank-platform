# Windows Agent Instructions: WSL2 GPU Instance Creation

## Context
You are a Windows-side agent helping to create a fresh WSL2 Ubuntu instance for GPU-enabled hybrid package management testing. The Linux-side agent has created scripts but cannot directly debug Windows PowerShell/WSL2 issues.

## Current Situation
- Main development is in WSL2 Ubuntu-22.04 with RTX 4070 GPU
- Need to create a **completely fresh** WSL2 instance (`ubuntu-gpu-test`) from virgin Ubuntu 22.04 rootfs
- Goal: Test GPU-enabled hybrid package management (uv+conda) on clean environment
- Problem: Batch file downloads failing, need PowerShell expertise

## Mission Objectives

### Primary Goal
Create working automation to:
1. Download fresh Ubuntu 22.04 WSL rootfs (325MB file)
2. Import as new WSL2 instance named `ubuntu-gpu-test`
3. Basic setup (user account, GPU access test)
4. Copy and test GPU hybrid script from main instance

### Success Criteria
- Fresh WSL2 instance created from virgin Ubuntu rootfs (not cloned)
- GPU access working (`nvidia-smi` responds)
- Ready to receive and test `setup_hybrid_environment_gpu.sh`

## Technical Details

### Download Target
- **URL**: `https://cloud-images.ubuntu.com/wsl/jammy/current/ubuntu-jammy-wsl-amd64-ubuntu22.04lts.rootfs.tar.gz`
- **Expected Size**: ~325MB (341,000,000 bytes)
- **Format**: Compressed tar.gz Ubuntu rootfs

### WSL2 Import Command
```cmd
wsl --import ubuntu-gpu-test %LOCALAPPDATA%\WSL\ubuntu-gpu-test %TEMP%\ubuntu-fresh.tar.gz
```

### Known Issues with Current Scripts
1. PowerShell `Invoke-WebRequest` may be failing silently
2. File size checks might be too aggressive
3. Need better error diagnostics

## Available Resources

### Existing Script Files (in `/mnt/c/temp/`)
- `debug_wsl_setup.bat` - Most recent diagnostic version
- `simple_wsl_setup.bat` - Simplified version
- `create_fresh_wsl.bat` - Original complex version

### Target GPU Script (ready for testing)
- Location: `/home/johnr/projects/crank-platform/scripts/setup_hybrid_environment_gpu.sh`
- Features: CUDA PyTorch, cupy, nvidia-ml-py3, WSL2 optimizations
- Validated base version works on Azure VM (41x speed improvement)

## Recommended Approach

### Phase 1: Get Download Working
1. Test PowerShell download methods:
   - `Invoke-WebRequest` with detailed error handling
   - `curl` with verbose output
   - `wget` if available
2. Verify file integrity (size, format)
3. Create bulletproof download function

### Phase 2: WSL2 Instance Creation
1. Test WSL2 import process
2. Handle existing instance cleanup
3. Verify instance starts and runs

### Phase 3: Basic Setup
1. Create test user account
2. Install basic packages
3. Test GPU access (`nvidia-smi`)

### Phase 4: Script Transfer and Testing
1. Copy GPU script from main instance
2. Execute hybrid installation
3. Validate results

## PowerShell Best Practices
- Use `try/catch` blocks for error handling
- Enable verbose output for debugging
- Test network connectivity first
- Validate file downloads before proceeding
- Use proper WSL2 commands with error checking

## Success Metrics
- Clean WSL2 instance creation: ✅
- GPU detection working: ✅  
- Hybrid script execution: ✅
- All package imports successful: ✅
- Ready for production use: ✅

## Next Steps After Success
1. Document working process
2. Create production-ready automation
3. Test on second gaming laptop
4. Create graphite PR for WSL2 GPU support

## Communication
- Document all findings and working solutions
- Create reusable PowerShell functions
- Provide clear error messages and diagnostics
- Enable easy replication on other Windows machines

## Goal Alignment
This supports the broader strategy of:
- Multi-platform GPU development workflows
- Bleeding-edge ML package management
- Reproducible environment creation
- TypeOps elimination through automation

---

**Remember**: The Linux-side agent has already validated the hybrid approach on Azure VM with 41x speed improvement. This Windows work is about creating the foundation for GPU testing on clean WSL2 environments.