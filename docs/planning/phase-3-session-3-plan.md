# Phase 3 Session 3: Real Worker Integration

**Date**: November 16, 2025
**Status**: 🚀 Ready to Start
**Prerequisites**: Sessions 1-2 Complete ✅
**Issue**: [#30 - Phase 3: Controller Extraction](https://github.com/crankbird/crank-platform/issues/30)

## Executive Summary

Integrate `crank_hello_world` worker with the controller service, implementing the complete worker lifecycle: startup → register → heartbeat → routing. This validates the end-to-end controller/worker pattern.

## Context

**Session 1 Complete** ✅:
- Capability registry (routing engine)
- 18/18 tests passing
- Extended schema (12 fields)

**Session 2 Complete** ✅:
- Controller FastAPI service (standalone, not WorkerApplication)
- 11/11 integration tests passing
- Codex-reviewed architecture (proper lifecycle separation)

**Session 3 Goal**: Prove the pattern works with a real worker.

## Deliverables

### 1. Update `crank_hello_world` for Controller Discovery

**File**: `services/crank_hello_world.py`

**Changes Needed**:

```python
# Add controller registration on startup
class HelloWorldWorker(WorkerApplication):
    def __init__(self, ...):
        super().__init__(...)
        self.controller_url = os.getenv(
            "CONTROLLER_URL",
            "https://localhost:9000"
        )

    async def on_startup(self):
        """Register with controller on startup."""
        await super().on_startup()
        await self._register_with_controller()

    async def _register_with_controller(self):
        """Send registration request to controller."""
        # POST to controller /register endpoint
        # Send: worker_id, worker_url, capabilities
        # Store: registration confirmation
```

**Pattern**: Use `ControllerClient` from worker runtime (if exists) or implement inline.

### 2. Implement Controller Registration Flow

**Option A - Add to WorkerApplication** (Recommended):
- Extend `WorkerApplication` with optional controller registration
- Environment: `CONTROLLER_URL` (if set, register on startup)
- Background: Heartbeat loop (if registered)

**Option B - Worker-Specific**:
- Each worker handles registration manually
- More flexible but duplicates code

**Decision**: Start with Option B (simpler), refactor to Option A in Phase 4.

### 3. End-to-End Integration Test

**File**: `tests/integration/test_worker_controller_integration.py`

**Test Flow**:

```python
def test_hello_world_registers_with_controller():
    """Test full worker registration lifecycle."""

    # 1. Start controller (TestClient)
    controller = ControllerService(https_port=9999)
    controller_client = TestClient(controller.app)

    # 2. Start hello_world worker (mock or TestClient)
    worker = HelloWorldWorker(https_port=8500)

    # 3. Worker registers on startup
    # (trigger worker.on_startup() or mock registration call)

    # 4. Verify controller received registration
    response = controller_client.get("/workers")
    workers = response.json()["workers"]
    assert len(workers) == 1
    assert workers[0]["worker_id"] == "hello-world-1"

    # 5. Route capability request
    route_request = {
        "verb": "invoke",
        "capability": "hello.greet"
    }
    response = controller_client.post("/route", json=route_request)
    assert response.status_code == 200
    route = response.json()
    assert route["worker_id"] == "hello-world-1"
    assert "hello-world-1" in route["worker_url"]
```

**Validation**:
- ✅ Worker registers successfully
- ✅ Controller sees worker in registry
- ✅ Routing finds worker by capability
- ✅ Health status tracked

### 4. Mock Controller Service (Optional)

**File**: `tests/mocks/mock_controller.py`

**Purpose**: Lightweight controller for worker unit tests (no full controller needed).

```python
class MockController:
    """Minimal controller for worker testing."""

    def __init__(self):
        self.registered_workers = {}
        self.heartbeats = defaultdict(list)

    def register(self, worker_id, worker_url, capabilities):
        """Record registration."""
        self.registered_workers[worker_id] = {
            "worker_url": worker_url,
            "capabilities": capabilities,
        }
        return {"status": "registered"}

    def heartbeat(self, worker_id):
        """Record heartbeat."""
        self.heartbeats[worker_id].append(datetime.now())
        return {"acknowledged": True}
```

**Use Case**: Fast worker tests without spinning up full controller.

## Technical Decisions

### 1. Controller Discovery

**Environment Variable**: `CONTROLLER_URL`
- Development: `https://localhost:9000`
- Production: `https://controller.crank.local:9000`
- Kubernetes: `https://crank-controller:9000`

**Fallback**: If not set, worker runs standalone (no registration).

**Future**: Support DNS-based discovery, service mesh integration.

### 2. Registration Timing

**When**: Worker `on_startup()` hook (after SSL/certificates loaded).

**Retry Logic**:
- Initial registration: retry 3 times with backoff
- On failure: log error, continue running (worker still functional)
- Heartbeat: background task every 30s

**Rationale**: Workers should be resilient to controller outages.

### 3. Heartbeat Strategy

**Pattern**: Background asyncio task (started in `on_startup()`).

```python
async def _heartbeat_loop(self):
    """Send periodic heartbeats to controller."""
    while True:
        await asyncio.sleep(30)  # 30s interval
        try:
            await self._send_heartbeat()
        except Exception as e:
            logger.warning("Heartbeat failed: %s", e)
            # Continue anyway - controller will mark stale
```

**Timeout**: Controller marks workers stale after 120s (4 missed heartbeats).

### 4. SSL/mTLS for Registration

**Challenge**: Worker → Controller communication needs mTLS.

**Options**:
- **A**: Use same certificates worker already has (`client.crt`, `ca.crt`)
- **B**: Separate controller client certificates
- **C**: No mTLS for registration (just HTTPS)

**Decision**: Option A - reuse existing certificates (simpler, already provisioned).

## Implementation Plan

### Step 1: Update Hello World Worker (30 min)

1. Add `CONTROLLER_URL` environment variable
2. Implement `_register_with_controller()` method
3. Call registration in `on_startup()` hook
4. Add heartbeat background task

### Step 2: Create Integration Test (30 min)

1. Create test file with controller + worker fixtures
2. Test registration flow
3. Test routing to registered worker
4. Test heartbeat updates

### Step 3: Test Manually (15 min)

```bash
# Terminal 1: Start controller
export CONTROLLER_HTTPS_PORT=9000
python services/crank_controller.py

# Terminal 2: Start worker
export WORKER_HTTPS_PORT=8500
export CONTROLLER_URL=https://localhost:9000
python services/crank_hello_world.py

# Terminal 3: Verify registration
curl -k https://localhost:9000/workers | jq
curl -k https://localhost:9000/capabilities | jq
```

### Step 4: Documentation (15 min)

1. Update `README.md` with controller+worker startup
2. Add environment variable documentation
3. Update architecture diagrams (if needed)

**Total Estimated Time**: 1.5 hours

## Success Criteria

### Functional
- ✅ Hello World worker registers with controller on startup
- ✅ Controller lists worker in `/workers` endpoint
- ✅ Controller lists `hello.greet` capability in `/capabilities` endpoint
- ✅ Routing request returns correct worker URL
- ✅ Heartbeat updates worker's `last_heartbeat` timestamp

### Quality
- ✅ Integration test passes (end-to-end flow)
- ✅ Type-clean (0 Pylance errors)
- ✅ Proper error handling (registration failures logged, not fatal)
- ✅ SSL/mTLS working (no certificate errors)

### Architecture
- ✅ Worker doesn't know about registry internals
- ✅ Controller doesn't know about worker implementation
- ✅ Clean separation via HTTP API
- ✅ Resilient to controller outages (worker continues running)

## Open Questions

### 1. Heartbeat Interval

**Options**:
- **30s**: Frequent (2 min to detect failure)
- **60s**: Balanced (4 min to detect failure)
- **120s**: Infrequent (8 min to detect failure)

**Recommendation**: 30s (controller timeout 120s = 4 missed heartbeats).

### 2. Registration Retry Logic

**Should workers retry forever or give up?**

**Recommendation**: Retry with exponential backoff for 5 minutes, then log error and continue. Worker should still respond to direct requests even if not registered.

### 3. Deregistration on Shutdown

**Should workers explicitly deregister?**

**Recommendation**: Yes - call `DELETE /deregister/{worker_id}` in `on_shutdown()` hook. Allows graceful removal vs. waiting for heartbeat timeout.

## Risks

### 1. Certificate Path Issues

**Risk**: Worker and controller might not find each other's certificates.

**Mitigation**: Use same certificate directory pattern, test manually first.

### 2. Port Conflicts

**Risk**: Controller (9000) and worker (8500) ports might be in use.

**Mitigation**: Environment variables for all ports, clear documentation.

### 3. Async/Sync Mixing

**Risk**: Registration from sync `main()` or async `on_startup()`?

**Mitigation**: Use async in `on_startup()` hook (already async context).

## Next Steps After Session 3

**Phase 3 Session 4** (Future):
- Migrate remaining workers to controller pattern
- Add SLO-based routing logic
- Implement mesh coordination between controllers
- Add economic routing (capability markets)

**Phase 4 Prep**:
- Refactor controller registration into `WorkerApplication` base
- Create `ControllerClient` abstraction
- Add service discovery (DNS, Consul)

## References

- **Session 1 Report**: `docs/planning/phase-3-session-1-COMPLETE.md`
- **Session 2 Commits**: `4315a60`, `80ae632`, `622253e`
- **Main Attack Plan**: `docs/planning/phase-3-controller-extraction.md`
- **Worker Runtime**: `src/crank/worker_runtime/base.py`
- **Controller Service**: `services/crank_controller.py`

---

**Status**: Ready to implement - all prerequisites met.
**Estimated Completion**: 1.5 hours
**Priority**: High (validates core architecture)
