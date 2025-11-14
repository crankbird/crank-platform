# Phase 3: Controller Extraction from Platform

**Type**: Active Plan
**Status**: 🔜 Ready to Start
**Temporal Context**: Next Phase - Implementation Pending
**Related Issues**: #30
**Dependencies**: Phases 0-2 Complete ✅

---

## Overview

Extract controller functionality from the monolithic platform service, establishing proper separation between node-local controller responsibilities and worker execution. This is the core architectural shift that realizes the controller/worker/capability model.

## Current State

**Foundation Ready** (Phases 0-2 Complete):

- ✅ Capability schema established
- ✅ Worker runtime base class proven
- ✅ 8 workers migrated to shared runtime
- ✅ Base worker image created
- ✅ Hybrid deployment (containers + native) validated

**Platform Files Requiring Refactor**:

- `services/crank_platform_service.py` → becomes `crank_controller_service.py`
- `services/crank_platform_app.py` → becomes `crank_controller_app.py`
- `services/crank_mesh_interface.py` → controller mesh coordination
- `services/dependencies.py` → controller-level DI (currently misplaced)

## Deliverables

### 1. Rename/Refactor Core Files

**Controller Service** (`services/crank_controller_service.py`):

- Capability registry management
- Worker registration/heartbeat endpoints
- Routing logic (capability-based)
- Mesh coordination
- Trust/certificate management (privileged operations)

**Controller Application** (`services/crank_controller_app.py`):

- FastAPI application setup
- Middleware configuration
- Controller-specific routes
- Health/metrics endpoints

**Remove from Controller**:

- Worker-specific business logic
- Direct work execution
- Service-specific endpoints (delegate to workers)

### 2. Implement Controller-Side Capability Registry

**Endpoints**:

```python
POST /controller/register
  # Workers register capabilities on startup
  # Validates against capability schema
  # Returns: worker_id, certificate, controller endpoints

GET /controller/capabilities
  # List all available capabilities in cluster
  # Filter by: capability_id, version, worker_id
  # Returns: [{capability, workers, health_status}]

POST /controller/route
  # Capability-based routing (not worker-specific)
  # Input: {capability_id, version, payload}
  # Logic: Find worker, load balance, route request
  # Returns: worker response OR queue ticket

GET /controller/workers
  # List registered workers
  # Health status, capabilities, load
  # Returns: [{worker_id, capabilities, status}]

POST /controller/mesh/sync
  # Mesh coordination (controller-to-controller)
  # Share capability availability
  # Returns: mesh state
```

**Validation Logic**:

- All worker capability declarations must match schema
- Version compatibility checks (semver)
- Contract enforcement (input/output schemas)

### 3. Update Workers for Controller Discovery

**Environment-Based Discovery** (not hardcoded):

```python
# In worker configuration
CONTROLLER_URL = os.getenv(
    "CONTROLLER_URL",
    "https://localhost:8000"  # Node-local by default
)

# Workers register to local controller
# Controller handles mesh coordination
```

**Registration Flow**:

1. Worker starts → reads `CONTROLLER_URL` from environment
2. Worker POSTs to `/controller/register` with capabilities
3. Controller validates capabilities against schema
4. Controller returns: worker_id, certificate, endpoints
5. Worker begins heartbeat loop to controller
6. Controller adds worker to capability registry

### 4. Update Tests

**Controller Mock** (`tests/mocks/controller_mock.py`):

- Lightweight controller for unit tests
- Validates capability registration
- Simulates routing logic
- No mesh complexity

**Integration Tests** (`tests/integration/test_controller_routing.py`):

- Real controller + multiple workers
- Capability-based routing validation
- Worker lifecycle (register, heartbeat, deregister)
- Fault tolerance (worker failure, recovery)

**Contract Tests** (`tests/contracts/test_capability_compliance.py`):

- Every worker's manifest matches schema
- Schema validation enforced
- Version compatibility verified

## Migration Strategy

### Phase 3A: Parallel Development (Low Risk)

1. **Create new controller files** (don't delete platform yet)
2. **Implement capability registry endpoints**
3. **Create controller mock for tests**
4. **Update ONE worker** to use controller (streaming worker)
5. **Validate** with integration tests

### Phase 3B: Blue-Green Deployment (Medium Risk)

1. **Deploy controller alongside platform** (both running)
2. **Migrate workers one-by-one** to controller
3. **Validate each migration** before proceeding
4. **Monitor metrics** (latency, error rates, throughput)

### Phase 3C: Cutover (High Risk - Final Step)

1. **All workers** connected to controller
2. **All tests passing** with controller
3. **Platform service** becomes thin proxy (deprecation path)
4. **Mesh coordination** fully operational
5. **Delete old platform code** (after burn-in period)

## Acceptance Criteria

- [ ] Controller files renamed and refactored
- [ ] Controller exposes capability registry endpoints
- [ ] Controller validates capabilities against schema
- [ ] Workers discover controller via ENV (not hardcoded)
- [ ] All existing functionality still works
- [ ] Tests use controller mocks for unit tests
- [ ] Integration tests prove multi-worker routing
- [ ] Mesh coordination still operational
- [ ] Documentation updated (`docs/architecture/controller-worker-model.md`)
- [ ] Migration guide for future workers (`docs/planning/worker-migration-guide.md`)

## Risk Mitigation

### Rollback Plan

- Keep old platform code until controller proven
- Feature flags for toggling old/new patterns
- Blue-green deployment allows instant rollback
- Monitoring dashboards track migration health

### Testing Strategy

- Unit tests for controller endpoints
- Integration tests for multi-worker scenarios
- Contract tests for capability compliance
- Load tests to validate performance
- Chaos tests for fault tolerance

### Success Metrics

**Functional**:

- All 8 workers register successfully
- Capability-based routing works
- Mesh coordination operational
- Zero downtime during migration

**Performance**:

- Latency unchanged or improved
- Error rates < 0.1%
- Throughput maintained or increased

**Architecture**:

- Controller-per-node pattern working
- Workers are node-local by default
- Mesh shares capability state correctly
- Privilege separation enforced (controller privileged, workers restricted)

## Open Questions

### 1. Controller URL Discovery

**Options**:

- **A**: Environment variable `CONTROLLER_URL` (simple, flexible)
- **B**: Config file `/etc/crank/controller.conf` (traditional)
- **C**: Service discovery (DNS, Consul, etc.) (complex, production-grade)
- **D**: Hardcoded localhost (development only)

**Recommendation**: Start with (A), support (C) for production deployments

### 2. Backward Compatibility

**How long maintain old platform patterns?**

- **Immediate cutover**: Delete old code once controller working
- **Deprecation period**: 1 release cycle with both patterns
- **Long-term support**: 6 months dual patterns

**Recommendation**: 1 release cycle deprecation (allows phased adoption)

### 3. Mesh Coordination

**Who initiates mesh sync?**

- **Pull**: Controllers poll each other
- **Push**: Controllers notify on state change
- **Hybrid**: Push with periodic sync

**Recommendation**: Hybrid (push for speed, periodic sync for reliability)

### 4. Certificate Authority Placement

**Where does CA live?**

- **A**: Controller includes CA (simple, single point of trust)
- **B**: Separate CA service (proper separation, more complex)
- **C**: External CA (HashiCorp Vault, etc.) (enterprise-grade)

**Recommendation**: (A) for MVP, design for (C) migration

## Timeline

**Estimated**: 3-5 days (assuming phases 0-2 complete)

**Breakdown**:

- Day 1: Controller refactoring + endpoint implementation
- Day 2: Worker discovery updates + mock creation
- Day 3: Integration tests + first worker migration
- Day 4: Remaining worker migrations + validation
- Day 5: Documentation + cleanup + burn-in

**Blockers**:

- Must complete Phases 0-2 first ✅
- Requires dedicated testing time (no concurrent feature work)
- May need production deployment window

## Next Steps

**When Ready to Begin**:

1. Create GitHub Issue #30
2. Review open questions and make decisions
3. Set up monitoring dashboards
4. Create feature flags for rollback
5. Begin Phase 3A (parallel development)

---

**Last Updated**: November 14, 2025
**Ready to Start**: Yes (foundation complete)
**Priority**: High (core architectural goal)
