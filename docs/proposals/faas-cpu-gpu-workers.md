# CPU vs GPU Worker Specification

## Overview
Same worker codebase, different deployments.

## Capability Model
Workers advertise acceleration type:

CPU Worker:

```json
{
  "capabilities": [{
    "name": "python.run.ml",
    "env_profile": "python-ml",
    "accelerator": "cpu"
  }]
}
```

GPU Worker:

```json
{
  "capabilities": [{
    "name": "python.run.ml",
    "env_profile": "python-ml",
    "accelerator": "gpu",
    "gpu_model": "RTX 1060"
  }]
}
```

## Job Constraint

```json
"constraints": { "accelerator": "gpu" }
```

## Agent Guidance
- Use GPU for ML or vector-heavy tasks.
- Prefer CPU for light text processing.
