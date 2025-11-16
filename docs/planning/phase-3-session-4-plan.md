# Phase 3 Session 4: Migrate Remaining Workers

**Goal**: Migrate all 8 remaining workers to controller registration pattern
**Time Estimate**: 1.5-2 hours
**Status**: 🔜 Ready to Start
**Prerequisites**: Sessions 1-3 Complete ✅
**Reference Implementation**: `services/crank_hello_world.py` (Session 3)

---

## Overview

With the controller operational and the registration pattern proven in `crank_hello_world`, Session 4 scales the pattern to all remaining workers:

1. **Add heartbeat background tasks** (30s interval, ADR-0023 requirement)
2. **Add deregistration on shutdown** (graceful cleanup)
3. **Test multi-worker routing** (2+ workers with same capability)
4. **Validate HTTPS-only enforcement** across all workers

**Key Insight**: This is primarily repetitive work following the proven pattern. Focus on consistency and validation.

---

## Workers to Migrate (8 Remaining)

| Worker | Port | Capabilities | Complexity |
|--------|------|--------------|------------|
| `crank_streaming.py` | 8501 | `stream:text_events`, `stream:sse_events` | Medium (multiple capabilities) |
| `crank_email_classifier.py` | 8502 | `classify:email_intent` | Low (single capability) |
| `crank_email_parser.py` | 8503 | `parse:email_headers` | Low (single capability) |
| `crank_document_conversion.py` | 8504 | `convert:document_to_pdf` | Low (single capability) |
| `crank_image_classifier.py` | 8505 | `classify:image_category` | Low (single capability) |
| `crank_image_classifier_gpu.py` | 8506 | `classify:image_category` | Medium (GPU, duplicate capability) |
| `crank_philosophical_analyzer.py` | 8507 | `analyze:philosophy` | Low (single capability) |
| `crank_sonnet_zettel_manager.py` | 8508 | `manage:zettel` | Low (single capability) |

**Total**: 8 workers, 10 unique capabilities (streaming has 2, GPU classifier duplicates CPU)

---

## Pattern to Apply (From Session 3)

### 1. Add Controller URL Configuration

```python
class MyWorker(WorkerApplication):
    def __init__(self, https_port: int = 8500):
        super().__init__(
            https_port=https_port,
            worker_id=f"crank-{service_name}",
        )
        
        # Controller discovery
        self.controller_url = os.getenv("CONTROLLER_URL")
        self._registration_confirmed = False
        self._heartbeat_task: Optional[asyncio.Task] = None
```

### 2. Declare Capabilities

```python
    def get_capabilities(self) -> list[CapabilitySchema]:
        """Declare worker capabilities for registration."""
        return [
            CapabilitySchema(
                name="capability_name",
                verb="verb",
                version="1.0.0",
                input_schema={"type": "object", ...},
                output_schema={"type": "object", ...},
                requires_gpu=False,  # True for GPU workers
                max_concurrency=10,
            )
        ]
```

### 3. Implement Lifecycle Hooks

```python
    async def on_startup(self) -> None:
        """Register with controller on startup (if configured)."""
        await super().on_startup()
        if self.controller_url:
            await self._register_with_controller()
            # Start heartbeat loop (30s interval)
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def on_shutdown(self) -> None:
        """Deregister from controller on shutdown."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self.controller_url and self._registration_confirmed:
            await self._deregister_from_controller()
        
        await super().on_shutdown()
```

### 4. Registration Logic (HTTPS with mTLS)

```python
    async def _register_with_controller(self) -> None:
        """Send registration request to controller."""
        capabilities = [cap.model_dump() for cap in self.get_capabilities()]
        payload = {
            "worker_id": self.worker_id,
            "worker_url": f"https://localhost:{self.https_port}",
            "capabilities": capabilities,
        }
        
        ssl_config = self.cert_manager.get_ssl_context()
        
        try:
            async with httpx.AsyncClient(
                cert=(ssl_config["ssl_certfile"], ssl_config["ssl_keyfile"]),
                verify=ssl_config["ssl_ca_certs"],
                timeout=5.0,
            ) as client:
                response = await client.post(
                    f"{self.controller_url}/register",
                    json=payload,
                )
                response.raise_for_status()
                self._registration_confirmed = True
                logger.info(
                    "Registered with controller: %s (capabilities: %d)",
                    self.controller_url,
                    len(capabilities),
                )
        except Exception as e:
            logger.warning(
                "Controller registration failed (continuing in standalone mode): %s",
                str(e),
            )
```

### 5. Heartbeat Loop (30s interval)

```python
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats to controller."""
        while True:
            await asyncio.sleep(30)  # 30 second interval
            
            if not self._registration_confirmed:
                continue
            
            try:
                ssl_config = self.cert_manager.get_ssl_context()
                async with httpx.AsyncClient(
                    cert=(ssl_config["ssl_certfile"], ssl_config["ssl_keyfile"]),
                    verify=ssl_config["ssl_ca_certs"],
                    timeout=5.0,
                ) as client:
                    response = await client.post(
                        f"{self.controller_url}/heartbeat",
                        data={"worker_id": self.worker_id},
                    )
                    
                    if response.status_code == 404:
                        # Controller doesn't know us - re-register
                        logger.warning("Controller lost our registration - re-registering")
                        await self._register_with_controller()
                    else:
                        response.raise_for_status()
                        
            except Exception as e:
                logger.warning("Heartbeat failed: %s", str(e))
```

### 6. Deregistration on Shutdown

```python
    async def _deregister_from_controller(self) -> None:
        """Deregister from controller on shutdown."""
        try:
            ssl_config = self.cert_manager.get_ssl_context()
            async with httpx.AsyncClient(
                cert=(ssl_config["ssl_certfile"], ssl_config["ssl_keyfile"]),
                verify=ssl_config["ssl_ca_certs"],
                timeout=5.0,
            ) as client:
                await client.post(
                    f"{self.controller_url}/deregister",
                    data={"worker_id": self.worker_id},
                )
                logger.info("Deregistered from controller: %s", self.controller_url)
        except Exception as e:
            logger.warning("Deregistration failed: %s", str(e))
```

---

## Migration Checklist (Per Worker)

For each worker:

- [ ] Add `self.controller_url` configuration (from ENV)
- [ ] Implement `get_capabilities()` method
- [ ] Add `on_startup()` hook with registration + heartbeat task
- [ ] Add `on_shutdown()` hook with deregistration
- [ ] Implement `_register_with_controller()` (HTTPS + mTLS)
- [ ] Implement `_heartbeat_loop()` (30s interval)
- [ ] Implement `_deregister_from_controller()`
- [ ] Test: Worker runs standalone (no `CONTROLLER_URL` set)
- [ ] Test: Worker registers when controller running
- [ ] Test: Worker sends heartbeats
- [ ] Test: Worker deregisters on Ctrl+C shutdown

---

## Integration Tests

### Test 1: All Workers Register Successfully

```python
@pytest.mark.asyncio
async def test_all_workers_register(controller_client):
    """Test all 9 workers can register with controller."""
    
    # Simulate registration from all workers
    workers = [
        ("crank-hello-world", 8500, ["greet:hello_world"]),
        ("crank-streaming", 8501, ["stream:text_events", "stream:sse_events"]),
        ("crank-email-classifier", 8502, ["classify:email_intent"]),
        # ... all 9 workers
    ]
    
    for worker_id, port, capabilities in workers:
        response = controller_client.post(
            "/register",
            json={
                "worker_id": worker_id,
                "worker_url": f"https://localhost:{port}",
                "capabilities": [
                    {"name": cap.split(":")[1], "verb": cap.split(":")[0], "version": "1.0.0"}
                    for cap in capabilities
                ],
            },
        )
        assert response.status_code == 200
    
    # Verify all capabilities available
    response = controller_client.get("/capabilities")
    assert response.status_code == 200
    capabilities = response.json()
    
    assert "greet:hello_world" in capabilities
    assert "stream:text_events" in capabilities
    assert "classify:email_intent" in capabilities
```

### Test 2: Multi-Worker Routing (Duplicate Capability)

```python
@pytest.mark.asyncio
async def test_routing_with_multiple_workers_same_capability():
    """Test routing when multiple workers provide same capability."""
    
    # Register CPU and GPU image classifiers (both provide classify:image_category)
    # ... registration code ...
    
    # Route request
    response = controller_client.post(
        "/route",
        json={"verb": "classify", "capability": "image_category"},
    )
    
    assert response.status_code == 200
    worker = response.json()
    assert worker["worker_id"] in ["crank-image-classifier", "crank-image-classifier-gpu"]
```

### Test 3: Heartbeat Auto-Recovery

```python
@pytest.mark.asyncio
async def test_heartbeat_auto_reregistration():
    """Test worker re-registers when controller loses state."""
    
    # Register worker
    # ... registration code ...
    
    # Manually clear controller registry
    registry.deregister("crank-hello-world")
    
    # Send heartbeat - should get 404
    response = controller_client.post(
        "/heartbeat",
        data={"worker_id": "crank-hello-world"},
    )
    assert response.status_code == 404
    
    # Worker should detect 404 and re-register
    # (This requires running real worker, not just TestClient)
```

---

## Validation Criteria

### Functional Requirements

- [ ] All 9 workers can register with controller
- [ ] All 10 capabilities available via `/capabilities` endpoint
- [ ] Routing works for all capabilities
- [ ] Duplicate capabilities (image classification) route correctly
- [ ] Workers continue to work in standalone mode (no `CONTROLLER_URL`)
- [ ] Heartbeat loops run without errors
- [ ] Graceful shutdown deregisters workers

### Security Requirements

- [ ] All worker→controller communication uses HTTPS
- [ ] All requests use mTLS (mutual TLS with certificates)
- [ ] No `http://` URLs anywhere
- [ ] No `verify=False` (disabled verification)
- [ ] Certificate validation enforced

### Performance Requirements

- [ ] Heartbeat interval = 30s (not too aggressive)
- [ ] Registration timeout = 5s (fail fast)
- [ ] Background tasks don't block worker requests
- [ ] Graceful shutdown completes within 10s

---

## Definition of Done

- [ ] All 8 workers migrated to controller pattern
- [ ] Integration tests pass (all workers register, route, heartbeat)
- [ ] HTTPS-only enforcement validated
- [ ] Workers run standalone when `CONTROLLER_URL` not set
- [ ] Workers handle controller unavailability gracefully
- [ ] Heartbeat auto-recovery tested
- [ ] Multi-worker routing tested (duplicate capabilities)
- [ ] Documentation updated (worker migration complete)
- [ ] Commit message references Session 4 completion

---

## Next Steps (Session 5)

After Session 4 complete:

1. **Platform cleanup**: Remove controller logic from `crank_platform_service.py`
2. **Documentation**: Update architecture docs with controller pattern
3. **E2E tests**: Run real controller + all workers with uvicorn
4. **Certificate provisioning**: Validate TLS handshake in production-like setup
5. **Migration guide**: Document pattern for future workers

---

**Status**: Ready to start (Sessions 1-3 complete, pattern proven)
**Estimated Time**: 1.5-2 hours (mostly repetitive work)
**Risk**: Low (pattern proven, workers already on WorkerApplication)
