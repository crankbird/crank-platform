# ADR-0009: Separate CPU and GPU Workers with Common Interface

**Status**: Accepted
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Core Platform & Agent Architecture](../planning/adr-backlog-2025-11-16.md#core-platform--agent-architecture)

## Context and Problem Statement

Some workers need GPU acceleration (image classification, LLM inference) while others run fine on CPU (email parsing, document conversion). GPUs are expensive and limited. We need to separate CPU and GPU workloads while maintaining a consistent interface for capability routing.

## Decision Drivers

- Resource optimization: Don't waste GPU on CPU-bound tasks
- Cost: GPU resources are expensive
- Deployment flexibility: macOS Metal native vs containerized CUDA
- Capability-based routing: Same interface regardless of hardware
- Privilege separation: GPU access requires host access (macOS Metal)
- Developer experience: Same code pattern for both worker types

## Considered Options

- **Option 1**: Separate CPU/GPU workers with common interface (chosen)
- **Option 2**: Single worker with dynamic GPU detection
- **Option 3**: All workers GPU-capable

## Decision Outcome

**Chosen option**: "Separate CPU/GPU workers with common interface", because it optimizes resource usage, enables hybrid deployment (native GPU + containerized CPU), and maintains clear capability boundaries.

### Positive Consequences

- Efficient resource usage (GPU only when needed)
- CPU workers fully containerized
- GPU workers can run native (macOS Metal) or containerized (CUDA)
- Clear capability declaration (worker advertises GPU requirement)
- Cost optimization (scale CPU and GPU independently)
- Same `WorkerApplication` interface for both

### Negative Consequences

- Must maintain two versions of some workers
- Capability registry must track resource requirements
- Routing complexity (match capability + available resources)
- Testing burden (test both CPU and GPU paths)

## Pros and Cons of the Options

### Option 1: Separate CPU/GPU Workers with Common Interface

Distinct worker implementations, same API.

**Pros:**
- Resource optimization
- Independent scaling
- Hybrid deployment support
- Clear capability boundaries
- Cost-efficient

**Cons:**
- Code duplication potential
- Routing complexity
- Multiple worker versions

### Option 2: Single Worker with Dynamic GPU Detection

Worker detects GPU at runtime, uses if available.

**Pros:**
- Single codebase
- Automatic fallback
- Simple deployment

**Cons:**
- Wastes GPU on CPU tasks
- Can't separate deployment
- Resource contention
- Complex startup logic

### Option 3: All Workers GPU-Capable

Require GPU for all workers.

**Pros:**
- Simplest deployment
- Maximum performance

**Cons:**
- Massive resource waste
- Prohibitive cost
- Doesn't work on CPU-only hosts
- GPU not needed for many tasks

## Links

- [Related to] ADR-0001 (Controller/Worker model supports hybrid deployment)
- [Related to] Phase 2 (Hybrid deployment implementation)
- [Related to] `docs/development/GPU_SETUP_GUIDE.md`

## Implementation Notes

**Capability Declaration**:

```yaml
# CPU worker
capabilities:
  - verb: parse_email
    resource_requirements:
      cpu: 1
      memory: 512Mi
      gpu: false

# GPU worker
capabilities:
  - verb: classify_image
    resource_requirements:
      cpu: 2
      memory: 4Gi
      gpu: true
      gpu_memory: 8Gi
```

**Deployment Patterns**:

**CPU Workers** (fully containerized):

```dockerfile
FROM python:3.11-slim
# Install CPU-only dependencies
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

**GPU Workers** (hybrid):
- **macOS**: Native execution with Metal acceleration
- **Linux**: Containerized with CUDA GPU passthrough

```dockerfile
FROM nvidia/cuda:12.1-runtime-ubuntu22.04
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

**Worker Interface** (identical for both):

```python
class ImageClassifierCPU(WorkerApplication):
    def __init__(self, https_port: int):
        super().__init__(
            name="image-classifier-cpu",
            https_port=https_port,
            capabilities=["classify_image"]
        )
        self.model = load_model(device="cpu")

class ImageClassifierGPU(WorkerApplication):
    def __init__(self, https_port: int):
        super().__init__(
            name="image-classifier-gpu",
            https_port=https_port,
            capabilities=["classify_image"]
        )
        self.model = load_model(device="cuda")  # or "mps" on macOS
```

**Routing Logic**:
1. Request for `classify_image` capability
2. Controller checks available workers
3. If GPU worker available and healthy → route to GPU
4. Else if CPU worker available → route to CPU
5. Else if cloud escalation enabled → route to cloud GPU worker

## Review History

- 2025-11-16 - Initial decision (formalizing Phase 2 implementation)
