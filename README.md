# Crank Platform

**A distributed capability-based ML execution platform with controller/worker architecture**

> ✅ **Architecture Refactor: Phases 0-2 Complete** (Nov 2025)
> Worker runtime and capability schema foundation complete. Phase 3 (controller extraction) ready to start.
> See `docs/planning/CONTROLLER_WORKER_REFACTOR_PLAN.md` | Old architecture: `archive/2025-11-09-pre-controller-refactor/`

## Architecture Vision

Crank Platform implements a **controller + worker + capability** model for distributed ML workloads:

- **Crank-Node**: Host environment capable of running workers + controller
- **Crank-Controller**: Supervisory process managing workers, trust, routing (one per node)
- **Crank-Worker**: Runtime component providing capabilities
- **Crank-Capability**: Declared function a worker provides (routing key)
- **Crank-Job**: Request for work routed by capability
- **Mesh**: Distributed network of controllers sharing capability/health/load info

### Design Principles

1. **Workers are not containers** - Logical providers; execution strategy varies (containers, native, hybrid)
2. **Capabilities are source of truth** - Routing correctness over service discovery
3. **Controller is the only privileged component** - Workers operate in restricted sandbox
4. **Mesh coordinates state, not execution** - Work stays local unless explicitly routed

## Current Capabilities

- Email classification and parsing
- Document conversion
- Image classification (CPU and GPU)
- Streaming data processing
- Certificate signing (CSR)

All services communicate over HTTPS with mutual TLS (mTLS) for enhanced security.

## Current Status

**Active Development**: Controller/Worker architecture refactor - **Phases 0-2 Complete** ✅ (Nov 2025)

- ✅ Old architecture archived and functional
- ✅ Migration plan documented (Phases 0-2: [docs/archive/completed/](docs/archive/completed/), Phase 3: [phase-3-controller-extraction.md](docs/planning/phase-3-controller-extraction.md))
- ✅ **Phase 0 Complete** (Nov 10): Capability schema + worker runtime foundation (Issue #27 - closed)
  - 29/29 capability schema tests passing
  - 35/35 worker runtime tests passing
- ✅ **Phase 1 Complete** (Nov 10): Worker migrations - 8 workers using `WorkerApplication` (Issue #28 - closed)
  - Streaming, email classifier, email parser, doc converter, hello world, philosophical analyzer, zettel workers
  - 40.4% code reduction while adding type safety + production features
- ✅ **Phase 2 Complete** (Nov 10): Base worker image + hybrid deployment + E2E tests (Issue #29 - closed)
  - `Dockerfile.worker-base` eliminates 40+ lines per worker
  - Makefile targets for native macOS execution
  - CI builds all workers from base image
- 🔜 **Phase 3 Ready**: Extract controller from platform (Issue #30 - foundation complete)
- ⏳ **Phase 4**: Integration tests & documentation (Issue #31)

## Documentation

### Architecture & Planning

- [**Controller/Worker Architecture**](docs/architecture/controller-worker-model.md) - Core architectural specification
- [**Active Refactor Plan**](docs/planning/phase-3-controller-extraction.md) - Phase 3 implementation (current work)
- [**Enhancement Roadmap**](docs/proposals/enhancement-roadmap.md) - Strategic feature proposals
- [**Philosophy**](philosophy/) - System vision and economic model

### Development

- [**Mascot System**](mascots/README.md) - AI specialist roles (future human+AI collaboration model)
- [**Quick Start**](QUICK_START.md) - Getting started (will be updated for controller architecture)
- [**Requirements**](REQUIREMENTS.md) - Dependencies and setup

### Operations

- [**Security Architecture**](docs/security/) - mTLS, certificates, trust model
- [**Certificate Authority**](docs/certificate-authority-architecture.md) - PKI infrastructure
- [**Anti-Fragile mTLS**](docs/anti-fragile-mtls-strategy.md) - Resilience patterns

## The Mascot System (Future Vision)

> *"Each mascot will eventually be replaced by real humans working with fine-tuned AIs rather than the generic pre-prompt we have now"* - Project Vision

The mascots model our future **controller + specialist** collaboration pattern:

- **🐰 Wendy (Security)** - Future: Security engineer + fine-tuned security AI
- **🦙 Kevin (Portability)** - Future: Platform engineer + fine-tuned deployment AI
- **🦊 Gary (GPU/Performance)** - Future: Performance engineer + fine-tuned optimization AI

Each represents a **capability domain** that will be provided by human+AI workers coordinated by the controller.

Current implementation: `mascots/` directory with AI prompt engineering
Future implementation: Human specialists with personal fine-tuned models, controller coordinates work

See [Mascot Happiness Report](docs/MASCOT_HAPPINESS_REPORT.md) for current status.

## Quick Start (Legacy - Will be Updated)

> ⚠️ Instructions below reference old platform architecture. Will be updated after Phase 3.

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- OpenSSL for certificate generation

### Development Setup

```bash
# Clone repository
git clone https://github.com/crankbird/crank-platform.git
cd crank-platform

# Set up Python environment (automatically installs editable package)
./scripts/dev-universal.sh setup

# OR manually:
uv venv --python 3.11
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync --all-extras
uv pip install -e .  # Install crank.* package in editable mode

# Initialize certificates
python scripts/initialize-certificates.py

# Start development environment
docker-compose -f docker-compose.development.yml up --build
```

**Important**: The `uv pip install -e .` step installs the `crank.*` package in editable mode, which is required for imports to resolve correctly in tests and VS Code. See `pyrightconfig.json` and `.vscode/settings.json` for import path configuration.

### Running Tests

```bash
# Install dependencies (if not already done)
uv sync --all-extras
uv pip install -e .

# Run unit tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

## Deployment Models

**Post-refactor** (from taxonomy document):

1. **Containers** (Windows/Linux/Cloud): Controller + workers in Docker
2. **Hybrid** (macOS): Controller + CPU workers in containers, GPU workers native (Metal support)
3. **Embedded** (iOS/Android): Controller + workers as native libraries
4. **Native** (Raspberry Pi): Controller + workers as system services

## Project Structure

```text
crank-platform/
├── src/crank/                    # Core platform libraries
│   ├── capabilities/             # ✅ Capability schema (Phase 0)
│   ├── worker_runtime/           # ✅ Shared worker base (Phase 0)
│   └── crank_platform/           # Type-safe core (existing)
├── services/                     # Worker implementations
│   ├── Dockerfile.worker-base    # ✅ Shared base image (Phase 2)
│   ├── crank_streaming.py        # ✅ Migrated to WorkerApplication
│   ├── crank_doc_converter.py    # ✅ Migrated to WorkerApplication
│   ├── crank_email_classifier.py # ✅ Migrated to WorkerApplication
│   ├── crank_email_parser.py     # ✅ Migrated to WorkerApplication
│   └── [5 more migrated workers] # ✅ All using worker runtime
├── tests/                        # Test suite
├── docs/                         # Documentation
│   ├── planning/                 # Architecture plans
│   └── architecture/             # Implementation docs
├── mascots/                      # AI specialist system
├── philosophy/                   # Vision documents
├── intellectual-property/        # Patent/IP context
└── archive/                      # Legacy code archives
    └── 2025-11-09-pre-controller-refactor/  # Old platform architecture
```

## Contributing

This project is undergoing major architectural refactor. If contributing:

1. Read architecture overview: [controller-worker-model.md](docs/architecture/controller-worker-model.md) and active work: [phase-3-controller-extraction.md](docs/planning/phase-3-controller-extraction.md)
2. Check active Phase in GitHub Issues (#27-#31)
3. New code should follow controller/worker pattern, not archived patterns
4. Tests must validate capability-based routing

## License

[Your License Here]

## Contact

[Your Contact Info]

---

**"The Fat Controller coordinates the workers, but the workers do the real work."** 🚂
