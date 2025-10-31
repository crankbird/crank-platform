#!/usr/bin/env python3
"""
Simplified GPU Detection and PyTorch Installation
Focus on uv-first approach with pip fallback for reliability
"""

import subprocess
import sys
import platform
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
    """Detect GPU capabilities - simplified and reliable"""
    
    env_info = {
        "platform": platform.system(),
        "architecture": platform.machine(),
        "cuda_available": False,
        "cuda_version": None,
        "mps_available": False,
        "recommended_backend": "cpu",
        "uv_commands": [],
        "pip_commands": []
    }
    
    print(f"🔍 Environment: {env_info['platform']} {env_info['architecture']}")
    
    # Apple Silicon detection
    if env_info["platform"] == "Darwin" and "arm" in env_info["architecture"].lower():
        env_info["mps_available"] = True
        env_info["recommended_backend"] = "mps"
        # Both uv and pip use same PyTorch index for Apple Silicon
        base_cmd = "torch torchvision torchaudio"
        env_info["uv_commands"] = [f"uv pip install {base_cmd}"]
        env_info["pip_commands"] = [f"pip install {base_cmd}"]
        print("🍎 Apple Silicon detected")
        return env_info
    
    # NVIDIA CUDA detection
    cuda_success, cuda_output, _ = run_command("nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits")
    
    if cuda_success and cuda_output.strip():
        env_info["cuda_available"] = True
        print("🎮 NVIDIA GPU detected")
        
        # Try to get CUDA version
        nvcc_success, nvcc_output, _ = run_command("nvcc --version")
        if nvcc_success:
            for line in nvcc_output.split('\n'):
                if "release" in line.lower():
                    version = line.split("release ")[1].split(",")[0]
                    env_info["cuda_version"] = version
                    break
        
        # If no nvcc, try nvidia-smi
        if not env_info["cuda_version"]:
            smi_success, smi_output, _ = run_command("nvidia-smi")
            if smi_success:
                for line in smi_output.split('\n'):
                    if "CUDA Version:" in line:
                        version = line.split("CUDA Version: ")[1].split()[0]
                        env_info["cuda_version"] = version
                        break
        
        # Set commands based on CUDA version
        if env_info["cuda_version"]:
            major = env_info["cuda_version"].split('.')[0]
            print(f"   CUDA Version: {env_info['cuda_version']}")
            
            if major == "12":
                env_info["recommended_backend"] = "cuda121"
                base_cmd = "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
            elif major == "11":
                env_info["recommended_backend"] = "cuda118"
                base_cmd = "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
            else:
                # Unknown CUDA version, use CPU
                env_info["recommended_backend"] = "cpu"
                base_cmd = "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
                
            env_info["uv_commands"] = [f"uv pip install {base_cmd}"]
            env_info["pip_commands"] = [f"pip install {base_cmd}"]
        else:
            print("   ⚠️  CUDA detected but version unknown, using CPU")
            env_info["recommended_backend"] = "cpu"
            base_cmd = "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
            env_info["uv_commands"] = [f"uv pip install {base_cmd}"]
            env_info["pip_commands"] = [f"pip install {base_cmd}"]
    
    # CPU fallback
    if not env_info["cuda_available"] and not env_info["mps_available"]:
        env_info["recommended_backend"] = "cpu"
        base_cmd = "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"
        env_info["uv_commands"] = [f"uv pip install {base_cmd}"]
        env_info["pip_commands"] = [f"pip install {base_cmd}"]
        print("💻 CPU-only backend")
    
    return env_info

def check_pytorch_installation():
    """Check if PyTorch is already installed and working"""
    try:
        import torch
        version = torch.__version__
        
        # Quick device test
        device = "cpu"
        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = "mps"
            
        return True, version, device
    except ImportError:
        return False, None, None
    except Exception as e:
        return False, None, f"error: {e}"

def install_pytorch_simple(env_info, force=False, prefer_uv=True):
    """Simple PyTorch installation with uv-first, pip-fallback strategy"""
    
    # Check existing installation
    if not force:
        installed, version, device = check_pytorch_installation()
        if installed:
            print(f"📦 PyTorch {version} already installed (device: {device})")
            
            # Quick compatibility check
            if env_info["recommended_backend"].startswith("cuda") and device != "cuda":
                print("⚠️  CUDA expected but not available, reinstalling...")
                force = True
            elif env_info["recommended_backend"] == "mps" and device != "mps":
                print("⚠️  MPS expected but not available, reinstalling...")
                force = True
            else:
                return True
    
    if force:
        print("🗑️  Uninstalling existing PyTorch...")
        # Use both uv and pip to be thorough
        run_command("uv pip uninstall torch torchvision torchaudio -y", capture=False)
        run_command("pip uninstall torch torchvision torchaudio -y", capture=False)
    
    # Try uv first if available and preferred
    if prefer_uv:
        uv_available, _, _ = run_command("uv --version")
        if uv_available:
            print(f"🚀 Installing PyTorch with uv (backend: {env_info['recommended_backend']})...")
            
            for cmd in env_info["uv_commands"]:
                print(f"   Running: {cmd}")
                success, stdout, stderr = run_command(cmd, capture=False)
                
                if success:
                    print("✅ uv installation successful")
                    return True
                else:
                    print(f"❌ uv installation failed: {stderr}")
                    print("🔄 Falling back to pip...")
                    break
    
    # Fallback to pip
    print(f"🚀 Installing PyTorch with pip (backend: {env_info['recommended_backend']})...")
    
    for cmd in env_info["pip_commands"]:
        print(f"   Running: {cmd}")
        success, stdout, stderr = run_command(cmd, capture=False)
        
        if success:
            print("✅ pip installation successful")
            return True
        else:
            print(f"❌ pip installation failed: {stderr}")
            return False
    
    return False

def verify_pytorch_simple():
    """Simple PyTorch verification"""
    
    try:
        import torch
        print(f"\n✅ PyTorch {torch.__version__} imported successfully")
        
        # Test device availability
        devices = []
        if torch.cuda.is_available():
            devices.append(f"CUDA ({torch.cuda.device_count()} GPU(s))")
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            devices.append("MPS (Apple Silicon)")
        devices.append("CPU")
        
        print(f"🎮 Available devices: {', '.join(devices)}")
        
        # Quick tensor test
        device = torch.device("cuda" if torch.cuda.is_available() 
                            else "mps" if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
                            else "cpu")
        
        print(f"\n🧪 Testing {device}...")
        x = torch.randn(100, 100, device=device)
        y = torch.mm(x, x.t())
        print(f"✅ Tensor operations working on {device}")
        
        # Save simple config
        config = {
            "pytorch_version": torch.__version__,
            "optimal_device": str(device),
            "verification_successful": True
        }
        
        with open("gpu_config_simple.json", "w") as f:
            json.dump(config, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main function with simplified approach"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simplified GPU Environment Setup")
    parser.add_argument("--detect-only", action="store_true", help="Only detect environment")
    parser.add_argument("--verify-only", action="store_true", help="Only verify installation")
    parser.add_argument("--force", action="store_true", help="Force reinstall")
    parser.add_argument("--use-pip", action="store_true", help="Use pip instead of uv")
    
    args = parser.parse_args()
    
    print("🔧 Simplified GPU Environment Setup")
    print("=" * 50)
    
    # Detect environment
    env_info = detect_gpu_environment()
    
    if args.detect_only:
        print(f"\n📋 Detection Results:")
        print(f"   Backend: {env_info['recommended_backend']}")
        print(f"   uv command: {env_info['uv_commands'][0] if env_info['uv_commands'] else 'N/A'}")
        print(f"   pip command: {env_info['pip_commands'][0] if env_info['pip_commands'] else 'N/A'}")
        return
    
    # Install if requested
    if not args.verify_only:
        prefer_uv = not args.use_pip
        if not install_pytorch_simple(env_info, force=args.force, prefer_uv=prefer_uv):
            print("❌ Installation failed")
            sys.exit(1)
    
    # Verify installation
    if not args.install_only:
        if not verify_pytorch_simple():
            print("❌ Verification failed")
            sys.exit(1)
    
    print(f"\n🎉 Setup complete! Backend: {env_info['recommended_backend']}")

if __name__ == "__main__":
    main()