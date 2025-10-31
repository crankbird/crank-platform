#!/usr/bin/env python3
"""
Universal GPU Detection and PyTorch Installation
Handles CUDA, MPS (Apple Silicon), and CPU-only environments
"""

import subprocess
import sys
import platform
import os
import json
from pathlib import Path

def run_command(cmd, capture=True):
    """Run command and return result"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def detect_gpu_environment():
    """Detect available GPU capabilities"""
    
    env_info = {
        "platform": platform.system(),
        "architecture": platform.machine(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "cuda_available": False,
        "cuda_version": None,
        "mps_available": False,
        "recommended_backend": "cpu",
        "install_commands": []
    }
    
    print(f"🔍 Detecting environment...")
    print(f"   Platform: {env_info['platform']}")
    print(f"   Architecture: {env_info['architecture']}")
    print(f"   Python: {env_info['python_version']}")
    
    # Check for Apple Silicon MPS
    if env_info["platform"] == "Darwin":
        if "arm" in env_info["architecture"].lower():
            env_info["mps_available"] = True
            env_info["recommended_backend"] = "mps"
            env_info["install_commands"] = [
                "pip install torch torchvision torchaudio"
            ]
            print("🍎 Apple Silicon detected - using MPS backend")
            return env_info
    
    # Check for NVIDIA CUDA
    cuda_success, cuda_output, cuda_error = run_command("nvidia-smi --query-gpu=driver_version,memory.total --format=csv,noheader,nounits")
    
    if cuda_success and cuda_output.strip():
        env_info["cuda_available"] = True
        print("🎮 NVIDIA GPU detected")
        
        # Get CUDA runtime version
        nvcc_success, nvcc_output, _ = run_command("nvcc --version")
        if nvcc_success:
            for line in nvcc_output.split('\n'):
                if "release" in line.lower():
                    version_part = line.split("release ")[1].split(",")[0]
                    env_info["cuda_version"] = version_part
                    break
        
        # If no nvcc, try to detect from nvidia-smi
        if not env_info["cuda_version"]:
            smi_success, smi_output, _ = run_command("nvidia-smi")
            if smi_success:
                for line in smi_output.split('\n'):
                    if "CUDA Version:" in line:
                        version = line.split("CUDA Version: ")[1].split()[0]
                        env_info["cuda_version"] = version
                        break
        
        # Determine PyTorch installation based on CUDA version
        if env_info["cuda_version"]:
            major_version = env_info["cuda_version"].split('.')[0]
            print(f"   CUDA Version: {env_info['cuda_version']}")
            
            if major_version == "12":
                env_info["recommended_backend"] = "cuda121"
                env_info["install_commands"] = [
                    "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
                ]
            elif major_version == "11":
                env_info["recommended_backend"] = "cuda118"  
                env_info["install_commands"] = [
                    "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
                ]
            else:
                # Default to CPU for unknown CUDA versions
                env_info["recommended_backend"] = "cpu"
                env_info["install_commands"] = [
                    "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
                ]
        else:
            print("   ⚠️  CUDA detected but version unknown, defaulting to CPU")
            env_info["recommended_backend"] = "cpu"
            env_info["install_commands"] = [
                "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
            ]
    
    # Default to CPU if no GPU detected
    if not env_info["cuda_available"] and not env_info["mps_available"]:
        env_info["recommended_backend"] = "cpu"
        env_info["install_commands"] = [
            "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
        ]
        print("💻 No GPU detected - using CPU backend")
    
    return env_info

def install_pytorch(env_info, force=False):
    """Install PyTorch with detected configuration"""
    
    # Check if PyTorch is already installed
    if not force:
        try:
            import torch
            print(f"📦 PyTorch {torch.__version__} already installed")
            
            # Quick compatibility check
            if env_info["recommended_backend"] == "cuda121" and not torch.cuda.is_available():
                print("⚠️  CUDA detected but PyTorch CUDA not available - reinstalling...")
                force = True
            elif env_info["recommended_backend"] == "mps" and not (hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()):
                print("⚠️  MPS detected but PyTorch MPS not available - reinstalling...")  
                force = True
            else:
                return True
        except ImportError:
            print("📦 PyTorch not installed")
    
    if force:
        print("🗑️  Uninstalling existing PyTorch...")
        run_command("pip uninstall torch torchvision torchaudio -y", capture=False)
    
    print(f"🚀 Installing PyTorch for {env_info['recommended_backend']}...")
    
    for cmd in env_info["install_commands"]:
        print(f"   Running: {cmd}")
        success, stdout, stderr = run_command(cmd, capture=False)
        
        if not success:
            print(f"❌ Installation failed: {stderr}")
            return False
    
    print("✅ PyTorch installation completed")
    return True

def verify_installation(env_info):
    """Verify PyTorch installation and GPU availability"""
    
    try:
        import torch
        print(f"\n✅ PyTorch {torch.__version__} imported successfully")
        
        # Check CUDA
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            print(f"🎮 CUDA available: {device_count} GPU(s)")
            for i in range(device_count):
                props = torch.cuda.get_device_properties(i)
                print(f"   GPU {i}: {props.name}")
                print(f"   Memory: {props.total_memory / 1e9:.1f}GB")
        
        # Check MPS
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("🍎 Metal Performance Shaders (MPS) available")
        
        # Determine optimal device
        if torch.cuda.is_available():
            test_device = "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            test_device = "mps"
        else:
            test_device = "cpu"
        
        print(f"\n🧪 Testing tensor operations on {test_device}...")
        
        # Test tensor creation and operation
        x = torch.randn(1000, 1000, device=test_device)
        y = torch.mm(x, x.t())
        
        print(f"✅ Matrix multiplication test passed on {test_device}")
        print(f"   Result shape: {y.shape}")
        print(f"   Device: {y.device}")
        
        # Save configuration for future use
        config = {
            "detected_backend": env_info["recommended_backend"],
            "optimal_device": test_device,
            "pytorch_version": torch.__version__,
            "verification_date": subprocess.check_output(["date"], text=True).strip()
        }
        
        with open("gpu_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"💾 Configuration saved to gpu_config.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Universal GPU Environment Setup")
    parser.add_argument("--detect-only", action="store_true", help="Only detect environment")
    parser.add_argument("--install-only", action="store_true", help="Only install PyTorch")  
    parser.add_argument("--verify-only", action="store_true", help="Only verify installation")
    parser.add_argument("--force", action="store_true", help="Force reinstall PyTorch")
    
    args = parser.parse_args()
    
    print("🔧 Universal GPU Development Environment Setup")
    print("=" * 60)
    
    # Detect environment
    env_info = detect_gpu_environment()
    
    if args.detect_only:
        print(f"\n📋 Detection Results:")
        print(f"   Recommended backend: {env_info['recommended_backend']}")
        print(f"   Install commands: {env_info['install_commands']}")
        return
    
    # Install PyTorch
    if not args.verify_only:
        if not install_pytorch(env_info, force=args.force):
            print("❌ Installation failed")
            sys.exit(1)
    
    # Verify installation  
    if not args.install_only:
        if not verify_installation(env_info):
            print("❌ Verification failed")
            sys.exit(1)
    
    print("\n🎉 Universal GPU environment setup complete!")
    print(f"   Backend: {env_info['recommended_backend']}")
    print(f"   Ready for development!")

if __name__ == "__main__":
    main()