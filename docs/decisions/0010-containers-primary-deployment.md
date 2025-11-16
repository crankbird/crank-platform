# ADR-0010: Use Containers as the Primary Deployment Unit

**Status**: Accepted
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Core Platform & Agent Architecture](../planning/adr-backlog-2025-11-16.md#core-platform--agent-architecture)

## Context and Problem Statement

Workers need consistent environments across development, staging, and production. We need isolation between workers, reproducible builds, and easy deployment. How should we package and deploy workers?

## Decision Drivers

- Consistency: Same environment dev → prod
- Isolation: Workers don't interfere with each other
- Reproducibility: Deterministic builds
- Portability: Run on macOS, Linux, Windows, cloud
- Resource limits: CPU/memory constraints per worker
- Security: Sandboxing untrusted code

## Considered Options

- **Option 1**: Containers as primary deployment unit (chosen)
- **Option 2**: Native Python virtualenvs
- **Option 3**: System-level packages

## Decision Outcome

**Chosen option**: "Containers as primary deployment unit", because they provide the best combination of isolation, reproducibility, and portability while allowing hybrid deployment (native for GPU workers on macOS).

### Positive Consequences

- Consistent environment across all platforms
- Strong isolation between workers
- Reproducible builds (Dockerfile = build spec)
- Resource limits via cgroups
- Security sandboxing
- Easy rollback (container tags)
- Base worker image eliminates duplication

### Negative Consequences

- Overhead vs native execution
- macOS GPU workers must run native (Metal not in containers)
- Container image size
- Build time for each worker
- Learning curve for container orchestration

## Pros and Cons of the Options

### Option 1: Containers as Primary Deployment Unit

Docker/Podman containers with hybrid exception for GPU workers.

**Pros:**
- Strong isolation
- Reproducible builds
- Resource limits
- Portability
- Security sandboxing
- Base image pattern

**Cons:**
- Runtime overhead
- macOS GPU exception needed
- Image size
- Build complexity

### Option 2: Native Python Virtualenvs

Each worker in its own venv.

**Pros:**
- No overhead
- Simple deployment
- Fast startup
- Native performance

**Cons:**
- No isolation (shared kernel)
- Dependency conflicts
- No resource limits
- Platform-specific issues
- Hard to reproduce

### Option 3: System-Level Packages

Install workers as system packages.

**Pros:**
- Maximum performance
- Simple installation

**Cons:**
- No isolation
- Dependency hell
- Can't run multiple versions
- Platform-specific
- Security risks

## Links

- [Related to] ADR-0001 (Controller/Worker model supports containerization)
- [Related to] ADR-0009 (GPU workers hybrid deployment)
- [Related to] Phase 2 (Base worker image implementation)
- [Related to] `Dockerfile.worker-base`

## Implementation Notes

**Base Worker Image** (`Dockerfile.worker-base`):

```dockerfile
FROM python:3.11-slim

# Common dependencies
RUN pip install fastapi uvicorn pydantic httpx

# Security setup
RUN useradd -m -u 1000 worker
USER worker

# Certificate paths
ENV CERT_DIR=/home/worker/.crank/certs

WORKDIR /app
```

**Worker-Specific Dockerfile**:

```dockerfile
FROM crank-worker-base:latest

# Worker-specific dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Worker code
COPY --chown=worker:worker . .

CMD ["python", "crank_email_classifier.py"]
```

**Benefits of Base Image**:
- Eliminates 40+ lines per worker Dockerfile
- Consistent base across all workers
- Faster builds (cached layers)
- Security updates in one place

**Hybrid Deployment**:

**CPU Workers** (containerized):

```bash
docker run -p 8501:8501 \
  -v ~/.crank/certs:/home/worker/.crank/certs:ro \
  crank-email-classifier:latest
```

**GPU Workers on macOS** (native with Metal):

```bash
# Native execution for Metal GPU access
python services/crank_image_classifier_gpu.py
```

**GPU Workers on Linux** (containerized with GPU passthrough):

```bash
docker run --gpus all -p 8503:8503 \
  -v ~/.crank/certs:/home/worker/.crank/certs:ro \
  crank-image-classifier-gpu:latest
```

**Resource Limits**:

```bash
docker run --cpus=2 --memory=4g \
  crank-email-classifier:latest
```

## Review History

- 2025-11-16 - Initial decision (formalizing Phase 2 implementation)
