#!/bin/bash
# Universal GPU Environment Setup Wrapper
# Works with pip, conda, uv, or poetry

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Universal GPU Environment Setup${NC}"
echo "=============================================="

# Detect package manager preference
PACKAGE_MANAGER=""
if command -v uv &> /dev/null; then
    PACKAGE_MANAGER="uv"
    echo -e "${YELLOW}📦 Using uv (fast Python package installer)${NC}"
elif command -v conda &> /dev/null; then
    PACKAGE_MANAGER="conda"
    echo -e "${YELLOW}📦 Using conda (scientific Python distribution)${NC}"
elif command -v poetry &> /dev/null; then
    PACKAGE_MANAGER="poetry"
    echo -e "${YELLOW}📦 Using poetry (dependency management)${NC}"
else
    PACKAGE_MANAGER="pip"
    echo -e "${YELLOW}📦 Using pip (standard Python installer)${NC}"
fi

# Create Python script that adapts to package manager
cat > /tmp/adaptive_pytorch_install.py << 'EOF'
import sys
import subprocess
import os

def install_with_package_manager(manager, commands):
    """Install PyTorch with specified package manager"""
    
    if manager == "uv":
        # uv uses pip-compatible syntax
        for cmd in commands:
            uv_cmd = cmd.replace("pip install", "uv pip install")
            print(f"Running: {uv_cmd}")
            result = subprocess.run(uv_cmd, shell=True)
            if result.returncode != 0:
                return False
                
    elif manager == "conda":
        # For conda, we need to use conda-forge or pytorch channel
        print("Installing PyTorch via conda...")
        
        # Detect GPU requirement from original command
        if "cu121" in " ".join(commands):
            conda_cmd = "conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y"
        elif "cu118" in " ".join(commands):
            conda_cmd = "conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y"
        else:
            conda_cmd = "conda install pytorch torchvision torchaudio cpuonly -c pytorch -y"
            
        print(f"Running: {conda_cmd}")
        result = subprocess.run(conda_cmd, shell=True)
        if result.returncode != 0:
            return False
            
    elif manager == "poetry":
        # Poetry requires adding to pyproject.toml, fallback to pip
        print("Poetry detected, using pip for PyTorch installation...")
        for cmd in commands:
            result = subprocess.run(cmd, shell=True)
            if result.returncode != 0:
                return False
                
    else:
        # Standard pip
        for cmd in commands:
            print(f"Running: {cmd}")
            result = subprocess.run(cmd, shell=True)
            if result.returncode != 0:
                return False
    
    return True

if __name__ == "__main__":
    manager = sys.argv[1]
    commands = sys.argv[2:]
    
    success = install_with_package_manager(manager, commands)
    sys.exit(0 if success else 1)
EOF

# Run GPU detection
echo -e "\n${YELLOW}🔍 Detecting GPU capabilities...${NC}"
python3 scripts/setup_gpu_env.py --detect-only > /tmp/gpu_detection.txt

# Extract install commands
INSTALL_COMMANDS=$(grep "Install commands:" /tmp/gpu_detection.txt | cut -d: -f2- | sed "s/\[//g" | sed "s/\]//g" | sed "s/'//g")

if [ -z "$INSTALL_COMMANDS" ]; then
    echo -e "${RED}❌ Failed to detect GPU configuration${NC}"
    exit 1
fi

echo -e "${GREEN}✅ GPU detection complete${NC}"
cat /tmp/gpu_detection.txt

# Install PyTorch with detected package manager
echo -e "\n${YELLOW}🚀 Installing PyTorch...${NC}"
python3 /tmp/adaptive_pytorch_install.py "$PACKAGE_MANAGER" $INSTALL_COMMANDS

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ PyTorch installation complete${NC}"
    
    # Verify installation
    echo -e "\n${YELLOW}🧪 Verifying installation...${NC}"
    python3 scripts/setup_gpu_env.py --verify-only
    
    if [ $? -eq 0 ]; then
        echo -e "\n${GREEN}🎉 Universal GPU environment setup successful!${NC}"
        echo -e "   Package Manager: ${PACKAGE_MANAGER}"
        echo -e "   Configuration saved to gpu_config.json"
    else
        echo -e "\n${RED}❌ Verification failed${NC}"
        exit 1
    fi
else
    echo -e "\n${RED}❌ Installation failed${NC}"
    exit 1
fi

# Cleanup
rm -f /tmp/adaptive_pytorch_install.py /tmp/gpu_detection.txt