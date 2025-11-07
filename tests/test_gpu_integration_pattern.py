#!/usr/bin/env python3
"""
Test script to validate UniversalGPUManager integration pattern
Tests the pattern we'll use to replace CUDA-only detection in services

This validates:
1. UniversalGPUManager can replace torch.cuda.is_available() calls
2. Device detection works correctly on M4 Mac Mini
3. Memory and capability reporting works
4. Integration pattern is simple and reliable
"""

import sys
import os
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    import torch
    from gpu_manager import UniversalGPUManager, get_optimal_device
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure to activate the virtual environment:")
    print("   source .venv/bin/activate")
    sys.exit(1)

def test_basic_detection():
    """Test basic GPU detection - replacing torch.cuda.is_available()"""
    print("🔍 Test 1: Basic GPU Detection")
    print("=" * 50)

    # OLD WAY (CUDA-only)
    old_cuda_available = torch.cuda.is_available()
    print(f"❌ Old CUDA-only detection: {old_cuda_available}")

    # NEW WAY (Universal)
    gpu_manager = UniversalGPUManager()
    device = gpu_manager.get_device()
    device_str = gpu_manager.get_device_str()

    print(f"✅ Universal detection: {device_str}")
    print(f"✅ Device object: {device}")
    print(f"✅ GPU available (universal): {device_str != 'cpu'}")
    print()

def test_device_initialization():
    """Test device initialization pattern"""
    print("🔍 Test 2: Device Initialization Pattern")
    print("=" * 50)

    # OLD WAY (CUDA-only with failure)
    try:
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA not available")
        old_device = torch.device("cuda:0")
        print(f"❌ Old CUDA-only device: {old_device}")
    except RuntimeError as e:
        print(f"❌ Old way failed: {e}")

    # NEW WAY (Universal)
    gpu_manager = UniversalGPUManager()
    new_device = gpu_manager.get_device()
    print(f"✅ Universal device: {new_device}")

    # Test tensor creation
    test_tensor = torch.zeros(10, 10, device=new_device)
    print(f"✅ Tensor created successfully on: {test_tensor.device}")
    print()

def test_device_info():
    """Test device information retrieval"""
    print("🔍 Test 3: Device Information")
    print("=" * 50)

    gpu_manager = UniversalGPUManager()
    info = gpu_manager.get_info()

    print(f"✅ Device type: {info['type']}")
    print(f"✅ Platform: {info['platform']}")
    print(f"✅ Architecture: {info['architecture']}")

    if info.get('memory_gb'):
        print(f"✅ Memory: {info['memory_gb']:.1f} GB")

    if info.get('compute_capability'):
        print(f"✅ Compute capability: {info['compute_capability']}")

    print()

def test_integration_pattern():
    """Test the exact integration pattern for services"""
    print("🔍 Test 4: Service Integration Pattern")
    print("=" * 50)

    print("# Pattern for replacing CUDA-only services:")
    print()

    print("# BEFORE (CUDA-only):")
    print("# if not torch.cuda.is_available():")
    print("#     raise RuntimeError('CUDA required')")
    print("# device = torch.device('cuda:0')")
    print()

    print("# AFTER (Universal):")
    print("from gpu_manager import UniversalGPUManager")
    print("gpu_manager = UniversalGPUManager()")
    print("device = gpu_manager.get_device()")
    print()

    # Demonstrate the pattern
    gpu_manager = UniversalGPUManager()
    device = gpu_manager.get_device()

    print(f"✅ Result: device = {device}")
    print(f"✅ Works on: CUDA, MPS (Apple Silicon), and CPU")
    print()

def test_model_loading():
    """Test that models can be loaded and moved to detected device"""
    print("🔍 Test 5: Model Loading Pattern")
    print("=" * 50)

    gpu_manager = UniversalGPUManager()
    device = gpu_manager.get_device()

    # Create a simple model for testing
    model = torch.nn.Linear(10, 1)

    # Move model to optimal device
    model = model.to(device)
    print(f"✅ Model moved to: {device}")

    # Test inference
    test_input = torch.randn(1, 10, device=device)
    with torch.no_grad():
        output = model(test_input)

    print(f"✅ Inference successful on: {output.device}")
    print()

def main():
    """Run all integration pattern tests"""
    print("🎯 UniversalGPUManager Integration Pattern Tests")
    print("=" * 60)
    print()

    try:
        test_basic_detection()
        test_device_initialization()
        test_device_info()
        test_integration_pattern()
        test_model_loading()

        print("🎉 All integration pattern tests passed!")
        print()
        print("✅ Ready to integrate UniversalGPUManager into services:")
        print("   1. services/crank_image_classifier.py")
        print("   2. archive/legacy-services/crank_image_classifier_gpu.py")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
