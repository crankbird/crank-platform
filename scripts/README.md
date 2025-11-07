# Universal GPU Dependency Automation

## Quick Start

```bash
# 1. Install all dependencies for GPU services
./scripts/install-gpu-dependencies.sh

# 2. Validate dependencies before development
python scripts/check-service-dependencies.py crank_image_classifier

# 3. Develop with confidence - dependencies are handled!
```

## What This Solves

During **Issue #20** (UniversalGPUManager integration), we encountered several dependency-related failures that blocked development:

- ❌ **Silent Import Failures**: Service imported but GPU detection failed
- ❌ **Missing ML Libraries**: `ultralytics`, `GPUtil` needed manual installation
- ❌ **Manual Resolution**: Step-by-step dependency hunting during integration
- ❌ **Platform Differences**: PyTorch installation varies between Apple Silicon and NVIDIA

## Automation Components

### 1. Installation Script
**File**: `scripts/install-gpu-dependencies.sh`
- ✅ **Platform Detection**: Automatically installs correct PyTorch for your hardware
- ✅ **Fast Installation**: Uses `uv` when available (10-50x faster than pip)
- ✅ **Comprehensive**: Installs all ML libraries needed for UniversalGPUManager
- ✅ **Validation**: Tests imports and GPU detection after installation

### 2. Dependency Checker
**File**: `scripts/check-service-dependencies.py`
- ✅ **Pre-Development**: Validate dependencies before starting work
- ✅ **Service-Specific**: Checks exactly what each service needs
- ✅ **Clear Feedback**: Shows what's missing and how to install it
- ✅ **Automation Ready**: Can be used in CI/CD or service startup

### 3. Unified Requirements
**File**: `services/requirements-universal-gpu.txt`
- ✅ **Comprehensive**: All dependencies for universal GPU services
- ✅ **Version Pinned**: Tested versions that work together
- ✅ **Cross-Platform**: Works with both MPS (Apple) and CUDA (NVIDIA)

## Real-World Usage

### Before Service Integration
```bash
# Ensure environment is ready
./scripts/install-gpu-dependencies.sh
```

### During Development
```bash
# Check what's needed for your service
python scripts/check-service-dependencies.py crank_image_classifier

# If something is missing, install just what you need
uv pip install ultralytics GPUtil opencv-python

# Validate the fix
python scripts/check-service-dependencies.py crank_image_classifier
```

### In Service Startup Scripts
```bash
# Fail fast if dependencies aren't ready
python scripts/check-service-dependencies.py crank_image_classifier && python services/crank_image_classifier.py
```

## Success Metrics

With this automation, the **Issue #20 integration process** changes from:

**❌ Before (Manual & Error-Prone)**:
1. Try to import service → Silent failure
2. Debug import issues → Missing ultralytics
3. Install manually → uv pip install ultralytics
4. Try again → Missing GPUtil
5. Install manually → uv pip install GPUtil
6. Try again → Finally works!

**✅ After (Automated & Reliable)**:
1. Run `./scripts/install-gpu-dependencies.sh` → All dependencies installed
2. Validate with checker → All green ✅
3. Integrate UniversalGPUManager → Works immediately! 🚀

## Integration Pattern

The automation ensures this pattern works reliably:

```python
# In services/crank_image_classifier.py
try:
    import torch
    import torchvision.transforms as transforms
    from ultralytics import YOLO
    import GPUtil

    # UniversalGPUManager integration
    from gpu_manager import UniversalGPUManager
    gpu_manager = UniversalGPUManager()
    GPU_AVAILABLE = gpu_manager.get_device_str() != 'cpu'
    GPU_DEVICE = gpu_manager.get_device()
    GPU_INFO = gpu_manager.get_info()

except ImportError:
    # This should now be rare with proper automation
    GPU_AVAILABLE = False
    GPU_DEVICE = None
    GPU_INFO = {'type': 'CPU', 'platform': 'Unknown'}
```

## Validation Results

✅ **Tested on M4 Mac Mini**:
```
🎯 SUCCESS: UniversalGPUManager Integration Complete!
   ✅ M4 Mac Mini MPS GPU properly detected
   ✅ Service upgraded from CUDA-only to universal GPU support
   ✅ Issue #20 integration pattern proven successful
   ✅ All ML dependencies installed and working
```

This automation prevents the dependency resolution issues we encountered and ensures reliable UniversalGPUManager integration across all GPU services.
