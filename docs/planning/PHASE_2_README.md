# Phase 2: Base Worker Image & Hybrid Deployment

**Status**: ✅ **IMPLEMENTATION READY** (Nov 10, 2025)

**Goal**: Eliminate Dockerfile duplication and enable native (non-containerized) worker execution per the taxonomy vision.

## What's New

### 1. Base Worker Image (`Dockerfile.worker-base`)

Single base image containing all common worker infrastructure:

- Python 3.11 slim base
- Non-root user (`crank:crank`)
- Common dependencies (FastAPI, uvicorn, httpx, pydantic)
- Shared crank modules (`src/crank/`)
- Certificate directory structure
- Common healthcheck setup

**Benefits**:

- **DRY**: Eliminates 40+ lines of duplication per worker Dockerfile
- **Consistency**: All workers use identical base environment
- **Cache**: Base layers cached, faster worker builds
- **Security**: Consistent user/permissions across workers

### 2. Thin Worker Dockerfiles

Worker-specific Dockerfiles reduced from ~45 lines to ~15 lines:

**Before** (`Dockerfile.crank-streaming`):

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install curl ca-certificates...
RUN groupadd crank && useradd crank...
COPY src/crank /app/src/crank
RUN pip install fastapi uvicorn httpx pydantic...
COPY services/crank_streaming.py /app/
COPY requirements-streaming.txt /app/
RUN pip install -r requirements-streaming.txt
EXPOSE 8500
CMD ["python", "crank_streaming.py"]
```

**After** (`Dockerfile.crank-streaming.new`):

```dockerfile
FROM worker-base:latest
COPY --chown=crank:crank services/crank_streaming.py /app/
COPY --chown=crank:crank requirements-streaming.txt /app/
RUN pip install --no-cache-dir -r requirements-streaming.txt
EXPOSE 8500
CMD ["python", "crank_streaming.py"]
```

### 3. Native Execution (Hybrid Deployment)

New Makefile targets for non-containerized deployment:

```bash
# Install worker in isolated venv
make worker-install WORKER=streaming

# Run worker natively (macOS, Linux, WSL2)
make worker-run WORKER=streaming
```

**Why**:

- **macOS Metal GPU**: Run GPU workers natively for Apple Silicon acceleration
- **Development**: Faster iteration without Docker rebuild
- **Testing**: Validate "workers are not containers" architecture principle
- **Embedded**: Pattern for mobile/Raspberry Pi deployment

## Usage

### Build Base Image

```bash
make worker-base
```

This creates `worker-base:latest` with all common infrastructure.

### Build Worker from Base

```bash
# Streaming worker
make worker-build WORKER=streaming

# Document converter
make worker-build WORKER=doc_converter

# Email classifier
make worker-build WORKER=email_classifier
```

### Native Installation & Execution

```bash
# Install streaming worker natively
make worker-install WORKER=streaming

# Run it (no Docker required)
make worker-run WORKER=streaming
```

Worker runs in isolated venv (`.venv-streaming/`), imports from `src/crank/`, uses WorkerApplication infrastructure.

### Clean Virtual Environments

```bash
make worker-clean
```

## Migration Checklist

**Per Worker**:

- [ ] Create `Dockerfile.crank-{worker}.new` using base image
- [ ] Test build: `make worker-build WORKER={worker}`
- [ ] Test native: `make worker-install WORKER={worker} && make worker-run WORKER={worker}`
- [ ] Verify healthcheck, registration, heartbeat
- [ ] Compare image sizes (base vs old)
- [ ] Validate all tests still pass
- [ ] Rename `.new` to replace old Dockerfile

**Workers to Migrate**:

- [ ] streaming (example provided)
- [ ] doc_converter
- [ ] email_classifier
- [ ] email_parser
- [ ] image_classifier_advanced (GPU - requires WSL2)

## File Structure

```text
crank-platform/
├── services/
│   ├── Dockerfile.worker-base          # NEW: Base image for all workers
│   ├── Dockerfile.crank-streaming.new  # NEW: Thin streaming worker
│   ├── Dockerfile.crank-streaming      # OLD: To be replaced
│   ├── crank_streaming.py              # Worker code (unchanged)
│   └── ...
├── Makefile                             # UPDATED: Phase 2 targets
├── tests/e2e/                           # NEW: E2E test structure
│   ├── doc_converter.feature
│   ├── test_doc_converter_steps.py
│   ├── conftest.py
│   ├── doc_converter_pickle.json
│   └── README.md                        # NEW: E2E testing guide
└── docs/planning/
    ├── PHASE_2_README.md               # This file
    └── REQUIREMENTS_TRACEABILITY.md    # UPDATED: MN-DOC-001 added
```

## E2E Testing Strategy

**Local-First Approach** (Recommended):

1. **Start MCP server locally**: Run `crank-doc-converter` on your machine
2. **Point tests at localhost**: Use MCP client fixture connecting to local server
3. **Fast iteration**: Zero deployment complexity, easy debugging
4. **See**: `tests/e2e/README.md` for detailed testing guide

**Remote Later**:

1. **Deploy to Azure**: Container Apps, App Service, or AKS with mTLS/token auth
2. **Update fixtures**: Point MCP client at HTTPS endpoint
3. **Production validation**: Run same tests against hosted service

**Current State**:

- ✅ Feature file with Gherkin scenarios (`doc_converter.feature`)
- ✅ pytest-bdd step definitions (`test_doc_converter_steps.py`)
- ✅ Mock fixtures for offline development (`conftest.py`)
- ⏳ TODO: Replace mocks with real MCP client, PDF generator, audit reader

**Run Tests**:

```bash
# Install dependencies
pip install pytest pytest-bdd

# Run locally (requires MCP server running)
pytest tests/e2e/test_doc_converter_steps.py -v

# Run with tags
pytest tests/e2e/ -m sync -v  # Only sync tests
pytest tests/e2e/ -m latency -v  # Only latency-critical tests
```

## Success Metrics

- [ ] Base image builds successfully
- [ ] At least one worker migrated and tested
- [ ] Image size reduction measured
- [ ] Native macOS deployment proven
- [ ] CI builds all workers from base
- [ ] Migration plan for remaining workers documented

## Next Steps

1. **Build base image**: `make worker-base`
2. **Migrate streaming worker**: Test `Dockerfile.crank-streaming.new`
3. **Test native execution**: `make worker-install WORKER=streaming`
4. **Measure improvements**: Image size, build time
5. **Update CI**: Build from base in GitHub Actions
6. **Migrate remaining workers**: doc_converter, email_classifier, email_parser
7. **Phase 3**: Extract controller from platform (Issue #30)

## Related Documents

- **Architecture Plan**: `docs/planning/CONTROLLER_WORKER_REFACTOR_PLAN.md`
- **Taxonomy**: `docs/planning/crank-taxonomy-and-deployment.md`
- **Traceability**: `docs/planning/REQUIREMENTS_TRACEABILITY.md` (MN-DOC-001)
- **E2E Tests**: `tests/e2e/doc_converter.feature`
- **Testing Guide**: `tests/e2e/README.md` - Local-first testing strategy, fixture implementation, CI/CD

## Questions?

See Issue #29 in CONTROLLER_WORKER_REFACTOR_PLAN.md for full context and acceptance criteria.
