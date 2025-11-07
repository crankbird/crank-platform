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
- ✅ **Comprehensive**: Handles CUDA, CPU, and Apple Silicon MPS
- ✅ **Fast**: Uses `uv` for 10-100x faster dependency installation than pip

### 2. Dependency Checker

**File**: `scripts/check-service-dependencies.py`

- ✅ **Pre-Development**: Validate dependencies before starting work
- ✅ **CI Integration**: Use in build pipelines to catch missing dependencies
- ✅ **Clear Output**: Shows exactly what's missing and how to install it

### 3. Unified Requirements

**File**: `requirements-*.txt` files with automatic service detection

- ✅ **Comprehensive**: All dependencies for universal GPU services
- ✅ **Modular**: Separate requirements for different service types
- ✅ **Maintained**: Automatically updated when services change

## Real-World Usage

### Before Service Integration

```bash
# Ensure environment is ready
./scripts/install-gpu-dependencies.sh
```

### During Development

```bash
# Check dependencies before coding
python scripts/check-service-dependencies.py crank_image_classifier

# Your development here...

# Validate again before commit
python scripts/check-service-dependencies.py crank_image_classifier
```

### In Service Startup Scripts

```bash
# Pre-flight dependency check
python scripts/check-service-dependencies.py crank_image_classifier && python services/crank_image_classifier.py
```

## The Problem This Solves

**Before automation:**

1. Try to import service → Silent failure
2. Debug missing dependencies → Spend 30 minutes
3. Install dependencies manually → Hope you got them all
4. Try again → Different missing dependency
5. Repeat until it works → Hours of frustration

**After automation:**

1. Run `./scripts/install-gpu-dependencies.sh` → All dependencies installed
2. Import service → Works immediately
3. Focus on business logic → Productive development

## Implementation Details

The automation works by:

1. **Platform Detection**: Detects your hardware (CUDA, Apple Silicon, CPU)
2. **Smart Installation**: Installs only what you need for your platform
3. **Validation**: Checks that installation actually worked
4. **Fast Package Management**: Uses `uv` instead of `pip` for speed
5. **Service Integration**: Each service can validate its own dependencies

## Installation Script Details

```text
./scripts/install-gpu-dependencies.sh

1. Detect Platform:
   ├─ Apple Silicon → Install PyTorch with MPS support
   ├─ NVIDIA GPU → Install PyTorch with CUDA support
   └─ CPU Only → Install CPU-optimized PyTorch

2. Install Base Dependencies:
   ├─ FastAPI, uvicorn (web framework)
   ├─ httpx, requests (HTTP clients)
   ├─ Pillow, pandas (data processing)
   └─ Platform-specific ML libraries

3. Validate Installation:
   ├─ Test PyTorch import
   ├─ Test GPU/MPS availability (if applicable)
   └─ Report success/failure with next steps
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

```text
🎯 SUCCESS: UniversalGPUManager Integration Complete!
   ✅ M4 Mac Mini MPS GPU properly detected
   ✅ Service upgraded from CUDA-only to universal GPU support
   ✅ Issue #20 integration pattern proven successful
   ✅ All ML dependencies installed and working
```

This automation prevents the dependency resolution issues we encountered and ensures reliable UniversalGPUManager integration across all GPU services.
