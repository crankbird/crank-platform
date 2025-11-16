# Phase 3 Session 1: Capability Registry - COMPLETE ✅

**Date**: November 16, 2025  
**Status**: All deliverables complete, 18/18 tests passing, type-clean  
**Issue**: [#30 - Phase 3: Controller Extraction](https://github.com/crankbird/crank-platform/issues/30)

## Executive Summary

Successfully implemented the **Capability Registry** - the core routing engine for the controller/worker architecture. This is the foundation for Phase 3's controller extraction from the platform.

**Key Achievement**: Created a production-ready registry with **12 future-proof schema fields** supporting 6+ strategic proposals while maintaining clean implementation (402 lines core + 447 lines tests).

## Deliverables

### 1. Core Implementation

**File**: `src/crank/controller/capability_registry.py` (402 lines)

#### CapabilitySchema (Extended)
- **Core fields (Phase 0)**: `name`, `verb`, `version`, `input_schema`, `output_schema`, `requires_gpu`, `max_concurrency`
- **FaaS metadata**: `runtime`, `env_profile`, `constraints` (faas-worker-specification.md)
- **SLO constraints**: `slo` (enhancement-roadmap.md)
- **Identity/CAP**: `spiffe_id`, `required_capabilities` (crank-mesh-access-model-evolution.md)
- **Economic routing**: `cost_tokens_per_invocation`, `slo_bid` (from-job-scheduling-to-capability-markets.md)
- **Multi-controller**: `controller_affinity` (enhancement-roadmap.md)

#### WorkerEndpoint
- Health tracking with configurable timeout (default: 120s)
- Heartbeat timestamps
- JSONL serialization (`to_dict()`, `from_dict()`)

#### CapabilityRegistry
Public API:
- `register(worker_id, worker_url, capabilities)` - Worker registration
- `heartbeat(worker_id)` - Update liveness
- `deregister(worker_id)` - Graceful shutdown
- `route(verb, capability, [slo], [identity], [budget])` - Routing with future hooks
- `cleanup_stale()` - Remove unhealthy workers
- `get_all_capabilities()` - Introspection (capability → worker counts)
- `get_all_workers()` - Introspection (all workers with health status)

Multi-controller scaffolding:
- `export_state()` - Serialize for controller sync
- `import_remote_state(controller_id, state)` - Merge remote state (stub)

Persistence (ADR-0005):
- `_save_state()` - JSONL file-backed state
- `_load_state()` - Warm cache on startup

### 2. Comprehensive Test Suite

**File**: `tests/unit/controller/test_capability_registry.py` (447 lines, 18 tests)

#### Test Coverage
- ✅ Registration: minimal capability, extended capability (all 12 fields), multiple capabilities
- ✅ Routing: find worker, no worker available, multiple workers (returns first healthy)
- ✅ Heartbeat: timestamp updates, unknown worker rejection
- ✅ Staleness: timeout detection, cleanup, routing exclusion
- ✅ Deregistration: worker removal
- ✅ Persistence: JSONL save/load, startup recovery
- ✅ Introspection: `get_all_capabilities()`, `get_all_workers()`
- ✅ Multi-controller: `export_state()`, `import_remote_state()` stubs

**Test Results**: 18/18 passing (0.21s execution)

### 3. Documentation Created

**New Documentation**:
- `docs/development/TESTING.md` (380 lines) - Comprehensive testing guide
  - Environment setup requirements (why `uv sync && uv pip install -e .` is critical)
  - Common errors and solutions (ModuleNotFoundError, logging patterns)
  - Test writing patterns (AAA, fixtures, parametrization)
  - Logging best practices (format strings, not keyword args)
  - Debugging techniques (VS Code, pdb, verbose output)

**Updated Documentation**:
- `README.md`: Added testing guide reference, proper environment setup instructions
- `.github/copilot-instructions.md`: Testing setup as critical requirement, logging patterns

## Technical Decisions

### 1. Extended Schema (12 Fields)

**Rationale**: Added 12 optional fields to support future proposals without breaking changes.

**Tradeoff**: Slightly more complex schema now vs. avoiding migration later.

**Validation**: All fields optional, Pydantic validates, tests cover extended usage.

### 2. JSONL Persistence (ADR-0005)

**Rationale**: File-backed state for simple recovery, no database dependency.

**Implementation**: One worker per line, `to_dict()`/`from_dict()` serialization.

**Future**: Easy migration to database (same dict format).

### 3. Future Hooks in `route()`

**Pattern**: Accepted `slo_constraints`, `requester_identity`, `budget_tokens` parameters but only implemented simple routing (first healthy worker).

**Rationale**: API stability - callers can pass these now, routing logic added incrementally.

**Comment Documentation**: Inline comments show where SLO filtering, CAP checks, economic routing will be added.

### 4. Type Safety (dict[str, Any])

**Decision**: Use `dict[str, Any]` instead of bare `dict` for all type hints.

**Validation**: Pylance strict mode clean, no type errors.

**Benefit**: Catches type errors at development time, better IDE autocomplete.

### 5. Logging Pattern (Format Strings)

**Decision**: Use `logger.info("msg %s", value)` not `logger.info("msg", value=value)`.

**Rationale**: Python's standard `logging` doesn't support keyword arguments (causes `TypeError`).

**Documentation**: Added to TESTING.md and copilot-instructions.md to prevent future mistakes.

## Environment Setup Discovery

**Problem**: Tests initially failed with import errors despite environment appearing correct.

**Root Cause**: `src/crank/` package structure requires editable install (`uv pip install -e .`) for imports to resolve.

**Trial-and-Error**:
1. `pytest` directly → `ModuleNotFoundError: No module named 'crank'`
2. `uv pip install pydantic` → `ModuleNotFoundError: No module named 'pytest'`
3. `uv run pytest` → `ModuleNotFoundError: No module named 'pydantic'` (wrong interpreter)
4. `uv pip install -e .` → Still errors (incomplete sync)
5. `uv sync --all-extras && uv pip install -e .` → ✅ **Success**

**Solution**: Created comprehensive `docs/development/TESTING.md` documenting:
- Why each step is required
- Common errors and solutions
- Verification commands
- Troubleshooting guide

**Impact**: Future developers (human and AI) won't need to rediscover this.

## Code Quality

### Metrics
- **Lines of Code**: 402 (implementation) + 447 (tests) = 849 total
- **Test Coverage**: 18 tests covering all public methods + internal state
- **Type Safety**: 0 Pylance errors, all functions typed
- **Docstrings**: Complete on all public methods
- **Logging**: Proper format strings, no keyword arguments

### Patterns Followed
- ✅ CLEAN MINIMAL pattern (like WorkerApplication)
- ✅ Type hints on all functions (including `-> None` on tests)
- ✅ Pydantic validation for schemas
- ✅ Dataclasses for structured data (WorkerEndpoint)
- ✅ Private methods prefixed with `_` (Pylance warnings in tests are acceptable)

### Future-Proofing
- ✅ Extended schema supports 6+ proposals without breaking changes
- ✅ Route method accepts future parameters (SLO, CAP, economic)
- ✅ Multi-controller scaffolding (export/import state)
- ✅ Comment documentation for future hook points

## Next Steps (Phase 3 Session 2)

**Goal**: Create `services/crank_controller.py` - the FastAPI service wrapping the registry.

**Deliverables**:
1. Controller service using `WorkerApplication` base
2. FastAPI endpoints:
   - `POST /register` - Worker registration
   - `POST /heartbeat` - Worker heartbeat
   - `DELETE /deregister` - Worker deregistration
   - `POST /route` - Capability routing
   - `GET /health` - Controller health
3. OpenTelemetry instrumentation
4. Integration test: One worker registers successfully

**Depends On**: This session's registry implementation ✅

## Lessons Learned

### For Future AI Agents

1. **Environment Setup is Critical**: Document `uv sync --all-extras && uv pip install -e .` requirement prominently. Tests will fail mysteriously without it.

2. **Logging Patterns**: Python's standard logging uses format strings (`%s`), not keyword arguments. This is a common mistake that causes `TypeError`.

3. **Type Hints Matter**: Pylance strict mode catches issues early. Use `dict[str, Any]` not bare `dict`.

4. **Test Internal State**: Protected member access in tests (`registry._workers`) is acceptable for unit testing - Pylance warnings are just style guidance.

5. **Future-Proof Schemas**: Adding optional fields now (even if unused) prevents breaking changes later. Pydantic makes this safe.

### For Human Developers

1. **Testing Documentation**: The trial-and-error to get tests running consumed significant effort. `docs/development/TESTING.md` prevents this for everyone.

2. **Type Safety Pays Off**: Comprehensive type hints caught several bugs during development (dict types, optional handling).

3. **JSONL is Underrated**: Simple line-delimited JSON for state persistence is easy to debug, easy to migrate, no dependencies.

## References

- **ADR-0023**: Capability Publishing Protocol (foundation for this registry)
- **ADR-0005**: File-Backed State (JSONL persistence pattern)
- **Phase 3 Attack Plan**: `docs/planning/phase-3-controller-extraction.md`
- **Testing Guide**: `docs/development/TESTING.md` (created this session)
- **Logging Guide**: `docs/development/LINTING_AND_TYPE_CHECKING.md` (updated with logging patterns)

---

**Status**: Ready for Codex review and Session 2 commencement.
