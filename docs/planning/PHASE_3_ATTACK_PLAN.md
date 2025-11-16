# Phase 3 Attack Plan: Controller Extraction

**Status**: 🚀 **60% Complete** (Sessions 1-3 ✅, Sessions 4-5 pending)
**Goal**: Extract controller from platform, implement capability-based routing (ADR-0023)
**Timeline**: 5 focused sessions (~8-12 hours total)
**Prerequisite**: Phases 0-2 complete ✅
**Completed**: Sessions 1-3 (Nov 15-16, 2025)

---

## Executive Summary

**What**: Separate privileged controller logic from platform service, implement capability registry + routing.

**Why**: Current platform service is a monolith. Controller/worker separation is the foundation for distributed mesh, Cloudflare integration, and scalable architecture.

**How**: 5 incremental sessions, each shippable, each with passing tests.

**ADR-0023 Relationship**: **Session 1-3 implement ADR-0023**. The capability publishing protocol IS the core controller functionality.

**Future-Proofing Strategy**: Phase 3 embeds scaffolding for 6 high-value proposals that depend on the controller. Adding hooks now (while the controller surface is forming) avoids invasive refactoring later:

1. **FaaS Workers** (faas-worker-specification.md, faas-environment-profiles.md)
   - Extended CapabilitySchema: `runtime`, `env_profile`, `constraints`
   - Workers declare execution requirements during registration
   - Session 1: Schema fields, Session 4: Workers can provide metadata

2. **Enterprise Readiness** (enhancement-roadmap.md: SLO files, idempotency, rate limiting, back-pressure)
   - Session 1: `slo` field in CapabilitySchema for SLO constraints
   - Session 3: Idempotency key parameter, rate-limit middleware stubs
   - Session 5: SLO YAML directory structure (`state/controller/slos/`)

3. **Observability** (enhancement-roadmap.md: OpenTelemetry distributed tracing)
   - Session 2: W3C Trace Context propagation, FastAPI auto-instrumentation
   - All endpoints emit spans (console output in Phase 3, Jaeger later)

4. **Multi-Controller Mesh** (enhancement-roadmap.md: peer-to-peer quorum)
   - Session 1: Registry `export_state()` / `import_remote_state()` methods
   - JSONL storage format supports gossip/replication (schema ready)

5. **Security & Authorization** (enterprise-security.md, crank-mesh-access-model-evolution.md: CAP/OPA, SPIFFE)
   - Session 1: `spiffe_id`, `required_capabilities` fields in schema
   - Session 3: Policy evaluation stub in routing (commented hook for OPA/Rego)
   - Session 5: Certificate rotation hooks documented

6. **Economic Routing** (from-job-scheduling-to-capability-markets.md: cost tokens, SLO bids)
   - Session 1: `cost_tokens_per_invocation`, `slo_bid` fields
   - Session 3: Routing accepts `budget_tokens` parameter (stub for market logic)

**Implementation Strategy**: All extended fields/hooks are **optional and commented** in Phase 3. Core functionality (registration, heartbeat, routing) works without them. Future proposals can activate these hooks without schema/API changes.

---

## The 5 Sessions

### ✅ Session 1: Capability Registry (Core of ADR-0023) - COMPLETE
**Time**: 2 hours (actual)
**Goal**: Create registry that tracks worker capabilities
**Status**: ✅ Complete (Nov 15, 2025)
**Deliverable**: `src/crank/controller/capability_registry.py`, 18 tests passing
**Docs**: `docs/planning/phase-3-session-1-COMPLETE.md`

### ✅ Session 2: Controller Service - COMPLETE
**Time**: 1.5 hours (actual)
**Goal**: New controller service with registration endpoint
**Status**: ✅ Complete (Nov 15, 2025)
**Deliverable**: `services/crank_controller.py`, 11 tests passing (Codex-approved)
**Notes**: Refactored to standalone FastAPI app (not WorkerApplication)

### ✅ Session 3: Worker Integration - COMPLETE
**Time**: 2 hours (actual)
**Goal**: Real worker registration with controller
**Status**: ✅ Complete (Nov 16, 2025)
**Deliverable**: `crank_hello_world` worker integration, 4 integration tests passing
**Docs**: `docs/planning/phase-3-session-3-COMPLETE.md`
**Security**: HTTPS-only enforcement validated, anti-patterns documented

### 🔜 Session 4: Migrate Remaining Workers
**Time**: 1.5 hours (estimated)
**Goal**: All 8 remaining workers register with controller
**Status**: Ready to start
**Plan**: Add heartbeat loops, deregistration on shutdown, multi-worker routing

### 🔜 Session 5: Cleanup & Documentation
**Time**: 1 hour (estimated)
**Goal**: Remove controller logic from platform, finalize docs
**Status**: Blocked by Session 4

---

## Session 1: Capability Registry

**Files to Create**:

```
src/crank/controller/
  __init__.py
  capability_registry.py      # The registry (ADR-0023)

tests/unit/controller/
  __init__.py
  test_capability_registry.py  # Unit tests
```

**What the Registry Does** (from ADR-0023):
- Stores capability → worker mappings
- Validates capability schemas (Pydantic)
- Tracks worker heartbeats
- Provides routing lookup (capability → worker URL)
- Cleans up stale workers (no heartbeat > 2 min)
- **Persists state to disk** (JSONL per ADR-0005) for controller restart recovery

**Persistence Strategy** (ADR-0005 compliant):
- On registration/heartbeat: Append to `state/controller/registry.jsonl`
- On controller startup: Load from file (warm cache, but not authoritative)
- **Recovery flow**:
  1. Controller restarts → loads JSONL → marks all workers "needs verification"
  2. Workers send heartbeat (30s interval) → controller returns `worker_not_registered` error
  3. Workers detect error → auto-reregister immediately
  4. Full state recovered within 1 heartbeat cycle (≤30s)
- **Key insight**: Workers actively reregister on heartbeat failure, JSONL is optimization not requirement
- No external database dependency (file-backed like zettel system)

**Extended CapabilitySchema** (future-proof for proposals):

```python
class CapabilitySchema(BaseModel):
    # Core (Phase 0 - already exists)
    name: str
    verb: str
    input_schema: dict
    output_schema: dict
    version: str
    requires_gpu: bool
    max_concurrency: int

    # FaaS metadata (faas-worker-specification.md, faas-environment-profiles.md)
    runtime: str | None = None  # "python", "node", "rust"
    env_profile: str | None = None  # "python-core", "python-ml", "node-standard"
    constraints: dict | None = None  # {"accelerator": "cpu", "timeout_sec": 10, "max_output_bytes": 1MB}

    # SLO constraints (enhancement-roadmap.md: SLO Files per Capability)
    slo: dict | None = None  # {"latency_p95_ms": 100, "availability": 0.999, "error_budget_pct": 1.0}

    # Identity & authorization (crank-mesh-access-model-evolution.md: SPIFFE mapping)
    spiffe_id: str | None = None  # "spiffe://crank.local/worker/streaming"
    required_capabilities: list[str] | None = None  # Capabilities THIS worker needs to call

    # Economic routing (from-job-scheduling-to-capability-markets.md: cost tokens, bids)
    cost_tokens_per_invocation: float | None = None
    slo_bid: dict | None = None  # {"latency_ms": 50, "budget_tokens": 10}

    # Multi-controller replication (enhancement-roadmap.md: multi-node quorum)
    controller_affinity: str | None = None  # Preferred controller ID for sticky routing

class CapabilityRegistry:
    def register(worker_id, worker_url, capabilities: list[CapabilitySchema])
    def route(
        verb: str,
        capability: str,
        slo_constraints: dict | None = None,  # Future: SLO-aware routing
        requester_identity: str | None = None,  # Future: CAP policy evaluation
        budget_tokens: float | None = None  # Future: Economic routing
    ) -> WorkerEndpoint | None
    def heartbeat(worker_id: str)
    def cleanup_stale()
    def get_all_capabilities() -> dict
    def get_workers_for_capability(capability: str) -> list[WorkerEndpoint]
    def save_state()  # Persist to state/controller/registry.jsonl
    def load_state()  # Recover from file on startup

    # Multi-controller gossip hooks (enhancement-roadmap.md: peer-to-peer quorum)
    def export_state() -> dict  # For controller-to-controller sync
    def import_remote_state(controller_id: str, state: dict)  # Merge remote registrations
```

**Future-Proofing Note**:
The extended schema fields (runtime, env_profile, slo, spiffe_id, cost_tokens, etc.) enable future proposals:
- **FaaS workers**: `runtime`, `env_profile`, `constraints` (faas-worker-specification.md)
- **SLO enforcement**: `slo` field + YAML files (enhancement-roadmap.md)
- **Identity-based auth**: `spiffe_id`, `required_capabilities` for CAP/OPA (enterprise-security.md, crank-mesh-access-model-evolution.md)
- **Economic routing**: `cost_tokens_per_invocation`, `slo_bid` (from-job-scheduling-to-capability-markets.md)
- **Multi-controller**: `controller_affinity`, `export_state()`, `import_remote_state()` (enhancement-roadmap.md)

**Implementation Strategy**:
- Session 1: Define full schema (all fields optional except core)
- Workers can omit extended fields (backward compatible)
- Future sessions add routing logic that uses these fields
- No refactoring needed when proposals land

**Tests**:
- Register worker with minimal capability (core fields only)
- Register worker with FaaS metadata (runtime, env_profile, constraints)
- Register worker with SLO constraints (latency_p95_ms, availability)
- Route finds correct worker
- Heartbeat updates timestamp
- Stale workers removed after 120s
- Schema validation rejects invalid capabilities
- Schema validation accepts optional extended fields

**Definition of Done**:
- [ ] `src/crank/controller/capability_registry.py` exists
- [ ] All tests pass (`pytest tests/unit/controller/`)
- [ ] Type hints complete, mypy clean
- [ ] Docstrings on all public methods
- [ ] State persists to `state/controller/registry.jsonl` (ADR-0005)
- [ ] Registry recovers from file on instantiation
- [ ] Test: Controller restart → workers reregister → full recovery

**Deliverable**: Standalone registry with disk persistence and restart recovery.

---

## Session 2: Controller Service Skeleton

**Files to Create**:

```
services/
  crank_controller.py          # Controller service (like crank_hello_world.py)

tests/integration/
  test_controller_basic.py     # Integration test
```

**What It Does**:
- **Plain FastAPI app** (not `WorkerApplication` - controller has different lifecycle)
- Uses `crank.security` module for HTTPS + mTLS (same as workers, but no worker runtime)
- **OpenTelemetry instrumentation** (enhancement-roadmap.md: distributed tracing)
  - W3C Trace Context propagation (`traceparent` header)
  - Span creation for all endpoints (/register, /heartbeat, /route, etc.)
  - Future: Jaeger/Tempo/Honeycomb integration
- Runs on port 9000 (controller port)
- Exposes `/health` endpoint
- Exposes `/register` endpoint (workers register here)
- Uses CapabilityRegistry from Session 1

**Why Not `WorkerApplication`**:
- Controller doesn't provide capabilities (it routes to them)
- No worker heartbeat to platform (controller IS the platform)
- Different certificate bootstrap (controller is CA-adjacent, not CA client)
- Simpler to use FastAPI directly with `crank.security.setup_ssl_context()`

**OpenTelemetry Setup** (minimal scaffolding, full integration deferred):

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor

# Setup (outputs to console for now, Jaeger later)
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(ConsoleSpanExporter())
)

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)  # Auto-instrument all endpoints

@app.post("/register")
async def register(request: Request):
    # Trace context automatically propagated via traceparent header
    with tracer.start_as_current_span("controller.register") as span:
        span.set_attribute("worker_id", worker_id)
        # ... registration logic
```

**Note**: Tracing outputs to console in Phase 3 (proves wiring), Jaeger/Tempo integration is future work.

**Endpoints**:

```python
GET  /health                    # Controller health check

POST /register                  # Workers register capabilities
  Body: {
    "worker_id": "worker-streaming",
    "worker_url": "https://localhost:8500",
    "capabilities": [CapabilitySchema, ...]
  }
  Returns: {
    "status": "registered",
    "worker_id": "worker-streaming"
  }

POST /heartbeat                 # Workers send periodic heartbeat
  Body: {
    "worker_id": "worker-streaming"
  }
  Returns: {
    "status": "acknowledged",
    "timestamp": "2025-11-16T10:30:00Z"
  }
  OR (worker unknown): {
    "error": "worker_not_registered",
    "worker_id": "worker-streaming"
  }

POST /deregister                # Workers deregister on shutdown
  Body: {
    "worker_id": "worker-streaming"
  }
  Returns: {
    "status": "deregistered"
  }
```

**Integration Test**:
- Start controller
- Call `/health` → 200 OK
- POST to `/register` with hello_world worker
- Verify worker appears in registry
- POST to `/heartbeat` with worker_id → acknowledged
- POST to `/deregister` with worker_id
- Verify worker removed from registry
- Stop controller

**Definition of Done**:
- [ ] `services/crank_controller.py` runs successfully
- [ ] Uses FastAPI + `crank.security` for HTTPS + mTLS
- [ ] Endpoints work: `/health`, `/register`, `/heartbeat`, `/deregister`
- [ ] Integration test passes
- [ ] One worker (hello_world) can register, heartbeat, deregister
- [ ] Registry persists all operations to disk (from Session 1)
- [ ] `/heartbeat` returns error when worker not registered (forces re-registration)

**Deliverable**: Working controller service that accepts worker registrations.

---

## Session 3: Routing Implementation (ADR-0023 Complete)

**Files to Modify**:

```
services/crank_controller.py   # Add /route endpoint

tests/integration/
  test_controller_routing.py   # Routing tests
```

**What It Does**:
- Adds `/route` endpoint (capability-based routing)
- Implements routing logic from ADR-0023
- Returns worker URL for given capability
- Handles "no worker available" gracefully

**Middleware Hooks** (enhancement-roadmap.md: rate limiting, back-pressure):

```python
# Add to controller app startup
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # FUTURE: Per-tenant token bucket rate limiting
    # tenant_id = extract_tenant_from_cert(request)
    # if not rate_limiter.check_quota(tenant_id):
    #     return JSONResponse({"error": "rate_limit_exceeded"}, status_code=429,
    #                        headers={"Retry-After": "60"})

    # FUTURE: Back-pressure based on queue depth
    # if registry.get_queue_depth(capability) > QUEUE_THRESHOLD:
    #     return JSONResponse({"error": "service_overloaded"}, status_code=503,
    #                        headers={"Retry-After": "5"})

    response = await call_next(request)
    return response
```

**Note**: Middleware stubs in place, actual rate-limiting/back-pressure logic deferred to future work.

**New Endpoints**:

```python
POST /route
  Body: {
    "verb": "convert",
    "capability": "convert_document_to_pdf"
  }
  Returns: {
    "worker_url": "https://worker-doc-1.local:8501",
    "worker_id": "worker-doc-1"
  }
  OR: {
    "error": "no_worker_available",
    "capability": "convert_document_to_pdf"
  }

GET /capabilities             # List all available capabilities
  Returns: {
    "capabilities": [
      {
        "verb": "classify",
        "capability": "image.classify",
        "workers": ["worker-image-1", "worker-image-2"],
        "version": "1.0.0"
      },
      ...
    ],
    "total_workers": 9,
    "healthy_workers": 8
  }

GET /workers                  # List all registered workers (for debugging)
  Returns: {
    "workers": [
      {
        "worker_id": "worker-streaming",
        "worker_url": "https://localhost:8500",
        "last_heartbeat": "2025-11-16T10:30:00Z",
        "is_healthy": true,
        "capabilities": ["stream:text", "stream:events"]
      },
      ...
    ]
  }
```

**Routing Logic** (from ADR-0023, extended for future proposals):

```python
async def route(
    verb: str,
    capability: str,
    requester_identity: str | None = None,  # Future: CAP/OPA policy
    slo_constraints: dict | None = None,  # Future: SLO-aware routing
    budget_tokens: float | None = None,  # Future: Economic routing
    idempotency_key: str | None = None  # Future: Idempotency manager
):
    # FUTURE HOOK: Idempotency check (enhancement-roadmap.md)
    # if idempotency_key and idempotency_manager.has_result(idempotency_key):
    #     return idempotency_manager.get_cached_result(idempotency_key)

    # FUTURE HOOK: Policy evaluation (enterprise-security.md: CAP/OPA)
    # if requester_identity:
    #     allowed = await policy_engine.evaluate(
    #         requester=requester_identity,
    #         action="invoke",
    #         resource=f"{verb}:{capability}"
    #     )
    #     if not allowed:
    #         raise HTTPException(403, "CAP policy denied")

    # 1. Find workers with this capability
    workers = registry.get_workers_for_capability(f"{verb}:{capability}")

    # 2. Filter healthy workers (heartbeat < 60s ago)
    healthy = [w for w in workers if w.is_healthy()]

    # FUTURE HOOK: SLO filtering (enhancement-roadmap.md: SLO-aware routing)
    # if slo_constraints:
    #     healthy = [w for w in healthy if w.meets_slo(slo_constraints)]

    # FUTURE HOOK: Economic routing (from-job-scheduling-to-capability-markets.md)
    # if budget_tokens:
    #     healthy = [w for w in healthy if w.cost_tokens <= budget_tokens]
    #     healthy.sort(key=lambda w: w.cost_tokens)  # Cheapest first

    # 3. Load balance (round-robin for now, future: least-loaded, affinity)
    if healthy:
        return healthy[0]  # Simple: return first
    else:
        return None
```

**Integration Test**:
- Start controller
- Register worker with capability "image.classify"
- GET `/capabilities` → verify "image.classify" listed
- GET `/workers` → verify worker present and healthy
- POST to `/route` with verb="classify", capability="image.classify"
- Verify correct worker URL returned
- POST with non-existent capability
- Verify error returned

**Definition of Done**:
- [ ] `/route` endpoint works (capability-based routing)
- [ ] `/capabilities` endpoint works (list all available)
- [ ] `/workers` endpoint works (list all registered workers)
- [ ] Returns correct worker for capability
- [ ] Returns error when no worker available
- [ ] OpenTelemetry spans created for all endpoints (visible in console output)
- [ ] Routing accepts optional future parameters (requester_identity, slo_constraints, budget_tokens, idempotency_key) but ignores them (documented as stubs)
- [ ] Registry storage format supports multi-controller replication (export_state/import_remote_state methods exist, not yet called)
- [ ] Integration tests pass
- [ ] **ADR-0023 Status → Accepted** (update ADR file)

**Deliverable**: Full capability-based routing working.

---

## Session 4: Worker Migration

**Files to Modify**:

```
services/crank_hello_world.py     # Update to register with controller
services/crank_streaming.py       # Update
services/crank_document_conversion.py  # Update
... (all 9 workers)

tests/integration/
  test_all_workers_registration.py  # Test all workers
```

**What Changes in Workers**:

```python
# OLD (Phase 0-2): Workers run standalone
class MyWorker(WorkerApplication):
    def __init__(self):
        super().__init__(https_port=8500)
        # No registration

# NEW (Phase 3): Workers register with controller
class MyWorker(WorkerApplication):
    def __init__(self):
        super().__init__(https_port=8500)
        self.controller_url = os.getenv(
            "CONTROLLER_URL",
            "https://localhost:9000"
        )
        self.capabilities = [
            CapabilitySchema(
                name="hello",
                verb="greet",
                version="1.0.0",
                ...
            )
        ]
        self._heartbeat_task = None

    async def on_startup(self):
        """Called by WorkerApplication.run()"""
        await self.register_with_controller()
        # Start heartbeat loop (ADR-0023 requirement)
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def on_shutdown(self):
        """Deregister from controller on graceful shutdown"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        await self.deregister_from_controller()

    async def register_with_controller(self):
        async with httpx.AsyncClient(verify=self.ca_cert) as client:
            await client.post(
                f"{self.controller_url}/register",
                json={
                    "worker_id": self.worker_id,
                    "worker_url": f"https://localhost:{self.https_port}",
                    "capabilities": [c.dict() for c in self.capabilities]
                },
                cert=(self.cert_path, self.key_path)
            )

    async def _heartbeat_loop(self):
        """Send heartbeat every 30s (ADR-0023 spec)"""
        while True:
            await asyncio.sleep(30)
            try:
                async with httpx.AsyncClient(verify=self.ca_cert) as client:
                    response = await client.post(
                        f"{self.controller_url}/heartbeat",
                        json={"worker_id": self.worker_id},
                        cert=(self.cert_path, self.key_path)
                    )
                    # Controller restart detection
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("error") == "worker_not_registered":
                            logger.info("Controller restarted, re-registering...")
                            await self.register_with_controller()
            except Exception as e:
                logger.warning(f"Heartbeat failed: {e}")
                # Network issue - keep trying, controller marks stale after 120s

    async def deregister_from_controller(self):
        """Gracefully deregister on shutdown"""
        try:
            async with httpx.AsyncClient(verify=self.ca_cert) as client:
                await client.post(
                    f"{self.controller_url}/deregister",
                    json={"worker_id": self.worker_id},
                    cert=(self.cert_path, self.key_path)
                )
        except Exception as e:
            logger.warning(f"Deregister failed: {e}")
```

**Migration Order** (one at a time):
1. hello_world (simplest)
2. streaming
3. document_conversion
4. email_classifier
5. semantic_search
6. zettel workers (3 workers)
7. image_classifier

**Integration Test**:
- Start controller
- Start all 9 workers
- Verify all workers registered (`GET /capabilities`)
- Verify routing works for each capability
- **Controller restart test**:
  - Stop controller (kill process)
  - Start new controller instance
  - Wait 30s (one heartbeat cycle)
  - Verify all workers reregistered (`GET /capabilities`)
  - Verify routing still works
- Stop workers one by one, verify registry updates (heartbeat timeout or deregister)

**Definition of Done**:
- [ ] All 9 workers register on startup
- [ ] All workers send heartbeats (every 30s)
- [ ] Workers auto-reregister when heartbeat returns `worker_not_registered`
- [ ] Controller tracks all workers
- [ ] Integration test passes (including controller restart scenario)
- [ ] Test: Restart controller mid-flight → workers reregister within 30s
- [ ] No regression in existing functionality

**Deliverable**: Full controller + workers system operational.

---

## Session 5: Platform Cleanup

**Files to Modify**:

```
services/crank_platform_service.py  # Remove controller logic
docs/architecture/CONTROLLER_WORKER_MODEL.md  # Update docs
docs/planning/phase-3-controller-extraction.md  # Mark complete
```

**What Gets Removed from Platform**:
- Worker registration logic
- Capability registry (now in controller)
- Routing logic (now in controller)
- Mesh coordination (future: move to controller)

**What Stays in Platform**:
- User-facing API endpoints
- Authentication/authorization
- Request validation
- Response formatting
- Future: AI agent orchestration

**Platform Becomes**:

```python
# Platform = thin API layer over controller
@app.post("/execute")
async def execute_capability(request: CapabilityRequest):
    # 1. Validate request (platform responsibility)
    # 2. Call controller for routing
    worker_url = await controller_client.route(
        verb=request.verb,
        capability=request.capability
    )
    # 3. Call worker directly
    result = await worker_client.execute(worker_url, request.payload)
    # 4. Return formatted response
    return result
```

**Documentation Updates**:
- Update architecture diagram (controller separate from platform)
- Document controller endpoints (including future-proof parameters)
- Document extended CapabilitySchema fields and their proposal origins
- Update deployment guide
- **Create SLO scaffolding** (enhancement-roadmap.md):
  - Create `state/controller/slos/` directory for YAML SLO files
  - Document SLO file format (latency_p95_ms, availability, error_budget_pct)
  - Add placeholder SLO file: `state/controller/slos/example-capability.yml`
  - Controller startup logs "SLO ingestion not yet implemented" (future work)
- **Certificate rotation preparation** (enterprise-security.md):
  - Document cert expiry monitoring hook (future: automated renewal)
  - Add placeholder for HSM integration (future work)
- Mark Phase 3 complete

**Definition of Done**:
- [ ] Platform service < 200 lines (thin proxy)
- [ ] Controller logic removed from platform
- [ ] All tests still pass
- [ ] Documentation updated
- [ ] Phase 3 marked complete in planning doc

**Deliverable**: Clean architectural separation, Phase 3 complete ✅

---

## Pre-Flight Checklist

**Before Session 1**:
- [ ] Phases 0-2 complete and tested
- [ ] All 9 workers using `WorkerApplication` pattern
- [ ] Security module consolidated (ADR-0003)
- [ ] Git status clean (commit pending work)
- [ ] Python environment up to date (`uv sync --all-extras`)

**Environment Setup**:

```bash
# Verify foundation
pytest tests/unit/capabilities/  # Phase 0
pytest tests/unit/worker_runtime/  # Phase 0
pytest tests/integration/  # Phases 1-2

# Create controller branch
git checkout -b phase-3-controller-extraction
```

---

## Success Metrics

**Functional**:
- [ ] Controller runs as separate service
- [ ] All 9 workers register successfully
- [ ] Capability-based routing works
- [ ] Heartbeat tracking prevents stale workers
- [ ] Tests pass (unit + integration)

**Performance**:
- [ ] Latency < 10ms for routing decision
- [ ] Registry lookup O(1) for capability
- [ ] Heartbeat overhead < 1% CPU

**Architecture**:
- [ ] Controller privileged, workers restricted
- [ ] Platform is thin API layer
- [ ] ADR-0023 fully implemented
- [ ] Ready for Cloudflare integration

---

## Risk Mitigation

**Rollback Plan**:
- Each session is git-committable
- If Session N fails, revert to Session N-1
- Keep old platform code until Session 5

**Testing Strategy**:
- Unit tests for registry (Session 1)
- Integration tests for each session
- Run full test suite after each session
- Manual smoke test (start controller + workers, call /route)

**What Could Go Wrong**:
1. **Worker registration fails**: Check HTTPS cert paths, controller URL
2. **Routing returns wrong worker**: Debug registry.route() logic
3. **Heartbeat doesn't work**: Verify async loop, check timing
4. **Platform breaks**: Keep old code until Session 5 complete

---

## Post-Phase 3: What's Next

**Immediate (Week After)**:
- Cloudflare Worker integration (can call controller `/route`)
- Observability (ADR-0024): Add metrics to controller
- Load testing: Validate performance under load

**Near-Term (Month After)**:
- Multi-controller mesh (controller-to-controller sync)
- Advanced routing (load balancing, affinity, constraints)
- Worker autoscaling (start workers on demand)

**Long-Term (Quarter After)**:
- ABAC permissions (ADR-0011)
- Default-deny network egress (ADR-0012)
- Plugin system for agents (ADR-0025)

---

## Decision Points

**Before Starting**:

1. **Controller Port**: 9000 or different?
   - **Recommendation**: 9000 (distinct from workers 8500-8599)

2. **Registration Authentication**: mTLS only or add API key?
   - **Recommendation**: mTLS only (already working from ADR-0002/0003)

3. **Heartbeat Interval**: 30s or different?
   - **Recommendation**: 30s (per ADR-0023, proven in worker patterns)

4. **Stale Worker Timeout**: 120s or different?
   - **Recommendation**: 120s (4 missed heartbeats = generous for network issues)

5. **Load Balancing Algorithm**: Round-robin, random, or least-loaded?
   - **Recommendation**: Round-robin (simplest, good enough for MVP)

---

## Communication Plan

**After Each Session**:
- Git commit with clear message: "feat(phase3): complete session N - [description]"
- Update this document's session status
- Run full test suite, verify no regressions

**After Session 3** (ADR-0023 complete):
- Update ADR-0023 status: Proposed → Accepted
- Create short demo video (register worker, call route, show result)

**After Session 5** (Phase 3 complete):
- Update `docs/planning/phase-3-controller-extraction.md`: Status → Complete
- Create GitHub Issue #30: Phase 3 Complete ✅
- Announce in team chat: "Controller extraction complete, ready for Cloudflare"
- Update `.vscode/AGENT_CONTEXT.md`: Phase 3 complete, Phase 4 ready

---

## Appendix: Quick Reference

### File Locations

**Controller Code**:
- `src/crank/controller/capability_registry.py`
- `services/crank_controller.py`

**Tests**:
- `tests/unit/controller/test_capability_registry.py`
- `tests/integration/test_controller_basic.py`
- `tests/integration/test_controller_routing.py`
- `tests/integration/test_all_workers_registration.py`

**Documentation**:
- `docs/architecture/CONTROLLER_WORKER_MODEL.md`
- `docs/decisions/0023-capability-publishing-protocol.md`
- `docs/planning/phase-3-controller-extraction.md`

### Commands

```bash
# Run controller (Session 2+)
python -m services.crank_controller

# Run specific tests
pytest tests/unit/controller/
pytest tests/integration/test_controller_routing.py

# Full test suite
pytest

# Type checking
mypy src/crank/controller/

# Start controller + all workers (Session 4+)
# Terminal 1: Controller
python -m services.crank_controller

# Terminal 2-10: Workers
python -m services.crank_hello_world
python -m services.crank_streaming
# ... etc
```

### Proposal Integration Map

| Proposal | Phase 3 Scaffolding | Future Activation |
|----------|-------------------|-------------------|
| **faas-worker-specification.md** | `runtime`, `env_profile`, `constraints` fields in CapabilitySchema | Workers declare execution requirements, controller routes to compatible workers |
| **faas-environment-profiles.md** | `env_profile` field (e.g., "python-ml", "node-standard") | Controller validates worker has requested profile |
| **enhancement-roadmap.md (SLO)** | `slo` field, `state/controller/slos/` directory | YAML SLO file ingestion, SLO-aware routing, error budget tracking |
| **enhancement-roadmap.md (Idempotency)** | `idempotency_key` parameter in `/route` | Idempotency manager caches results, 1-hour TTL, replay on retry |
| **enhancement-roadmap.md (Rate Limiting)** | Middleware stub with commented token bucket logic | Per-tenant quotas, 429 responses with Retry-After headers |
| **enhancement-roadmap.md (Back-Pressure)** | Middleware stub with queue depth check | 503 responses when queue > threshold, graceful degradation |
| **enhancement-roadmap.md (Tracing)** | OpenTelemetry FastAPI instrumentation, console exporter | Jaeger/Tempo backend integration, exemplar linking |
| **enhancement-roadmap.md (Multi-Controller)** | `export_state()`, `import_remote_state()`, `controller_affinity` | Peer-to-peer gossip, quorum consensus, multi-region deployment |
| **enterprise-security.md (CAP/OPA)** | `requester_identity` parameter, policy evaluation stub | OPA sidecar, Rego policies, 403 denials, audit trail |
| **enterprise-security.md (Cert Rotation)** | Cert expiry monitoring hooks documented | HSM-backed CA, automated renewal, zero-downtime rotation |
| **crank-mesh-access-model-evolution.md** | `spiffe_id`, `required_capabilities` in schema | SPIFFE identity validation, capability tokens (JWT/cert-derived) |
| **from-job-scheduling-to-capability-markets.md** | `cost_tokens_per_invocation`, `slo_bid`, `budget_tokens` | Economic routing, SLO bid matching, market-based worker selection |

**Key Insight**: All 12 proposal integrations are **schema fields, API parameters, or commented hooks**. Core routing works without them. Activating a proposal means uncommenting code and adding logic, not refactoring APIs.

### Environment Variables

```bash
# Controller
CONTROLLER_HTTPS_PORT=9000
CONTROLLER_CERT_PATH=/path/to/certs/controller.crt
CONTROLLER_KEY_PATH=/path/to/certs/controller.key
CA_CERT_PATH=/path/to/certs/ca.crt

# Workers
CONTROLLER_URL=https://localhost:9000
WORKER_HTTPS_PORT=8500  # 8501, 8502, etc.
```

---

**This Document**:
- Created: 2025-11-16
- Owner: Platform Team
- Status: Ready for Codex Review
- Next: Share with Codex, get feedback, begin Session 1
