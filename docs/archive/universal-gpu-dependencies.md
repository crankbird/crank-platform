# Universal GPU Service Dependencies

## Overview

This document provides automated dependency installation for Universal GPU services, specifically addressing the dependency resolution issues encountered during Issue #20 (UniversalGPUManager integration).

## Problem Statement

During the integration of UniversalGPUManager with `services/crank_image_classifier.py`, we encountered several dependency-related failures:

1. **Silent Import Failures**: Service imports succeeded but GPU detection failed due to missing ML libraries

2. **Missing Core Dependencies**: `ultralytics`, `GPUtil` required for full GPU functionality

3. **Manual Resolution Required**: Dependencies had to be installed step-by-step during integration

4. **No Automation**: No automated way to install service-specific GPU dependencies

## Dependency Categories

### Core PyTorch (Required for UniversalGPUManager)

- `torch>=2.0.0` with MPS support (Apple Silicon) or CUDA support (NVIDIA)

- `torchvision>=0.15.0`

- `torchaudio>=2.0.0` (if audio processing needed)

### ML Libraries (Required for GPU Services)

- `ultralytics>=8.0.0` (YOLOv8 object detection)

- `GPUtil>=1.4.0` (GPU monitoring and stats)

- `opencv-python>=4.8.0` (Computer vision)

### System Dependencies (Required for Memory Monitoring)

- `psutil>=5.9.0` (System memory info for MPS)

## Installation Scripts

### 1. Universal GPU Dependencies Script

**File**: `scripts/install-gpu-dependencies.sh`

```bash
#!/bin/bash

# install-gpu-dependencies.sh

# Automated installation of Universal GPU service dependencies

set -e

echo "🔧 Installing Universal GPU Service Dependencies"
echo "=============================================="

# Activate virtual environment if it exists

if [ -f ".venv/bin/activate" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# Check for uv vs pip

if command -v uv &> /dev/null; then
    INSTALLER="uv pip"
    echo "⚡ Using uv for fast installation"
else
    INSTALLER="pip"
    echo "🐌 Using pip (consider installing uv for speed)"
fi

echo ""
echo "1️⃣ Installing Core PyTorch Dependencies..."
echo "----------------------------------------"

# PyTorch installation with platform detection

if [[ "$(uname)" == "Darwin" ]] && [[ "$(uname -m)" == "arm64" ]]; then
    echo "🍎 Apple Silicon detected - installing MPS-compatible PyTorch"
    $INSTALLER install torch torchvision torchaudio
elif command -v nvidia-smi &> /dev/null; then
    echo "🎮 NVIDIA GPU detected - installing CUDA PyTorch"
    $INSTALLER install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
else
    echo "💻 CPU-only installation"
    $INSTALLER install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

echo ""
echo "2️⃣ Installing ML and GPU Libraries..."
echo "------------------------------------"

$INSTALLER install \
    ultralytics \
    GPUtil \
    opencv-python \
    psutil \
    pillow \
    numpy

echo ""
echo "3️⃣ Validating Installation..."
echo "----------------------------"

python3 -c "
import sys
import torch

print(f'✅ PyTorch {torch.__version__} imported successfully')

# Test GPU detection

if torch.cuda.is_available():
    print(f'🎮 CUDA available: {torch.cuda.device_count()} GPU(s)')
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    print(f'🍎 Metal Performance Shaders (MPS) available')
else:
    print(f'💻 CPU-only mode')

# Test ML library imports

try:
    from ultralytics import YOLO
    print('✅ ultralytics imported successfully')
except ImportError as e:
    print(f'❌ ultralytics import failed: {e}')
    sys.exit(1)

try:
    import GPUtil
    print('✅ GPUtil imported successfully')
except ImportError as e:
    print(f'❌ GPUtil import failed: {e}')
    sys.exit(1)

try:
    import cv2
    print('✅ opencv-python imported successfully')
except ImportError as e:
    print(f'❌ opencv-python import failed: {e}')
    sys.exit(1)

print('')
print('🎯 All dependencies installed and validated!')
"

echo ""
echo "✅ Universal GPU dependencies installed successfully!"
echo "🚀 Ready for UniversalGPUManager integration"

```

### 2. Service-Specific Dependency Checker

**File**: `scripts/check-service-dependencies.py`

```python
#!/usr/bin/env python3

"""
Service Dependency Checker

Validates that all required dependencies are available before service startup.
Prevents silent failures from missing GPU libraries.
"""

import sys
import importlib
from pathlib import Path
from typing import Dict, List, Optional

def check_dependency(package: str, import_name: Optional[str] = None) -> bool:
    """Check if a package can be imported"""
    try:
        module_name = import_name or package
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def get_service_dependencies(service_name: str) -> Dict[str, List[str]]:
    """Get required dependencies for a service"""

    dependencies = {
        "crank_image_classifier": [
            "torch",
            "torchvision",
            "ultralytics",
            "cv2:opencv-python",
            "GPUtil",
            "psutil",
            "PIL:Pillow"
        ],
        "universal_gpu_base": [
            "torch",
            "psutil"
        ]
    }

    return dependencies.get(service_name, [])

def validate_service_dependencies(service_name: str) -> bool:
    """Validate all dependencies for a service"""

    print(f"🔍 Checking dependencies for {service_name}")
    print("=" * 50)

    dependencies = get_service_dependencies(service_name)
    if not dependencies:
        print(f"⚠️  No dependency requirements defined for {service_name}")
        return True

    missing = []
    available = []

    for dep in dependencies:
        if ":" in dep:
            import_name, package_name = dep.split(":")
        else:
            import_name, package_name = dep, dep

        if check_dependency(package_name, import_name):
            available.append(f"✅ {package_name}")
        else:
            missing.append(f"❌ {package_name} (import: {import_name})")

    # Report results

    if available:
        print("Available dependencies:")
        for dep in available:
            print(f"  {dep}")

    if missing:
        print(f"\nMissing dependencies:")
        for dep in missing:
            print(f"  {dep}")

        print(f"\n🔧 Install missing dependencies:")
        print(f"   cd /path/to/crank-platform")
        print(f"   source .venv/bin/activate")
        print(f"   ./scripts/install-gpu-dependencies.sh")

        return False

    print(f"\n🎯 All dependencies satisfied for {service_name}!")
    return True

def main():
    """Main dependency checker"""

    if len(sys.argv) < 2:
        print("Usage: python check-service-dependencies.py <service_name>")
        print("Examples:")
        print("  python check-service-dependencies.py crank_image_classifier")
        print("  python check-service-dependencies.py universal_gpu_base")
        sys.exit(1)

    service_name = sys.argv[1]

    if validate_service_dependencies(service_name):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

```

## Usage Examples

### Before Service Development

```bash
# Install all GPU dependencies

./scripts/install-gpu-dependencies.sh

# Validate dependencies before starting work

python scripts/check-service-dependencies.py crank_image_classifier

```

### During Service Integration

```bash
# Check what's missing

python scripts/check-service-dependencies.py crank_image_classifier

# Install only what's needed

uv pip install ultralytics GPUtil opencv-python

# Validate the fix

python scripts/check-service-dependencies.py crank_image_classifier

```

### Before Service Startup

```bash
# Automated check in service startup

python scripts/check-service-dependencies.py crank_image_classifier && python services/crank_image_classifier.py

```

## Integration with UniversalGPUManager

The dependency automation ensures that when `UniversalGPUManager` is integrated into services:

1. **All required ML libraries are available** for full GPU detection

2. **Import failures are prevented** by pre-installation validation

3. **Silent fallbacks are avoided** by explicit dependency checking

4. **Cross-platform support** works with PyTorch MPS/CUDA detection

### Expected Integration Pattern

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
    # Fallback mode - should be rare with automation

    GPU_AVAILABLE = False
    GPU_DEVICE = None
    GPU_INFO = {'type': 'CPU', 'platform': 'Unknown'}
    logger.warning("GPU libraries not available - running in CPU mode")

```

## Lessons Learned

1. **Validate Early**: Check dependencies before service integration, not during

2. **Automate Installation**: Manual step-by-step installation leads to errors

3. **Platform Detection**: PyTorch installation varies significantly between platforms

4. **Service-Specific**: Different services need different ML library subsets

5. **Silent Failures**: Import errors can cause services to start in degraded mode

This automation prevents the dependency resolution issues we encountered during Issue #20 and ensures reliable UniversalGPUManager integration across all GPU services.
