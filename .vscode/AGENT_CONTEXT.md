# CRITICAL CONTEXT FOR CODING AGENTS

This file is loaded by Codex / Copilot / GPT-5 when assisting with this repository.
It defines **non-negotiable architectural rules**, **service boundaries**, and **tooling expectations**.

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

## 🐳 Runtime Strategy

| Scenario | Worker to Use | Runtime |
|--------|-----------|---------|
| macOS laptop | CPU worker | **native host runtime** (not container) |
| Windows + WSL2 | GPU worker | **Docker GPU runtime** |
| Linux server w/ GPU | GPU worker | **OCI container** |

Automatic GPU detection was attempted, reverted as unreliable.
Separation is **intentional** and **permanent**.

---

## 🧭 FastAPI Dependency Injection Strategy

We use **Lifespan initialization + Service-Level DI**:

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
3. **Workers do *one* job**. If you need more, create another worker.
4. **No global state outside lifespan DI.**
5. **If unsure: ask** — do not guess capability/service boundaries.
