# Crank Platform - AI Coding Agent Instructions

## 📋 Essential Reading

- **Primary agent context**: `.vscode/AGENT_CONTEXT.md` (comprehensive rules and patterns)
- **Architecture roadmap**: `docs/planning/CONTROLLER_WORKER_REFACTOR_PLAN.md`

## 🏗️ Architecture: Controller/Worker Model (Active Refactor)

**CRITICAL**: This platform is migrating from "platform-centric" to "controller + worker + capability" architecture (Nov 2025). Always check the current phase:

- **Phase 0**: Building capability schema + worker runtime foundation (Issue #27)
- **Phase 1**: Migrating first worker (streaming) to shared runtime (Issue #28)
- **Legacy code**: Archived in `archive/2025-11-09-pre-controller-refactor/`

### Core Concepts

1. **Workers** = Logical service providers (not containers)
2. **Controllers** = Node-local supervisors managing workers/routing
3. **Capabilities** = Declared functions workers provide (routing keys)
4. **Mesh** = Distributed network of controllers sharing state

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

## ⚠️ Common Pitfalls

1. **Import Resolution**: Always run `uv pip install -e .` after environment setup
2. **Phase Confusion**: Check refactor status before modifying worker code
3. **Certificate Issues**: Run certificate initialization before any service testing
4. **Legacy Patterns**: Don't copy registration/heartbeat code from existing `services/crank_*.py`

## 💡 AI Agent Workflow

1. **Check refactor phase** in GitHub Issues #27-#31
2. **Read architecture docs** before major changes
3. **Use mascot testing** for specialized validation
4. **Follow NEW patterns** from `src/crank/*`, not legacy `services/*`
5. **Test with certificates** using development compose files
