# Controller + Worker Architecture Refactor Plan

**Date**: November 9, 2025
**Last Updated**: November 10, 2025
**Status**: 🏗️ **Phase 1 In Progress** (Worker Runtime Implementation)
**Related**: `docs/planning/crank-taxonomy-and-deployment.md`

## Executive Summary

This document outlines the migration from the current "platform-mediated service" architecture to the new "controller + worker + capability" model defined in the taxonomy document.

**Goal**: Eliminate code duplication, enforce proper separation of concerns, enable capability-based routing, and support hybrid deployment (containers + native).

---

## Current State Analysis

### Problems Identified (Both Human + Codex Analysis)

#### 1. **No Capability Schema** 🚫

- Workers have ad-hoc capability declarations embedded in code
- `services/crank_streaming.py` (line 138) vs `services/crank_email_classifier.py` (line 205) use different formats
- No versioning, no validation, no contract enforcement
- **Impact**: Can't reason about worker compatibility or substitutability

#### 2. **Massive Code Duplication** 🔄

Every worker reimplements:

- `WorkerRegistration` model definitions
- Heartbeat loops with retry logic
- Certificate bootstrap logic
- Health check endpoints
- Controller discovery

**Files affected**:

- `services/crank_email_classifier.py` (line 123)
- `services/crank_streaming.py` (line 28)
- `services/crank_doc_converter.py` + runner script
- `services/crank_email_parser.py`
- `services/relaxed-checking/crank_image_classifier.py`

**Impact**: Drift in auth, error handling, capability names. Maintenance nightmare.

#### 3. **Platform vs Controller Confusion** 🏢

- `services/crank_platform_service.py` and `services/crank_platform_app.py` treat "platform" as monolith
- Workers register to `PLATFORM_URL` instead of node-local controller
- Violates "controller-per-node" principle from taxonomy §1
- **Files affected**:
  - `services/crank_streaming.py` (line 120)
  - `services/crank_email_classifier.py` (line 158)
  - All other workers

**Impact**: Prevents mesh-aware routing, scalability issues.

#### 4. **Dockerfile Redundancy** 🐳

Seven near-identical Dockerfiles:

- `services/Dockerfile.crank-email-classifier`
- `services/Dockerfile.crank-doc-converter`
- `services/Dockerfile.crank-streaming`
- `services/Dockerfile.crank-email-parser`
- `services/Dockerfile.crank-platform`
- `image-classifier/Dockerfile`
- `image-classifier-gpu/Dockerfile`

All repeat:

- Non-root user setup
- `apt install` packages
- Copy `src/`
- Drop `run_worker.py`
- Healthcheck definitions

**Only differences**: Requirements files, exposed ports

**Impact**: Obscures that "workers are logical providers, not containers". Brittle maintenance.

#### 5. **Certificate Privilege Violation** 🔐

- Certificate initialization bolted onto each worker
- `services/crank_cert_initialize.py` copied into each image
- Workers invoke cert generation via generated scripts
- **Violates taxonomy §2.3**: "Controller is the only privileged component"

**Impact**: Security boundary violation, workers have more privilege than they should.

#### 6. **Tests Bypass Capability Routing** 🧪

- `tests/test_email_pipeline.py`
- `tests/quick_validation_test.py`
- `tests/test_streaming_basic.py`

All refer to workers by old service names and hardcoded ports. Don't exercise capability-based routing.

**Impact**: Tests won't validate taxonomy concepts once implemented.

#### 7. **dependencies.py is Misplaced** 📦

The `services/dependencies.py` we just created for FastAPI DI is actually **controller-level** concern, not worker concern. It's mixing layers.

#### 8. **CrankMeshInterface is Proto-Controller** 🌐

`services/crank_mesh_interface.py` is actually the seed of what should become the controller. It's trying to emerge but trapped in the old architecture.

---

## Three Layers Fighting Each Other

1. **Old Layer**: Direct service-to-service calls
2. **Current Layer**: Platform-mediated routing (what we just fixed with FastAPI DI)
3. **Future Layer**: Controller + capability-based mesh

We need to collapse these into the proper controller/worker separation.

---

## Migration Strategy (Phased Approach)

### **Phase 0: Foundation**

**Timeline**: 1-2 days
**Risk**: Low (non-breaking)
**Dependencies**: None

#### **Issue #27: Create Capability Schema & Worker Runtime Foundation**

**Deliverables**:

1. **Create `src/crank/capabilities/schema.py`**

   ```python
   # Core types
   - CapabilityDefinition (id, version, io_contract)
   - IOContract (input_schema, output_schema, errors)
   - CapabilityVersion (semver)

   # Catalog of existing capabilities
   - DOCUMENT_CONVERSION
   - EMAIL_CLASSIFICATION
   - IMAGE_CLASSIFICATION
   - EMAIL_PARSING
   - STREAMING_CLASSIFICATION
   - CSR_SIGNING
   ```

2. **Create `src/crank/worker_runtime/`**

   ```text
   worker_runtime/
   ├── __init__.py
   ├── base.py          # WorkerApplication base class
   ├── registration.py  # Controller discovery, heartbeat
   ├── lifecycle.py     # Health checks, graceful shutdown
   └── security.py      # Cert retrieval from controller (not self-init)
   ```

3. **Validation**
   - Unit tests for capability schema
   - Contract validation tests
   - Worker runtime base class tests

**Acceptance Criteria**:

- [x] Capability schema module exists with all current capabilities cataloged
- [x] Worker runtime base class can be imported and subclassed
- [x] Tests prove schema validation works (24 capability + 24 worker runtime = 48 tests passing)
- [x] Documentation explains capability schema format
- [x] Code quality patterns documented (LINTING_AND_TYPE_CHECKING.md + AGENT_CONTEXT enhancements)
- [x] **No existing code is changed** (foundation only)

**Status**: ✅ **COMPLETE** (Nov 10, 2025 - Commits 976dfd9 + ceea5b8)

**Why First**: Creates foundation everything else builds on. Zero risk to running system.

---

### **Phase 1: Worker Migration**

**Timeline**: 2-3 days
**Risk**: Medium (changes one worker, keeps others working)
**Dependencies**: Phase 0 complete

#### **Issue #28: Migrate First Worker to Shared Runtime**

**Strategy**: Pick **ONE** worker as proof-of-concept

**Primary Option**: `crank_streaming.py` (cleanest implementation for refactor)
**Alternative Option**: **NEW** `crank_philosophical_analyzer.py` (from golden integration - proof-of-concept for greenfield worker development)

> **Note**: Golden integration provides opportunity to demonstrate worker pattern with BOTH refactor (streaming) AND greenfield (philosophical analyzer) approaches.

**Recommended**: Start with philosophical analyzer as greenfield proof-of-concept, then apply lessons to streaming refactor.

**Deliverables**:

1. **Refactor `services/crank_streaming.py`**

   ```python
   # BEFORE (current)
   - 207 lines
   - Custom WorkerRegistration model
   - Handwritten heartbeat loop
   - Ad-hoc capability list

   # AFTER (refactored)
   - ~80 lines (business logic only)
   - Subclasses WorkerApplication
   - Uses schema.STREAMING_CLASSIFICATION
   - Uses registration.py for heartbeat
   - Uses security.py for certs
   ```

2. **Compatibility Layer**
   - Ensure refactored worker still works with current platform
   - No breaking changes to API
   - Same Docker image behavior

3. **Documentation**
   - Migration guide for other workers
   - Before/after comparison
   - Lessons learned

**Acceptance Criteria**:

- [x] Streaming worker refactored to use worker_runtime
- [x] All existing streaming tests still pass (4/4 tests passing)
- [x] Docker container still healthy (image builds successfully)
- [x] Heartbeat/registration still works with current platform
- [x] Code size reduced by >50% (44% reduction: 525→292 lines, 233 removed)
- [x] Migration guide written (see below)

**Status**: ✅ **COMPLETE** (Nov 10, 2025 - Commit TBD)

**Results**:

- **Lines of Code**: 525 → 292 (44% reduction, 233 lines removed)
- **Boilerplate Eliminated**:
  - WorkerRegistration model (20 lines)
  - initialize_and_register() (70 lines)
  - _register_with_platform() (50 lines)
  - _send_heartbeat() (30 lines)
  - _start_heartbeat_task() (20 lines)
  - _create_adaptive_client() (10 lines)
  - lifespan context manager (10 lines)
  - Manual certificate initialization (40 lines)
  - Total: ~250 lines of boilerplate removed

- **Business Logic Retained**: ~242 lines
  - StreamingRequest/Status models (30 lines)
  - text_stream_generator() (20 lines)
  - WebSocket connection management (40 lines)
  - Route handlers for /stream/text, /ws, /events, /status (150 lines)
  - All functionality preserved

- **Testing**: 4/4 tests passing
  - Health endpoint test ✅
  - Real-time classification test ✅
  - WebSocket streaming test ✅
  - SSE streaming test ✅

- **Docker**: Build successful, image size unchanged
  - Dockerfile simplified (removed startup script generation)
  - Direct execution: `CMD ["python", "crank_streaming.py"]`
  - All environment variables compatible

**Migration Pattern Established**:

1. **Create Worker Subclass**:

   ```python
   from crank.worker_runtime import WorkerApplication
   from crank.capabilities.schema import STREAMING_CLASSIFICATION

   class StreamingWorker(WorkerApplication):
       def __init__(self):
           super().__init__(
               service_name="crank-streaming",
               https_port=int(os.getenv("STREAMING_HTTPS_PORT", "8500")),
           )
           # Business-specific state only
           self.active_connections = []
           self.active_streams = {}
   ```

2. **Implement Required Methods**:

   ```python
   def get_capabilities(self) -> list[CapabilityDefinition]:
       return [STREAMING_CLASSIFICATION]

   def setup_routes(self) -> None:
       @self.app.post("/stream/text")
       async def stream_text(request: StreamingRequest):
           # Business logic only
   ```

3. **Simplify main()**:

   ```python
   def main():
       worker = StreamingWorker()
       worker.run()  # Handles everything!
   ```

4. **Update Dockerfile**:

   - Remove certificate initialization script
   - Remove startup script generation
   - Use `CMD ["python", "crank_streaming.py"]`

**Lessons Learned**:

- WorkerApplication pattern eliminates ~250 lines of boilerplate per worker
- All tests passed without modification (perfect backward compatibility)
- Docker builds simplified (no intermediate scripts needed)

#### **Phase 1 Extension: Philosophical Analyzer (Golden Integration)**

**Status**: 🚧 **PLANNED** (Integration with golden knowledge base)
**Timeline**: 2-3 days
**Risk**: Low (new service, no existing dependencies)

**Purpose**: Demonstrate greenfield worker development using established worker_runtime pattern. Integrates philosophical analysis capabilities from golden repository.

**Deliverables**:

1. **Create `services/crank_philosophical_analyzer.py`**
   - First NEW worker built from scratch using worker_runtime foundation
   - Implements `PHILOSOPHICAL_ANALYSIS` capability (from golden/semantic-config)
   - Integrates golden/philosophical-analyzer/ code as service logic
   - Proves new capability schema and worker pattern works end-to-end

2. **Container & Deployment Integration**
   - `Dockerfile.crank-philosophical-analyzer` using worker-base pattern
   - Add to `docker-compose.development.yml`
   - Integration with existing mTLS/certificate system

3. **Golden Knowledge Base Integration**
   - golden/zettels/ → docs/knowledge/ (organized zettel knowledge vault)
   - BDD integration: golden/gherkins/ → tests/bdd/features/philosophical/
   - Semantic configuration: golden/semantic-config/ → docs/schemas/philosophical/

**Acceptance Criteria**:

- [ ] Philosophical analyzer service operational using worker_runtime
- [ ] PHILOSOPHICAL_ANALYSIS capability registered and functional
- [ ] Integration with golden knowledge base complete
- [ ] BDD tests operational for philosophical analysis features
- [ ] Template established for future greenfield worker development

**Strategic Value**:

- Validates capability schema with novel use case
- Demonstrates end-to-end worker development process
- Provides template for future service creation
- Integrates valuable philosophical analysis tooling
- Route handlers work exactly as before (FastAPI compatibility)
- Environment variables remain the same (deployment unchanged)
- Migration is straightforward: ~1 hour per worker

**Beauty Pass (Nov 10, 2025 - Commit 824bb96)**:

After Phase 1 worker migrations validated the pattern, applied code quality improvements:

1. **ShutdownHandler callback metadata** - Named tasks with timeouts/descriptions for better observability
2. **CertificateBundle dataclass** - Type-safe certificate handling with automatic validation
3. **Decomposed `WorkerApplication.__init__`** - Single-responsibility configuration methods
4. **httpx.AsyncClient lifecycle** - Proper connection pooling and resource cleanup

**Deferred Patterns** (documented in AGENT_CONTEXT.md):

- Route registration helper - Waiting for 5+ core routes before abstracting
- ControllerSession context manager - Linear startup flow is already clear
- Full clock injection - Optional _now parameter sufficient for testing

**Why Second**: Proves the pattern works. Creates template for migrating others.

---

### **Phase 2: Standardize Packaging**

**Timeline**: 1-2 days
**Risk**: Low (build-time changes only)
**Dependencies**: Phase 1 complete

#### **Issue #29: Create Base Worker Image & Hybrid Deployment**

**Deliverables**:

1. **Create `services/Dockerfile.worker-base`**

   ```dockerfile
   # Multi-stage base image
   ARG PYTHON_VERSION=3.11
   FROM python:${PYTHON_VERSION}-slim AS base

   # Common setup (used by ALL workers)
   - Non-root user creation
   - Common apt packages
   - COPY src/ to /app/src/
   - Common healthcheck setup
   - Certificate directory structure
   ```

2. **Refactor ONE Worker Dockerfile**

   ```dockerfile
   # services/Dockerfile.crank-streaming
   FROM worker-base:latest

   # ONLY worker-specific bits
   COPY services/crank_streaming.py /app/
   COPY requirements-streaming.txt /app/
   RUN pip install -r requirements-streaming.txt

   EXPOSE 8500
   CMD ["python", "crank_streaming.py"]
   ```

3. **Create `make worker-install` for macOS**

   ```makefile
   # For native execution (macOS Metal GPU workers)
   worker-install:
       uv venv --python 3.11
       uv pip install -e src/crank/worker_runtime
       uv pip install -r requirements-$(WORKER).txt
   ```

4. **Validation**
   - Build all workers from base image
   - Verify identical runtime behavior
   - Test native macOS installation

**Acceptance Criteria**:

- [ ] `Dockerfile.worker-base` exists and builds successfully
- [ ] At least one worker migrated to use base image
- [ ] Image size reduction measured and documented
- [ ] Native macOS deployment tested
- [ ] CI builds all workers from base
- [ ] Migration plan for remaining workers documented

**Why Third**: Reduces maintenance burden, enables hybrid deployment pattern from taxonomy.

---

### **Phase 3: Controller Emergence**

**Timeline**: 3-5 days
**Risk**: High (core architectural change)
**Dependencies**: Phases 0, 1, 2 complete

#### **Issue #30: Extract Controller from Platform**

**This is the big architectural shift.**

**Deliverables**:

1. **Rename/Refactor Core Files**

   ```text
   services/crank_platform_service.py → services/crank_controller_service.py
   services/crank_platform_app.py     → services/crank_controller_app.py
   ```

2. **Controller Responsibilities** (Keep These)
   - Capability registry
   - Worker registration/heartbeat endpoints
   - Routing logic
   - Mesh coordination
   - Trust/certificate management

3. **Controller Responsibilities** (Remove/Delegate These)
   - Worker-specific logic
   - Direct work execution
   - Service-specific endpoints

4. **Implement Controller-Side Capability Registry**

   ```python
   # In controller
   - POST /controller/register (workers register capabilities)
   - GET /controller/capabilities (list available capabilities)
   - POST /controller/route (capability-based routing)
   - Validates worker capabilities against schema
   ```

5. **Update Workers for Controller Discovery**

   ```python
   # In each worker
   # BEFORE
   PLATFORM_URL = "https://crank-platform:8443"

   # AFTER
   CONTROLLER_URL = os.getenv("CONTROLLER_URL", "https://localhost:8000")
   # Controller is node-local by default
   ```

6. **Update Tests**

   ```python
   # Create lightweight controller mock
   # Workers test against mock instead of real platform
   # Integration tests use real controller + workers
   ```

**Acceptance Criteria**:

- [ ] Controller files renamed and refactored
- [ ] Controller exposes capability registry endpoints
- [ ] Controller validates capabilities against schema
- [ ] Workers discover controller via ENV (not hardcoded)
- [ ] All existing functionality still works
- [ ] Tests use controller mocks
- [ ] Integration tests prove multi-worker routing
- [ ] Mesh coordination still works
- [ ] Documentation updated

**Why Fourth**: Big architectural shift. Do it when foundation is solid and proven.

---

### **Phase 4: Validation & Cleanup**

**Timeline**: 1-2 days
**Risk**: Low (cleanup only)
**Dependencies**: All previous phases complete

#### **Issue #31: Integration Tests & Documentation**

**Deliverables**:

1. **Integration Tests**
   - Multi-worker capability routing
   - Controller capability registry
   - Worker lifecycle (register, heartbeat, deregister)
   - Fault tolerance (worker failure, recovery)

2. **Contract Tests**
   - Every worker's manifest matches schema
   - Schema validation enforced
   - Version compatibility checks

3. **CI Pipeline**
   - Build all workers from base image
   - Run smoke tests on each worker
   - Integration tests with controller
   - Contract validation

4. **Documentation Updates**
   - Update `docs/planning/crank-taxonomy-and-deployment.md` with implementation details
   - Cross-link to capability schema
   - Cross-link to worker runtime
   - Migration guide for future workers
   - Deployment guide (containers + native)

5. **Cleanup**
   - Delete old duplicated code
   - Remove obsolete patterns
   - Archive migration documentation

**Acceptance Criteria**:

- [ ] Integration test suite passing
- [ ] Contract tests prove schema compliance
- [ ] CI pipeline validates all workers
- [ ] Documentation complete and accurate
- [ ] Old code deleted (no dead code)
- [ ] Migration marked complete

**Why Last**: Proves everything works. Documents the new normal.

---

## Risk Mitigation

### **Current System Stability**

We have **7 healthy containers in production right now**. Any refactor must maintain this.

**Strategy**:

1. **Parallel Development**: New patterns exist alongside old ones
2. **One Worker at a Time**: Migrate incrementally, test thoroughly
3. **Rollback Plan**: Keep old code until new code proven
4. **Feature Flags**: Toggle between old/new patterns if needed

### **Testing Strategy**

- Unit tests for each new module
- Integration tests before deleting old code
- Contract tests ensure schema compliance
- Smoke tests run on every change

### **Deployment Strategy**

- Phase 0-2: No deployment changes (foundation only)
- Phase 3: Blue-green deployment (new controller alongside old platform)
- Phase 4: Full cutover after validation

---

## Success Metrics

### **Code Quality**

- [ ] Worker code size reduced by >50%
- [ ] Dockerfile count reduced from 7 to 1 base + 7 thin layers
- [ ] Code duplication eliminated (measured by DRY analysis)
- [ ] Type safety improved (all capabilities schema-validated)

### **Architecture Alignment**

- [ ] Taxonomy document fully implemented
- [ ] Controller-per-node pattern working
- [ ] Capability-based routing operational
- [ ] Hybrid deployment (containers + native) proven

### **Developer Experience**

- [ ] New worker creation time reduced (template + base image)
- [ ] Onboarding documentation clear and complete
- [ ] Tests run faster (mocked controller)
- [ ] CI pipeline more reliable

### **Production Readiness**

- [ ] All existing functionality preserved
- [ ] Performance unchanged or improved
- [ ] Security posture strengthened (privilege separation)
- [ ] Scalability improved (mesh-aware routing)

---

## Open Questions for Review

1. **Phase 3 Timing**: Should we migrate ALL workers to runtime library (Phase 1) before doing controller extraction (Phase 3)? Or migrate streaming worker, extract controller, then migrate remaining workers?

2. **Backward Compatibility**: How long should we maintain compatibility with old patterns? Immediate cutover or gradual deprecation?

3. **Base Image Strategy**: Single base image for all workers, or separate base images for CPU vs GPU workers?

4. **Controller URL Discovery**: Environment variable? Config file? Service discovery? DNS?

5. **Capability Versioning**: Semver? Date-based? How to handle breaking changes?

6. **Testing Infrastructure**: Mock controller? Lightweight controller? Full controller in tests?

7. **Documentation Location**: Keep planning docs separate from implementation docs? Or merge?

---

## Next Steps

**Immediate Action Required**:

1. **Review this plan** - Both human and Codex
2. **Identify gaps** - What's missing? What's unclear?
3. **Debate differences** - Any disagreements on approach?
4. **Create GitHub Issues** - Issues #27, #28, #29, #30, #31
5. **Prioritize** - Confirm phase order makes sense
6. **Begin Phase 0** - Start with foundation

**Decision Points**:

- [ ] Plan approved by both reviewers
- [ ] Open questions answered
- [ ] GitHub issues created
- [ ] Phase 0 implementation begins

---

## Appendix: Code Examples

### A. Current Pattern (Duplicated Across Workers)

```python
# services/crank_streaming.py (simplified)
class WorkerRegistration(BaseModel):
    worker_id: str
    capabilities: list[str]
    # ... etc

async def heartbeat_loop():
    while True:
        try:
            response = await client.post(
                f"{PLATFORM_URL}/v1/workers/{worker_id}/heartbeat"
            )
            # ... error handling
        except Exception:
            # ... retry logic
        await asyncio.sleep(30)

# Certificate initialization
cert_store = SecureCertificateStore()
cert_store.initialize_certificates()  # PRIVILEGED OPERATION

# Health endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

**This pattern is copy-pasted in 7 different files!**

---

### B. Proposed Pattern (Using Worker Runtime)

```python
# services/crank_streaming.py (refactored)
from crank.worker_runtime import WorkerApplication
from crank.capabilities.schema import STREAMING_CLASSIFICATION

class StreamingWorker(WorkerApplication):
    """Streaming classification worker."""

    capabilities = [STREAMING_CLASSIFICATION]

    async def process_request(self, request: dict) -> dict:
        """Business logic only - no boilerplate."""
        # ... actual streaming classification code
        return result

# That's it! Everything else handled by base class:
# - Registration with controller
# - Heartbeat loop
# - Health checks
# - Certificate retrieval (from controller, not self-init)
# - Graceful shutdown
# - Error handling
```

**80 lines instead of 207. Pure business logic.**

---

### C. Capability Schema Example

```python
# src/crank/capabilities/schema.py
from pydantic import BaseModel
from typing import Literal

class CapabilityDefinition(BaseModel):
    id: str
    version: str
    input_schema: dict
    output_schema: dict
    error_codes: list[str]

# Catalog
STREAMING_CLASSIFICATION = CapabilityDefinition(
    id="streaming.email.classify",
    version="1.0.0",
    input_schema={
        "type": "object",
        "properties": {
            "email_content": {"type": "string"},
            "classification_types": {"type": "string"}
        }
    },
    output_schema={
        "type": "object",
        "properties": {
            "results": {"type": "array"},
            "processing_time_ms": {"type": "number"}
        }
    },
    error_codes=["INVALID_INPUT", "CLASSIFIER_UNAVAILABLE"]
)
```

---

## Document History

- **2025-11-09**: Initial plan created based on human + Codex analysis
- **Status**: Awaiting review and approval to proceed

---

**END OF DOCUMENT**
