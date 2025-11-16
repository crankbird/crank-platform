# Crank Platform - AI Coding Agent Instructions

## 📋 Essential Reading

- **Primary agent context**: `.vscode/AGENT_CONTEXT.md` (comprehensive rules and patterns)
- **Architecture roadmap**: `docs/planning/phase-3-controller-extraction.md`

## 🏗️ Architecture: Controller/Worker Model (Active Refactor)

**CRITICAL**: This platform is migrating from "platform-centric" to "controller + worker + capability" architecture (Nov 2025). Always check the current phase:

- ✅ **Phase 0 Complete**: Capability schema + worker runtime foundation (Issue #27, Nov 10 - CLOSED)
- ✅ **Phase 1 Complete**: 8 workers migrated - 40.4% code reduction (Issue #28, Nov 10 - CLOSED)
- ✅ **Phase 2 Complete**: Base worker image + hybrid deployment (Issue #29, Nov 10 - CLOSED)
- 🔜 **Phase 3 Ready**: Controller extraction from platform (Issue #30 - foundation ready)
- **Legacy code**: Archived in `archive/2025-11-09-pre-controller-refactor/`

### Core Concepts

1. **Workers** = Logical service providers (not containers)
2. **Controllers** = Node-local supervisors managing workers/routing
3. **Capabilities** = Declared functions workers provide (routing keys)
4. **Mesh** = Distributed network of controllers sharing state

**Architecture**:

```text
Crank-Node (host environment)
  ├── Controller (supervisor: routing, trust, mesh coordination)
  └── Workers (capability providers: email classification, doc conversion, etc.)
```

**Deployment varies by platform**:

- **macOS**: Hybrid (CPU workers containerized, GPU native for Metal)
- **Windows/Linux**: Full containerization with GPU passthrough
- **Mobile/IoT**: Embedded workers in app sandbox

## 🚨 Security Anti-Patterns (CRITICAL)

**NEVER use these patterns - they violate the HTTPS-only architecture:**

❌ **HTTP URLs**: `http://localhost:9000` → ✅ Use `https://localhost:9000`
❌ **Disabled verification**: `verify=False` → ✅ Use `cert_manager.get_ssl_context()`
❌ **Manual SSL config**: Custom uvicorn SSL → ✅ Use `worker.run()` method
❌ **HTTP in tests**: `TestClient` with http:// → ✅ Use https:// even in tests

**Correct Pattern for HTTP Clients**:

```python
# ✅ CORRECT: HTTPS with mTLS
import httpx
ssl_config = self.cert_manager.get_ssl_context()
async with httpx.AsyncClient(
    cert=(ssl_config["ssl_certfile"], ssl_config["ssl_keyfile"]),
    verify=ssl_config["ssl_ca_certs"],
) as client:
    response = await client.post(f"{url}/endpoint", json=data)

# ❌ WRONG: HTTP or disabled verification
async with httpx.AsyncClient(verify=False) as client:  # NEVER DO THIS
    response = await client.post(f"http://{url}/endpoint", json=data)
```

**Why**: All communication uses HTTPS with mTLS (mutual TLS) - no HTTP capability exists even in development. This is enforced by `HTTPS_ONLY=true` in all environments.

---

## 🎯 Development Patterns

### Package Structure (Import-Critical)

```python
# Always use editable install: uv pip install -e .
from crank.capabilities import CapabilitySchema  # NEW: Phase 0
from crank.worker_runtime import BaseWorker     # NEW: Phase 0
from crank.typing_interfaces import *           # Core types
```

**Setup**: Run `./scripts/dev-universal.sh setup` for complete environment or manual `uv sync --all-extras && uv pip install -e .`

### Worker Development (CLEAN MINIMAL PATTERN)

**Reference**: `services/crank_hello_world.py` - 3-line main function with automatic HTTPS+mTLS

```python
# CLEAN PATTERN (Issue #19 - Nov 2025):
from crank.worker_runtime import WorkerApplication

def main() -> None:
    port = int(os.getenv("WORKER_HTTPS_PORT", "8500"))
    worker = MyWorker(https_port=port)
    worker.run()  # Handles SSL, certificates, uvicorn automatically

if __name__ == "__main__":
    main()
```

**Key Points**:
- Use `WorkerApplication` base class (provides `.run()` method)
- Pass `https_port` to worker `__init__` and to `super().__init__()`
- Call `worker.run()` - it handles SSL/certificates/uvicorn
- `main()` is sync, not async
- Workers automatically get HTTPS+mTLS via `crank.security` module

```python
# LEGACY: Avoid duplicating this pattern
class SomeWorker:
    def __init__(self):
        self._setup_heartbeat()  # ❌ Code duplication
        self._setup_certificates()  # ❌ Code duplication
        # Manual uvicorn config  # ❌ Bypasses SSL setup
```

### Type Safety Patterns

**All pytest functions need return annotations**:

```python
def test_something() -> None:  # ✅ Required
    assert True
```

**Enum comparisons require `.value`**:

```python
assert status.value == "healthy"  # ✅ Correct
assert status == "healthy"        # ❌ Type error
```

**FastAPI route binding** (avoids Pylance "not accessed" warnings):

```python
async def handler() -> JSONResponse:
    return JSONResponse(...)

self.app.get("/health")(handler)  # ✅ Explicit binding instead of @decorator
```

See `docs/development/LINTING_AND_TYPE_CHECKING.md` for complete patterns.

### Certificate-First Security (Issue #19 Complete - Nov 2025)

All services use **unified `crank.security` module** with automatic mTLS:

- **Certificate Authority**: Service on port 9090 (signs worker CSRs)
- **Worker Pattern**: Call `worker.run()` - automatic HTTPS+mTLS setup
- **Certificate Bootstrap**: Workers generate CSR → CA signs → worker stores cert
- **Smart Path Detection**: Auto-detects containers vs native execution
- **All 9 workers**: Production + reference workers using unified security
- Initialize CA: `python scripts/initialize-certificates.py`
- Config: `HTTPS_ONLY=true` in all environments

**Security Consolidation** (675 lines deprecated code removed):
- ✅ `src/crank/security/` - unified security module (7 files)
- ✅ All workers use `WorkerApplication.run()` for automatic SSL
- ✅ Certificate path detection: env → writable dirs → container defaults
- ❌ Never manually configure uvicorn SSL - use `.run()` method

## 🧪 Testing Framework

### Environment Setup (CRITICAL)

**All tests require proper environment setup first**:

```bash
uv sync --all-extras  # Install all dependencies (pytest, etc.)
uv pip install -e .   # Install crank.* package in editable mode
```

**Why**: The `src/crank/` package structure requires editable installation for imports to resolve. Tests will fail with `ModuleNotFoundError` if skipped.

**Always use**: `uv run pytest` not bare `pytest` (ensures correct Python interpreter).

See `docs/development/TESTING.md` for complete guide.

### Mascot-Driven Testing

Use specialized AI testing personas via VS Code tasks:

- **🐰 Wendy**: Security/zero-trust testing (`🐰 Wendy Security Test`)
- **🦙 Kevin**: Portability testing (`🦙 Kevin Portability Test`)
- **🤝 Collaboration**: Multi-mascot testing (`🤝 Mascot Collaboration Test`)
- **🏛️ Full Council**: Complete review (`🏛️ Full Council Review`)

```bash
# Manual execution
python scripts/run_mascot_tests.py --mascot wendy --target src/
```

### Standard Testing

```bash
# Setup first
uv sync --all-extras && uv pip install -e .

# Unit tests
pytest

# Coverage report
pytest --cov=src --cov-report=html
```

## 🚀 Deployment Patterns

### Environment Commands

```bash
# Development (legacy platform architecture)
docker-compose -f docker-compose.development.yml up --build

# GPU development (macOS Metal support)
docker-compose -f docker-compose.gpu-dev.yml up --build

# Production-like
docker-compose -f docker-compose.local-prod.yml up --build
```

### Worker Management (NEW: Phase 2+)

```bash
# Build base worker image
make worker-base

# Build specific worker
make worker-build WORKER=streaming

# Native execution (macOS hybrid deployment)
make worker-install WORKER=streaming
make worker-run WORKER=streaming
```

## 📁 Key File Locations

- **Architecture docs**: `docs/architecture/controller-worker-model.md`
- **Capability schema**: `src/crank/capabilities/` (Phase 0)
- **Worker runtime**: `src/crank/worker_runtime/` (Phase 0)
- **Legacy services**: `services/crank_*.py` (avoid duplicating patterns)
- **Mascot testing**: `mascots/` directory + `scripts/run_mascot_tests.py`
- **Certificate management**: `scripts/initialize-certificates.py`

## 🚨 Deployment Anti-Patterns (Critical)

From unified Sonnet+Codex analysis (`docs/development/AI_DEPLOYMENT_OPERATIONAL_PATTERNS.md`):

1. **Stranded Endpoints**: Refactor capabilities → update controller routing + plugin YAML manifests simultaneously
2. **Missing Dependencies**: Use `crank.testing.ensure_dependency()` for graceful environment checks
3. **Artifact Lag**: Code changes → update Docker, CI, plugin configs together
4. **Metadata Drift**: Follow zettel worker front-matter pattern for artifact storage

**Migration checklist template**: `cp deployment/worker-migration-checklist.yml deployment/migration-{worker}-{date}.yml`

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors (`crank.*` not found) | Run `uv sync --all-extras && uv pip install -e .` from project root |
| `TypeError: Logger._log() got unexpected keyword` | Use `logger.info("msg %s", value)` NOT `logger.info("msg", value=value)` |
| Type errors in tests | Add `-> None` return annotation to all test functions |
| Pylance "not accessed" warnings | Use explicit route binding: `app.get("/path")(handler)` |
| Certificate failures | Initialize: `python scripts/initialize-certificates.py` |
| Worker registration duplication | Subclass `WorkerApplication`, don't copy legacy patterns |
| **Worker runs HTTP not HTTPS** | Use `worker.run()` method, NOT manual uvicorn config |
| **Worker unhealthy in docker** | Ensure `main()` is sync, passes `https_port` to worker |
| **HTTP URL or verify=False** | ❌ SECURITY VIOLATION - use HTTPS + `cert_manager.get_ssl_context()` |
| **422 heartbeat errors** | Send form data (service_type, load_score), not empty POST |
| **Permission denied in container** | Use `--chown=worker:worker` on all COPY commands in Dockerfile |
| Deployment inconsistencies | Use `deployment/worker-migration-checklist.yml` template |

## 💡 AI Agent Workflow

1. **Check refactor phase** in GitHub Issues #27-#31
2. **Read architecture docs** before major changes
3. **Review deployment patterns** from unified Sonnet+Codex worker analysis
4. **Use mascot testing** for specialized validation
5. **Follow NEW patterns** from `src/crank/*`, not legacy `services/*`
6. **Test with certificates** using development compose files
7. **Verify deployment artifacts** (Docker, CI, plugin manifests) updated together
