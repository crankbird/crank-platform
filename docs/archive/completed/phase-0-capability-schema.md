# Phase 0: Capability Schema & Worker Runtime Foundation

**Type**: Completed Refactor Phase
**Status**: ✅ Complete (November 10, 2025)
**Temporal Context**: Historical - Lessons Learned
**Related Issues**: #27
**Commits**: 976dfd9, ceea5b8

---

## Overview

Created the foundation for the controller/worker architecture refactor by establishing capability schema and worker runtime base classes. This phase was non-breaking - no existing code was changed, only new infrastructure added.

## Deliverables

### 1. Capability Schema (`src/crank/capabilities/schema.py`)

Created core types:

- `CapabilityDefinition` - Declares what a worker can do
- `IOContract` - Input/output schema validation
- `CapabilityVersion` - Semantic versioning

Cataloged 6 existing capabilities:

- `DOCUMENT_CONVERSION`
- `EMAIL_CLASSIFICATION`
- `IMAGE_CLASSIFICATION`
- `EMAIL_PARSING`
- `STREAMING_CLASSIFICATION`
- `CSR_SIGNING`
- `PHILOSOPHICAL_ANALYSIS` (from golden integration)
- `CODEX_ZETTEL_REPOSITORY` (zettel management)

### 2. Worker Runtime (`src/crank/worker_runtime/`)

Created shared infrastructure to eliminate code duplication:

```text
worker_runtime/
├── __init__.py
├── base.py          # WorkerApplication base class
├── registration.py  # Controller discovery, heartbeat
├── lifecycle.py     # Health checks, graceful shutdown
└── security.py      # Cert retrieval from controller
```

## Test Results

**64 tests passing** (as of Phase 2 completion):

- 29 capability schema tests
- 35 worker runtime tests

Test coverage validates:

- Schema validation works correctly
- Contract enforcement prevents invalid capabilities
- Worker base class can be imported and subclassed
- All capability IDs are unique and valid

## Code Quality Documentation

Enhanced during this phase:

- `docs/development/LINTING_AND_TYPE_CHECKING.md` - Established type safety patterns
- `.vscode/AGENT_CONTEXT.md` - Updated with worker development patterns

## Key Lessons Learned

### What Worked Well

1. **Non-Breaking Foundation** - Adding new infrastructure without changing existing code eliminated risk
2. **Type Safety First** - Using Pydantic for capability schema caught errors early
3. **Test-Driven** - Writing tests before migrating workers validated the foundation
4. **Documentation Concurrent** - Documenting patterns while building prevented knowledge loss

### Challenges Encountered

1. **Import Paths** - Needed to ensure `uv pip install -e .` for editable install
2. **Enum Comparisons** - Required `.value` for string comparisons (type safety)
3. **FastAPI Route Binding** - Explicit binding pattern needed to avoid Pylance warnings

### Design Decisions

**Capability Schema Format**:

- Chose JSON Schema over custom DSL for input/output validation
- Used semantic versioning for capability versions
- Made error codes explicit rather than inferred

**Worker Runtime Architecture**:

- Inheritance-based (`WorkerApplication` base class) rather than composition
- Shared lifecycle management (health, shutdown, heartbeat)
- Certificate retrieval from controller (not self-initialization)

## Impact Metrics

- **Code Reduction**: Foundation enabled 40.4% reduction in worker code (measured in Phase 1)
- **Duplication Eliminated**: 7 workers no longer duplicate registration/heartbeat logic
- **Type Safety**: 100% of capabilities now schema-validated
- **Developer Experience**: New workers use template + base class (1 hour vs 1 day)

## Next Phase

Phase 1 (Worker Migration) built on this foundation by refactoring existing workers to use the shared runtime, validating the architecture with real production code.

---

**Verified Complete**: November 14, 2025 (64/64 tests passing)
