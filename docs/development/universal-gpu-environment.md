# Universal GPU Development Environment

## The Problem

PyTorch CUDA installations often conflict between different package managers:

- **conda**: Bundles CUDA libraries, can conflict with system CUDA

- **pip**: Requires system CUDA installation, version mismatches common

- **uv**: Fast but limited CUDA wheel support

- **Apple Silicon**: Requires Metal Performance Shaders (MPS) backend

## Solution: Adaptive Environment Detection

### Environment Detection Script

```python
#!/usr/bin/env python3

"""
Universal GPU capability detection and PyTorch installation
Handles CUDA, MPS (Apple Silicon), and CPU-only environments
"""

import subprocess
import sys
import platform
import os
from pathlib import Path

def detect_gpu_environment():
    """Detect available GPU capabilities and return optimal PyTorch installation"""
    
    gpu_info = {
        "platform": platform.system(),
        "architecture": platform.machine(),
        "cuda_available": False,
        "cuda_version": None,
        "mps_available": False,
        "recommended_backend": "cpu",
        "install_command": []
    }
    
    # Check for Apple Silicon

    if gpu_info["platform"] == "Darwin" and "arm" in gpu_info["architecture"].lower():
        gpu_info["mps_available"] = True
        gpu_info["recommended_backend"] = "mps"
        gpu_info["install_command"] = [
            "pip", "install", "torch", "torchvision", "torchaudio"
        ]
        return gpu_info
    
    # Check for NVIDIA CUDA

    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        if result.returncode == 0:
            gpu_info["cuda_available"] = True
            
            # Extract CUDA version from nvidia-smi

            for line in result.stdout.split('\n'):
                if "CUDA Version:" in line:
                    cuda_version = line.split("CUDA Version: ")[1].split()[0]
                    gpu_info["cuda_version"] = cuda_version
                    break
            
            # Determine PyTorch CUDA version

            if gpu_info["cuda_version"]:
                major_version = gpu_info["cuda_version"].split('.')[0]
                if major_version == "12":
                    gpu_info["recommended_backend"] = "cuda121"
                    gpu_info["install_command"] = [
                        "pip", "install", "torch", "torchvision", "torchaudio",
                        "--index-url", "https://download.pytorch.org/whl/cu121"
                    ]
                elif major_version == "11":
                    gpu_info["recommended_backend"] = "cuda118"
                    gpu_info["install_command"] = [
                        "pip", "install", "torch", "torchvision", "torchaudio",
                        "--index-url", "https://download.pytorch.org/whl/cu118"
                    ]
    except FileNotFoundError:
        pass
    
    # Fallback to CPU

    if not gpu_info["cuda_available"] and not gpu_info["mps_available"]:
        gpu_info["recommended_backend"] = "cpu"
        gpu_info["install_command"] = [
            "pip", "install", "torch", "torchvision", "torchaudio",
            "--index-url", "https://download.pytorch.org/whl/cpu"
        ]
    
    return gpu_info

def install_pytorch_optimal():
    """Install PyTorch with optimal configuration for detected hardware"""
    
    print("🔍 Detecting GPU capabilities...")
    gpu_info = detect_gpu_environment()
    
    print(f"📋 Environment Detection Results:")
    print(f"   Platform: {gpu_info['platform']}")
    print(f"   Architecture: {gpu_info['architecture']}")
    print(f"   CUDA Available: {gpu_info['cuda_available']}")
    if gpu_info['cuda_version']:
        print(f"   CUDA Version: {gpu_info['cuda_version']}")
    print(f"   MPS Available: {gpu_info['mps_available']}")
    print(f"   Recommended Backend: {gpu_info['recommended_backend']}")
    
    print(f"\n🚀 Installing PyTorch for {gpu_info['recommended_backend']}...")
    print(f"Command: {' '.join(gpu_info['install_command'])}")
    
    # Execute installation

    result = subprocess.run(gpu_info['install_command'])
    
    if result.returncode == 0:
        print("✅ PyTorch installation successful!")
        return True
    else:
        print("❌ PyTorch installation failed!")
        return False

def verify_pytorch_installation():
    """Verify PyTorch installation and GPU availability"""
    
    try:
        import torch
        print(f"\n✅ PyTorch {torch.__version__} imported successfully")
        
        # Check CUDA

        if torch.cuda.is_available():
            print(f"🎮 CUDA available: {torch.cuda.device_count()} GPU(s)")
            for i in range(torch.cuda.device_count()):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
                print(f"   Memory: {torch.cuda.get_device_properties(i).total_memory / 1e9:.1f}GB")
        
        # Check MPS (Apple Silicon)

        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("🍎 Metal Performance Shaders (MPS) available")
        
        # Test tensor creation on optimal device

        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
            
        print(f"\n🧪 Testing tensor operations on {device}...")
        x = torch.randn(1000, 1000).to(device)
        y = torch.mm(x, x.t())
        print(f"✅ Matrix multiplication test passed on {device}")
        
        return True
        
    except ImportError as e:
        print(f"❌ PyTorch import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ PyTorch test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Universal GPU Development Environment Setup")
    print("=" * 50)
    
    if "--detect-only" in sys.argv:
        gpu_info = detect_gpu_environment()
        print(f"Detected backend: {gpu_info['recommended_backend']}")
        print(f"Install command: {' '.join(gpu_info['install_command'])}")
    elif "--verify-only" in sys.argv:
        verify_pytorch_installation()
    else:
        # Full setup

        if install_pytorch_optimal():
            verify_pytorch_installation()

```

### Smart Device Detection Class

```python
class UniversalGPUManager:
    """
    Manages GPU detection and optimal PyTorch device selection
    Works across CUDA, MPS, and CPU environments
    """
    
    def __init__(self):
        self.device_info = self._detect_optimal_device()
        self.device = self.device_info["device"]
        
    def _detect_optimal_device(self):
        """Detect and return optimal PyTorch device"""
        import torch
        
        device_info = {
            "device": "cpu",
            "type": "CPU",
            "memory": None,
            "compute_capability": None
        }
        
        # Check CUDA first (highest performance)

        if torch.cuda.is_available():
            device_info.update({
                "device": "cuda",
                "type": "NVIDIA CUDA",
                "memory": torch.cuda.get_device_properties(0).total_memory,
                "compute_capability": torch.cuda.get_device_capability(0)
            })
            
        # Check MPS (Apple Silicon)

        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            try:
                # Test MPS availability

                _ = torch.zeros(1).to('mps')
                device_info.update({
                    "device": "mps",
                    "type": "Apple Metal Performance Shaders",
                    "memory": None,  # Unified memory, queried differently
                    "compute_capability": "Apple Silicon"
                })
            except:
                # Fallback to CPU if MPS fails

                pass
                
        return device_info
    
    def get_device(self):
        """Return optimal PyTorch device"""
        return self.device
    
    def get_info(self):
        """Return device information"""
        return self.device_info
    
    def optimize_for_device(self, model):
        """Apply device-specific optimizations"""
        model = model.to(self.device)
        
        if self.device == "cuda":
            # CUDA optimizations

            model = torch.compile(model) if hasattr(torch, 'compile') else model
            
        elif self.device == "mps":
            # MPS optimizations

            # Use float16 for memory efficiency on unified memory

            if hasattr(model, 'half'):
                model = model.half()
                
        return model
    
    def get_memory_info(self):
        """Get memory information for current device"""
        if self.device == "cuda":
            return {
                "allocated": torch.cuda.memory_allocated(),
                "cached": torch.cuda.memory_reserved(),
                "total": torch.cuda.get_device_properties(0).total_memory
            }
        elif self.device == "mps":
            # For MPS, we can check system memory

            import psutil
            return {
                "allocated": None,  # Not directly available
                "cached": None,
                "total": psutil.virtual_memory().total
            }
        else:
            import psutil
            return {
                "allocated": None,
                "cached": None,
                "total": psutil.virtual_memory().total
            }

```

## Usage in Crank Platform

### Integration with Mesh Interface

```python
# In mesh_interface.py

from .gpu_manager import UniversalGPUManager

class MeshInterface:
    def __init__(self):
        self.gpu_manager = UniversalGPUManager()
        self.device = self.gpu_manager.get_device()
        
        print(f"🎮 Initialized with {self.gpu_manager.get_info()['type']}")
        
    def load_ai_model(self, model_path):
        """Load AI model with optimal device configuration"""
        model = torch.load(model_path, map_location='cpu')
        model = self.gpu_manager.optimize_for_device(model)
        return model

```

### Environment Setup Script

```bash
#!/bin/bash

# setup_universal_gpu_env.sh

echo "🔧 Setting up Universal GPU Development Environment"

# Detect environment

python3 gpu_detection.py --detect-only

# Install optimal PyTorch

python3 gpu_detection.py

# Verify installation

python3 gpu_detection.py --verify-only

echo "🎉 Environment setup complete!"

```

## Benefits of This Approach

### ✅ Advantages

- **Automatic detection** of optimal GPU backend

- **No manual configuration** across different machines

- **Consistent API** regardless of underlying hardware

- **Graceful fallbacks** when GPU unavailable

- **Package manager agnostic** (works with pip, conda, uv)

### 🎯 For Your Multi-Environment Strategy

```python
# Same code works everywhere

# RTX 4070 (CUDA) → Mac Mini M4 (MPS) → Raspberry Pi (CPU)

gpu_manager = UniversalGPUManager()
model = model.to(gpu_manager.get_device())  # Automatic optimal placement

```

This approach eliminates the CUDA/conda/uv conflicts by detecting capabilities first, then installing the appropriate PyTorch variant. Perfect for your multi-platform development strategy!
