# Dependency Automation Quick Reference

## Install All GPU Dependencies
```bash
./scripts/install-gpu-dependencies.sh
```

## Check Service Dependencies
```bash
python scripts/check-service-dependencies.py crank_image_classifier
```

## Files Created
- `scripts/install-gpu-dependencies.sh` - Automated dependency installation
- `scripts/check-service-dependencies.py` - Dependency validation
- `services/requirements-universal-gpu.txt` - Unified requirements file
- `docs/development/universal-gpu-dependencies.md` - Complete documentation

## Problem Solved
During Issue #20, missing `ultralytics` and `GPUtil` dependencies caused silent failures in UniversalGPUManager integration. This automation prevents those issues.
