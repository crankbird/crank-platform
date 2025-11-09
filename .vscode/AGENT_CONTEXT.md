# CRITICAL CONTEXT FOR CODING AGENTS

This file is loaded by Codex / Copilot / GPT-5 when assisting with this repository.
It defines **non-negotiable architectural rules**, **service boundaries**, and **tooling expectations**.

---

## 📝 MARKDOWN FORMATTING RULES

**CRITICAL**: Every fenced code block you write MUST specify a language tag (MD040).

Examples:

````markdown
```python
def example():
    pass
```

```bash
uv pip install -e .
```

```json
{"key": "value"}
```

```text
Plain text output or diagrams
```
````

- Never use bare ```` ``` ```` without a language
- Common languages: `python`, `bash`, `zsh`, `json`, `jsonc`, `yaml`, `toml`, `dockerfile`, `sql`, `text`, `markdown`
- When showing command output or plain text: use `text`
- Always include blank lines before/after lists and code blocks (MD031, MD032)

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
6. **Follow linting patterns** in `docs/development/LINTING_AND_TYPE_CHECKING.md`

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
5. **All markdown code blocks MUST specify language** - Never use bare ```` ``` ```` without a language tag (MD040).
6. **NEW: Respect controller/worker separation** - Workers never perform privileged operations.
7. **NEW: All capabilities MUST be schema-validated** - No ad-hoc capability declarations.
8. **NEW: Workers discover controller via ENV** - No hardcoded URLs (use `CONTROLLER_URL`).

---

## 🧠 Type Checking & Testing Standards

### Strict Mode Requirements

- **Pylance + mypy run in strict mode** - All code must pass strict type checking
- **Every pytest function MUST have return annotation** - Use `-> None` if no return value
- **Example**:

  ```python
  def test_something() -> None:
      """Test docstring."""
      assert True
  ```

### Documentation Linting Standards

- **All fenced code blocks MUST specify language** (MD040) - Use ```` ```python ```` not ```` ``` ````
  - Common languages: `python`, `bash`, `json`, `jsonc`, `yaml`, `toml`, `dockerfile`, `sql`, `text`, `markdown`
  - For shell commands: use `bash` or `zsh` (not `sh`)
  - For plain text output or diagrams: use `text`
  - **CRITICAL**: This applies to ALL markdown you write, including conversation responses and documentation
- **Planning docs should minimize duplicate headings** (MD024) - Especially in long markdown files
- **Lists need blank lines** (MD032) - Always put blank lines before and after list items
- **Fenced blocks need blank lines** (MD031) - Always put blank lines before and after code blocks
- Run `npx markdownlint-cli2 --fix "**/*.md"` to auto-fix common issues
- For complex docs, consider having Codex handle mass MD040/MD024 fixes

### Capability Schema Work

- **Annotate every Pydantic field** - If it's a list, keep the `list[Type]` annotation AND use a typed factory function (e.g., `@staticmethod def _default_error_codes() -> list[ErrorCode]: return []`) so Pyright/Pylance don't downcast it to `list[Unknown]`.
- **NEVER use bare list assignments** - Writing `error_codes = []` erases type information; use `error_codes: list[ErrorCode] = Field(default_factory=_default_error_codes, ...)` where `_default_error_codes` has an explicit return type.
- **For complex default values** - Use typed factory functions with explicit return annotations instead of `default_factory=list`, which loses type information.

### Python Path Configuration

The `crank` package lives under `src/`. Import resolution is configured at three levels:

**1. Pyright/Pylance Global Config** (✅ Already configured)

- `pyrightconfig.json` has `"extraPaths": ["src"]` at the top level (applies to all code)
- **Critical**: The `tests` execution environment (lines 53-66) also has `"extraPaths": ["src", "."]` so Pylance can resolve `crank.*` imports when analyzing test files
- This dual configuration ensures imports work both globally and specifically within tests

**2. VS Code Workspace Settings** (✅ Already configured)

- `.vscode/settings.json` has `"python.analysis.extraPaths": ["${workspaceFolder}/src"]`
- This ensures the editor language server can resolve `crank.*` imports

**3. Package Marker** (✅ Already exists)

- `src/crank/__init__.py` makes `crank.*` a proper Python package

**Runtime Options** (choose one for tests/scripts):

**Option A: Editable Install (Recommended)**

```bash
uv pip install -e .
```

**Option B: PYTHONPATH Export**

```bash
export PYTHONPATH=src
pytest
```

**Critical**: Don't add imports that editors can't resolve. If Pylance shows an import error, fix the path configuration, don't ignore the error.

**Note**: After changing `pyrightconfig.json` or `.vscode/settings.json`, restart the language server ("Python: Restart Language Server" in Command Palette) or reload the VS Code window for changes to take effect.

---

## 🔍 CODE QUALITY PATTERNS (Pylance/Mypy/Ruff)

### FastAPI Route Handlers

**Problem**: Pylance flags nested route handlers as "not accessed" when using decorators.

**Solution**: Use explicit binding instead of decorators:

```python
# ❌ Avoid - Pylance can't see decorator usage
@self.app.get("/health")
async def health_check() -> JSONResponse:
    return JSONResponse(...)

# ✅ Correct - Explicit binding
async def health_check() -> JSONResponse:
    return JSONResponse(...)

self.app.get("/health")(health_check)
```

**Pattern Usage**:
- `src/crank/worker_runtime/base.py` (lines 11-13, 187-192) - Base class implementation
- `services/crank_streaming.py` - Streaming worker with 6 endpoints using explicit binding

**IMPORTANT**: Route registration code IS business logic, not boilerplate. A streaming
service with 6 endpoints (/stream/text, /ws, /events, /status, /capabilities, /) will
naturally have ~125 lines of route handlers. What WorkerApplication eliminates is the
~250 lines of infrastructure (registration, heartbeat, certs, health checks).

### Optional Hooks in Abstract Base Classes

**Problem**: Ruff B027 flags empty methods in abstract classes without `@abstractmethod`.

**Solution**: Add explicit `return None` for optional hooks:

```python
# ❌ Avoid - Ruff sees this as missing implementation
async def on_startup(self) -> None:
    """Optional startup hook."""

# ✅ Correct - Explicit return
async def on_startup(self) -> None:
    """Optional startup hook."""
    return None
```

### Enum String Comparisons

**Problem**: Comparing enum members directly to strings fails type checking.

**Solution**: Use `.value` to access the string representation:

```python
# ❌ Avoid - Type mismatch
assert HealthStatus.HEALTHY == "healthy"

# ✅ Correct - Compare enum value
assert HealthStatus.HEALTHY.value == "healthy"
```

### Type Narrowing After Assertions

**Problem**: Pylance narrows types after assertions, causing false "non-overlapping" errors.

**Solution**: Re-fetch or add explicit type annotation:

```python
# ❌ Avoid - Type narrowed to literal after first assert
manager.set_status(HealthStatus.HEALTHY)
assert manager.status == HealthStatus.HEALTHY
manager.set_status(HealthStatus.STOPPING)
assert manager.status == HealthStatus.STOPPING  # ❌ Type narrowing issue

# ✅ Correct - Re-fetch with type annotation
manager.set_status(HealthStatus.HEALTHY)
assert manager.status == HealthStatus.HEALTHY
manager.set_status(HealthStatus.STOPPING)
current_status: HealthStatus = manager.status  # Widen type
assert current_status == HealthStatus.STOPPING
```

### Optional Types Require Null Checks

**Problem**: Accessing attributes on `Optional[T]` without guards fails type checking.

**Solution**: Add explicit null checks before attribute access:

```python
# ❌ Avoid - Task might be None
assert client.heartbeat_task.done()

# ✅ Correct - Null check first
assert client.heartbeat_task is not None
assert client.heartbeat_task.done()
```

### Callable Type Annotations

**Problem**: Generic `Callable` without parameters triggers "missing type parameters" warnings.

**Solution**: Use type aliases with Union for sync/async callbacks:

```python
# ❌ Avoid - Missing type parameters
shutdown_callbacks: list[Callable] = []

# ✅ Correct - Type alias with parameters
from collections.abc import Awaitable, Callable

ShutdownCallback = Callable[[], None] | Callable[[], Awaitable[None]]
shutdown_callbacks: list[ShutdownCallback] = []
```

### FastAPI Lifespan (Modern Pattern)

**Problem**: `@app.on_event()` is deprecated in FastAPI.

**Solution**: Use `lifespan` context manager:

```python
# ❌ Avoid - Deprecated
@app.on_event("startup")
async def startup():
    pass

# ✅ Correct - Lifespan context manager
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    await startup_logic()
    yield
    # Shutdown
    await shutdown_logic()

app = FastAPI(lifespan=lifespan)
```

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
