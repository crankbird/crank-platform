# WSL2 GPU Development Experiments

This directory contains archived scripts and documentation from our WSL2 GPU development experiments.

## Context

We initially explored using WSL2 for GPU-enabled AI/ML development but encountered networking complexity and virtualization layer overhead. We've since moved to Docker Desktop for a cleaner container-based approach.

## What's Here

- `create_named_wsl_instance.ps1` - PowerShell script for creating fresh WSL2 instances
- `test_wsl2_gpu.sh` - GPU testing script with WSL2-specific CUDA paths
- Notes and lessons learned from the experiment

## Why We Moved Away

- **Network Complexity**: Bridged vs mirrored networking, IP address management
- **Custom Ports**: SSH on port 2222, connection reliability issues  
- **CUDA Path Issues**: WSL2-specific library paths (`/usr/lib/wsl/lib`)
- **Virtualization Overhead**: Multiple layers (Host → WSL2 → Container)

## What Worked

- ✅ Hybrid package management (conda+uv) 
- ✅ nvidia-smi detection and GPU enumeration
- ✅ Automated fresh environment creation
- ✅ SSH configuration and passwordless access

## Lessons Learned

1. **Docker Desktop is cleaner** for GPU development than WSL2
2. **Container isolation** beats VM/WSL2 combinations
3. **Standard networking** is preferable to custom virtualization
4. **Hybrid package management** works great regardless of platform

## Current Approach

See the main repository for our Docker-based development environment using the same validated hybrid package management approach.