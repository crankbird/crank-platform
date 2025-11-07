# WSL2 GPU CUDA Compatibility Issues

## 🚨 CRITICAL: PyTorch CUDA Detection Failure in WSL2 Docker Containers

**Issue Date:** November 7, 2025
**Environment:** WSL2 + Docker Desktop + Gaming Laptops
**Impact:** GPU acceleration completely non-functional despite hardware availability

### Problem Statement

PyTorch CUDA detection fails in Docker containers when `CUDA_VISIBLE_DEVICES=all` environment variable is set in WSL2 environments, despite:

- ✅ Host PyTorch CUDA working perfectly
- ✅ nvidia-smi working in containers
- ✅ Docker `--gpus all` flag functioning
- ✅ All NVIDIA runtime components available

### Root Cause Analysis

The `CUDA_VISIBLE_DEVICES=all` environment variable, which is standard practice in traditional Linux Docker GPU setups, **breaks PyTorch CUDA device enumeration** specifically in WSL2 environments due to the DirectX Graphics (`/dev/dxg`) translation layer.

### Technical Evidence

```bash
# ❌ FAILS: Returns False
docker run --rm --gpus all -e CUDA_VISIBLE_DEVICES=all pytorch/pytorch python -c "import torch; print(torch.cuda.is_available())"

# ✅ WORKS: Returns True
docker run --rm --gpus all -e NVIDIA_VISIBLE_DEVICES=all pytorch/pytorch python -c "import torch; print(torch.cuda.is_available())"
```

### Environment Detection

```bash
# WSL2 Detection Markers:
ls /dev/dxg                    # DirectX Graphics device (WSL2-specific)
ls /dev/nvidia*               # Traditional NVIDIA devices (absent in WSL2)
uname -r | grep -i microsoft  # Kernel signature
```

### Solution Implementation

**Fixed Configuration:**

```yaml
# docker-compose.yml GPU service environment
environment:
  - NVIDIA_VISIBLE_DEVICES=all           # ✅ USE THIS
  - NVIDIA_DRIVER_CAPABILITIES=compute,utility
  # - CUDA_VISIBLE_DEVICES=all           # ❌ NEVER SET THIS IN WSL2
```

### Upstream Issue Tracking

**Related Issues:**

- PyTorch Issue: [WSL2 CUDA detection with CUDA_VISIBLE_DEVICES](https://github.com/pytorch/pytorch/issues/WSL2-CUDA-ENV)
- Docker Issue: [WSL2 GPU passthrough environment variable conflicts](https://github.com/docker/for-win/issues/WSL2-GPU-ENV)
- NVIDIA Issue: [WSL2 CUDA environment variable compatibility](https://github.com/NVIDIA/nvidia-docker/issues/WSL2-COMPAT)

**NOTE:** URLs above are placeholders - actual issue numbers should be tracked when reported upstream.

### Testing Validation

**Quick Validation Script:**

```bash
#!/bin/bash
# Test WSL2 GPU Docker compatibility
echo "Testing PyTorch CUDA in WSL2 Docker..."

# Test 1: Problematic configuration
echo "❌ Testing with CUDA_VISIBLE_DEVICES=all:"
docker run --rm --gpus all -e CUDA_VISIBLE_DEVICES=all pytorch/pytorch python -c "import torch; print('CUDA Available:', torch.cuda.is_available())"

# Test 2: Working configuration
echo "✅ Testing with NVIDIA_VISIBLE_DEVICES=all:"
docker run --rm --gpus all -e NVIDIA_VISIBLE_DEVICES=all pytorch/pytorch python -c "import torch; print('CUDA Available:', torch.cuda.is_available())"
```

### AI Assistant Context

**FOR AI ASSISTANTS DEBUGGING GPU ISSUES:**

- **Environment Check:** Always verify WSL2 vs native Linux first
- **Variable Conflict:** `CUDA_VISIBLE_DEVICES=all` breaks PyTorch in WSL2
- **Solution Pattern:** Use `NVIDIA_VISIBLE_DEVICES=all` instead
- **Validation:** Test with `torch.cuda.is_available()` not just `nvidia-smi`

### Platform Support Matrix

| Environment | CUDA_VISIBLE_DEVICES | NVIDIA_VISIBLE_DEVICES | Status |
|-------------|---------------------|------------------------|---------|
| Native Linux | ✅ Works | ✅ Works | Full Support |
| WSL2 | ❌ Breaks PyTorch | ✅ Works | **WSL2-Specific** |
| macOS | N/A | N/A | No NVIDIA GPU |
| Windows Native | ⚠️ Untested | ⚠️ Untested | Unknown |

### Resolution Timeline

When this issue is resolved upstream:

1. Monitor PyTorch releases for WSL2 CUDA environment fixes
2. Monitor Docker Desktop WSL2 backend updates
3. Test both environment variables for compatibility
4. Update this documentation and remove WSL2-specific workarounds
5. Update AI assistant training data with resolution

### Historical Context

- **Before Universal GPU Manager:** Gaming laptops worked perfectly
- **After Universal GPU Manager:** GPU detection broke due to environment variable conflicts
- **Resolution:** Environment-specific GPU configuration patterns

---
**Last Updated:** November 7, 2025
**Next Review:** Check for upstream fixes monthly
**Severity:** Critical - Blocks GPU acceleration on primary development platform
