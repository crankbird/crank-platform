# CRITICAL CONTEXT FOR CODING AGENTS

This file is loaded by Codex / Copilot / GPT-5 when assisting with this repository.
It defines **non-negotiable architectural rules**, **service boundaries**, and **tooling expectations**.

---

## ⚠️ MAJOR ARCHITECTURE REFACTOR IN PROGRESS (Nov 2025)

**Current Status**: Migrating from platform-centric to **controller/worker/capability** model

### Active Work
- **Phase 0** (Issue #27): Building capability schema + worker runtime foundation
- Old architecture archived in `archive/2025-11-09-pre-controller-refactor/`
- See `docs/planning/CONTROLLER_WORKER_REFACTOR_PLAN.md` for complete roadmap

### Critical Rules for New Code
1. **Do NOT modify archived services** in `archive/2025-11-09-pre-controller-refactor/`
2. **New workers MUST use** `src/crank/worker_runtime/` base classes (when ready)
3. **Capabilities MUST be defined** in `src/crank/capabilities/schema.py` (when ready)
4. **Tests MUST validate** capability-based routing, not direct service calls
5. **Follow taxonomy** in `docs/planning/crank-taxonomy-and-deployment.md`

### Architecture Principles (NEW)
- **Workers are not containers** - Logical providers; execution strategy varies
- **Capabilities are source of truth** - Routing correctness over service discovery
- **Controller is only privileged component** - Workers operate in restricted sandbox
- **Mesh coordinates state, not execution** - Work stays local unless routed

---

## 🧱 Package Management

### ALWAYS USE **uv**, NEVER **pip** DIRECTLY

```bash
uv pip install <package>
uv pip list
uv pip freeze > requirements.txt
```

- `uv` ensures deterministic envs and consistent dependency solving.
- Do not run `pip install` or modify system Python envs.

---

## 🧠 Image Classifier Architecture

There are **two distinct classifier workers** — not interchangeable:

### 1. CPU Classifier (Edge / Low power)

- File: `services/relaxed-checking/crank_image_classifier.py`
- Dependencies: `opencv`, `PIL`, `scikit-learn`
- Designed for **macOS host runtime**, Raspberry Pi, phones, thin workers
- **Relaxed type checking** is acceptable here

### 2. GPU Classifier (High-performance / Datacenter)

- File: `services/crank_image_classifier_advanced.py`
- Dependencies: `torch`, `transformers`, `YOLO`, `CLIP`
- Lives in **Linux / WSL2 / CUDA environments**
- macOS cannot run this worker due to hardware constraints

#### Architectural Reason

macOS containers **cannot** access Metal/MPS from inside Docker.
Therefore: **CPU and GPU workers are separate services** by design.

---

## 🐳 Runtime Strategy (Legacy - Being Replaced)

> ⚠️ **Note**: This describes the OLD architecture. Will be replaced by controller/worker model in Phase 2-3.

| Scenario | Worker to Use | Runtime |
|--------|-----------|---------|
| macOS laptop | CPU worker | **native host runtime** (not container) |
| Windows + WSL2 | GPU worker | **Docker GPU runtime** |
| Linux server w/ GPU | GPU worker | **OCI container** |

**NEW (Post-Phase 3)**:
- All platforms run **controller** (container or native)
- Workers can be containers OR native (deployment model specific)
- Hybrid mode (macOS): CPU workers in containers, GPU workers native (Metal)

---

## 🧭 FastAPI Dependency Injection Strategy (Current - Controller Will Evolve)

We use **Lifespan initialization + Service-Level DI** with modern Annotated pattern:

```python
@asynccontextmanager
async def lifespan(app):
    app.state.platform = PlatformService()
    app.state.protocol = ProtocolService()
    yield
```

```python
from typing import Annotated, cast
from fastapi import Depends, Request

def get_platform_service(request: Request) -> PlatformService:
    svc = getattr(request.app.state, "platform", None)
    if svc is None:
        raise RuntimeError("PlatformService not initialized")
    return cast(PlatformService, svc)
```

Route handlers receive **concrete typed services**:

```python
@app.get("/endpoint")
async def handler(platform: Annotated[PlatformService, Depends(get_platform_service)]):
    return await platform.method()
```

Why:

- Type checkers see **non-optional** concrete services
- No `# type: ignore` sprawl
- Only **one cast** per service
- Test overrides are easy (`app.state.platform = FakePlatform()`)

---

## 📌 Non-Negotiable Rules

1. **Do not merge code that breaks type checking** unless inside `relaxed-checking/`.
2. **Never touch `sys.path`** — import paths must be valid under `src/` layout.
3. **ALWAYS use `uv`** for package management, NEVER `pip` directly.
4. **Follow three-ring architecture** (Ring 1: strict core, Ring 2: boundary shims, Ring 3: external).
5. **NEW: Respect controller/worker separation** - Workers never perform privileged operations.
6. **NEW: All capabilities MUST be schema-validated** - No ad-hoc capability declarations.
7. **NEW: Workers discover controller via ENV** - No hardcoded URLs (use `CONTROLLER_URL`).

---

## 📦 Development Environment Setup

### Initial Setup (Phase 0+)

```bash
# Use uv for all Python package management
uv venv --python 3.11
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install all dependencies including new runtime packages
uv sync --all-extras

# Install development tools
uv pip install pytest pytest-asyncio pytest-cov pytest-timeout

# Verify installation
uv pip list | grep crank
```

### Expected Packages (Growing in Phase 0+)

**Core Platform** (existing):

- `crank-platform` - Type-safe core libraries
- `fastapi`, `uvicorn`, `pydantic` - Web framework
- `httpx`, `requests` - HTTP clients
- `cryptography`, `pyopenssl` - Certificate management

**NEW - Worker Runtime** (Phase 0):

- `crank-worker-runtime` - Shared worker base classes (will be editable install)
- Additional dependencies TBD based on implementation

**NEW - Capabilities** (Phase 0):

- `crank-capabilities` - Capability schema definitions (will be editable install)
- JSON schema validation libraries TBD

**ML/CV Workers** (existing, will migrate):

- CPU: `opencv-python`, `pillow`, `scikit-learn`
- GPU: `torch`, `transformers`, `clip`, `yolo`

**Development**:

- `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-timeout`
- `black`, `ruff`, `mypy`, `pyright`

### Post-Refactor venv (Phase 3+)

The venv will become **richer** with:

- Controller runtime packages
- Worker runtime base classes
- Capability schema validators
- Mesh coordination libraries
- Potentially split into multiple venvs (controller vs worker dependencies)

---

## 📋 Legacy Rules (Still Apply)

1. **Workers do *one* job**. If you need more, create another worker.
2. **No global state outside lifespan DI.**
3. **If unsure: ask** — do not guess capability/service boundaries.
