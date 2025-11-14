# Crank Platform - AI Coding Agent Instructions

## 📋 Essential Reading

- **Primary agent context**: `.vscode/AGENT_CONTEXT.md` (comprehensive rules and patterns)
- **Architecture roadmap**: `docs/planning/CONTROLLER_WORKER_REFACTOR_PLAN.md`

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

## 🎯 Development Patterns

### Package Structure (Import-Critical)

```python
# Always use editable install: uv pip install -e .
from crank.capabilities import CapabilitySchema  # NEW: Phase 0
from crank.worker_runtime import BaseWorker     # NEW: Phase 0
from crank.typing_interfaces import *           # Core types
```

**Setup**: Run `./scripts/dev-universal.sh setup` for complete environment or manual `uv sync --all-extras && uv pip install -e .`

### Worker Development (NEW Pattern)

Workers should inherit from `src/crank/worker_runtime/` base classes, NOT duplicate registration/heartbeat logic found in legacy `services/crank_*.py` files.

```python
# NEW: Use shared runtime (Phase 1+)
from crank.worker_runtime import BaseWorker
from crank.capabilities import CapabilitySchema

# LEGACY: Avoid duplicating this pattern
class SomeWorker:
    def __init__(self):
        self._setup_heartbeat()  # ❌ Code duplication
        self._setup_certificates()  # ❌ Code duplication
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

### Certificate-First Security

All services use **mutual TLS (mTLS)**:

- Initialize: `python scripts/initialize-certificates.py`
- Certificate authority: Service on port 9090
- All worker communication: HTTPS with client certs
- Config: `HTTPS_ONLY=true` in all environments

## 🧪 Testing Framework

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

- **Architecture docs**: `docs/planning/CONTROLLER_WORKER_REFACTOR_PLAN.md`
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
| Import errors (`crank.*` not found) | Run `uv pip install -e .` from project root |
| Type errors in tests | Add `-> None` return annotation to all test functions |
| Pylance "not accessed" warnings | Use explicit route binding: `app.get("/path")(handler)` |
| Certificate failures | Initialize: `python scripts/initialize-certificates.py` |
| Worker registration duplication | Subclass `WorkerApplication`, don't copy legacy patterns |
| Deployment inconsistencies | Use `deployment/worker-migration-checklist.yml` template |

## 💡 AI Agent Workflow

1. **Check refactor phase** in GitHub Issues #27-#31
2. **Read architecture docs** before major changes
3. **Review deployment patterns** from unified Sonnet+Codex worker analysis
4. **Use mascot testing** for specialized validation
5. **Follow NEW patterns** from `src/crank/*`, not legacy `services/*`
6. **Test with certificates** using development compose files
7. **Verify deployment artifacts** (Docker, CI, plugin manifests) updated together
