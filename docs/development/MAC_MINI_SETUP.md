# Mac Mini Development Setup

**Status**: Active  
**Type**: Platform-Specific Setup  
**Last Updated**: 2025-11-10  
**Hardware**: Mac Mini M2/M4 with Apple Silicon  
**Purpose**: macOS-specific development environment configuration

---

## Hardware Recommendations

### Mac Mini Configuration

- **Model**: Mac Mini M2 or M4
- **Memory**: 32GB unified memory (recommended for ML development)
- **Storage**: 512GB minimum (1TB recommended for AI model storage)
- **Network**: Gigabit Ethernet for reliable development

**Why Mac Mini for Platform Development**:

- Native ARM architecture matches edge deployment targets (Raspberry Pi, ARM cloud)
- Unified memory architecture (32GB shared CPU/GPU) enables large model development
- Metal Performance Shaders (MPS) provides GPU acceleration for ML
- Cost-effective alternative to cloud GPU development ($1,400 one-time vs $6,000/year)

## Initial Setup

### 1. Install Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Docker Desktop

```bash
brew install --cask docker
```

**Important**: Enable "Use Rosetta for x86/amd64 emulation on Apple Silicon" in Docker Desktop settings if you need x86 compatibility.

### 3. Install Development Tools

```bash
# Git and build tools
xcode-select --install

# Python package manager (UV)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Optional: Traditional Python from Homebrew
brew install python@3.12
```

## Python Environment for ML Development

### PyTorch with Metal Performance Shaders (MPS)

```bash
# Install PyTorch with MPS support
pip install torch torchvision torchaudio

# Verify MPS availability
python3 -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}')"
```

**Expected output**: `MPS available: True`

### Apple Silicon Optimized ML Libraries

```bash
# TensorFlow for macOS (optional)
pip install tensorflow-macos tensorflow-metal

# Hugging Face transformers with Apple Silicon optimization
pip install accelerate transformers optimum
```

## GPU Development with MPS

### Check Metal GPU

```python
import torch

if torch.backends.mps.is_available():
    device = torch.device("mps")
    print(f"Using Metal GPU")
else:
    device = torch.device("cpu")
    print("MPS not available, using CPU")

# Example: Move model to GPU
model = YourModel().to(device)
tensor = torch.randn(1, 3, 224, 224).to(device)
output = model(tensor)
```

### Memory Management

Apple Silicon uses **unified memory** (shared CPU/GPU):

```python
# Check available memory
import psutil
total_memory = psutil.virtual_memory().total / 1e9
print(f"Total unified memory: {total_memory:.1f}GB")

# For large models, use half precision
model = AutoModel.from_pretrained(
    "model-name",
    torch_dtype=torch.float16,   # Half precision for memory efficiency
    device_map="auto"            # Automatic memory management
)
```

**32GB Mac Mini**: Can handle models up to ~25GB in half precision (fp16)

## Crank Platform Setup

### Clone and Run

```bash
# Clone repository
git clone https://github.com/crankbird/crank-platform.git
cd crank-platform

# Run development environment
./dev-universal.sh  # Includes GPU services with MPS support
```

### Verify GPU Services

```bash
# Check image classifier GPU service
curl -k https://localhost:8402/health

# Should show MPS device detected
```

## Platform-Specific Considerations

### Rosetta 2 for x86 Compatibility

Some Docker images may require x86 emulation:

```bash
# Enable Rosetta 2
softwareupdate --install-rosetta --agree-to-license

# Docker will use Rosetta automatically for x86 images
```

### File System Case Sensitivity

macOS default file system (APFS) is case-insensitive:

```bash
# Check case sensitivity
diskutil info / | grep "Case-sensitive"

# For development, case-insensitive is usually fine
# Docker volumes work correctly on both
```

### Network Configuration

macOS firewall may block local services:

```bash
# Allow Docker in firewall
# System Settings → Network → Firewall → Options
# Add Docker to allowed applications
```

## Performance Optimization

### Docker Resource Limits

In Docker Desktop → Settings → Resources:

- **CPUs**: 8 cores (for M4 Pro with 12 cores, use 10)
- **Memory**: 24GB (leave 8GB for macOS)
- **Swap**: 4GB
- **Disk**: 100GB+

### MPS Performance Tips

```python
# Enable MPS fallback for unsupported operations
import os
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

# For training, use mixed precision
from torch.cuda.amp import autocast, GradScaler

# Replace torch.cuda with torch.mps for Apple Silicon
# Note: amp is CUDA-specific, use manual fp16 on MPS
model = model.half()  # Convert to fp16
```

## Troubleshooting

### MPS Not Detected

```bash
# Check PyTorch version (need 2.0+)
python3 -c "import torch; print(torch.__version__)"

# Reinstall PyTorch
pip install --upgrade torch torchvision torchaudio

# Verify installation
python3 -c "import torch; print(torch.backends.mps.is_built())"
```

### Docker Performance Issues

```bash
# Use VirtioFS for better file system performance
# Docker Desktop → Settings → General
# Enable "VirtioFS" under file sharing implementation

# Clear Docker cache
docker system prune -a --volumes
```

### Port Conflicts

```bash
# Check what's using a port
lsof -i :8443

# Kill process
kill -9 <PID>
```

## Development Workflow

### Recommended Editor: VS Code

```bash
brew install --cask visual-studio-code

# Open workspace
cd crank-platform
code crank-platform-mascots.code-workspace
```

**Extensions**:

- Python (Microsoft)
- Docker (Microsoft)
- GitHub Copilot
- Ruff (linting/formatting)

### Testing GPU Code

```bash
# Run GPU-specific tests
pytest tests/ -k "gpu" -v

# Check GPU memory usage
import torch
if torch.backends.mps.is_available():
    print(f"Allocated: {torch.mps.current_allocated_memory()/1e9:.2f}GB")
```

## Next Steps

1. **Complete setup**: Follow [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) for full platform setup
2. **Understand architecture**: Read [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md)
3. **Check agent context**: Review `.vscode/AGENT_CONTEXT.md` for development rules
4. **Start developing**: Pick a service in `services/` and start coding!

## Related Documentation

- [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) — Complete cross-platform setup
- [universal-gpu-environment.md](universal-gpu-environment.md) — GPU detection and configuration
- [ml-development-guide.md](ml-development-guide.md) — ML-specific development patterns
- [../ARCHITECTURE.md](../ARCHITECTURE.md) — Platform architecture

---

**Questions?** Open an issue or check the [development README](README.md).
