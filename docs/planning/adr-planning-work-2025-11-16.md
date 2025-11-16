# ADR and Planning Work - November 16, 2025

## Summary

Created comprehensive architectural decision records and implementation plans to capture high-value proposals identified for Phase 3 controller work.

## New ADRs Created

### ADR-0026: Controller-Level SLO Enforcement and Idempotency Manager
**Status**: Proposed
**Path**: `docs/decisions/0026-controller-slo-and-idempotency.md`

**Purpose**: Define how the controller enforces Service Level Objectives and prevents duplicate execution on retries.

**Key Decisions**:
- YAML-based SLO definitions (version controlled in Git)
- In-memory idempotency cache (1-hour TTL, LRU eviction)
- CI integration (fail builds on SLO regression)
- Prometheus metrics for SLO tracking
- Three-phase rollout: log-only → enforcement with exceptions → full enforcement

**Proposal Origins**:
- [enhancement-roadmap.md lines 78-95](../proposals/enhancement-roadmap.md) - SLO files, idempotency manager
- Enterprise readiness requirements

---

### ADR-0027: Controller Policy Enforcement (CAP/OPA Integration)
**Status**: Proposed
**Path**: `docs/decisions/0027-controller-policy-enforcement.md`

**Purpose**: Define capability-based access control using OPA and SPIFFE identity.

**Key Decisions**:
- OPA (Open Policy Agent) with Rego policies
- SPIFFE ID extraction from mTLS certificates
- Worker manifests declare needed capabilities
- Policy-as-code (version controlled Rego files)
- Audit trail for all policy decisions
- Shadow mode → exceptions → full enforcement migration

**Proposal Origins**:
- [enterprise-security.md lines 41-115](../proposals/enterprise-security.md) - CAP/OPA enforcement
- [crank-mesh-access-model-evolution.md lines 147-155](../proposals/crank-mesh-access-model-evolution.md) - SPIFFE + capability tokens
- Zero-trust security requirements

---

## ADRs Updated

### ADR-0006: Verb/Capability Registry
**Change**: Added "Extended by Phase 3" note documenting future-proof schema fields

**Extended Fields**:
- FaaS metadata: `runtime`, `env_profile`, `constraints`
- SLO constraints: `slo` field
- Identity fields: `spiffe_id`, `required_capabilities`
- Economic routing: `cost_tokens_per_invocation`, `slo_bid`
- Multi-controller: `controller_affinity`

**Links Added**: Phase 3 Session 1, FaaS proposals, enhancement roadmap

---

### ADR-0024: Observability Strategy
**Change**: Extended with "Phase 3 Controller Tracing" section

**Added Content**:
- W3C Trace Context propagation implementation
- FastAPI auto-instrumentation code examples
- Trace propagation to workers (traceparent header)
- Metrics exemplars (linking traces to metrics)
- Future Jaeger/Tempo integration plan

**Links Added**: Enhancement roadmap observability requirements, Phase 3 Session 2

---

### docs/decisions/README.md
**Change**: Added two new ADRs to index

**Updated Table**:

```markdown
| [0026](0026-controller-slo-and-idempotency.md) | Controller-Level SLO Enforcement and Idempotency Manager | Proposed | 2025-11-16 |
| [0027](0027-controller-policy-enforcement.md) | Controller Policy Enforcement (CAP/OPA Integration) | Proposed | 2025-11-16 |
```

---

## Planning Documents Created

All three implementation plans are now complete, providing tactical execution paths for the high-value proposals integrated into Phase 3.

### 1. controller-slo-idempotency-plan.md
**Status**: ✅ Complete - Ready to Execute (Post-Phase 3)
**Path**: `docs/planning/controller-slo-idempotency-plan.md`

**Timeline**: 2-3 days (4 sessions)
**Blocks**: ADR-0026 acceptance
**Depends On**: Phase 3 Session 3 complete

**Sessions**:
1. **SLO Manager + YAML Schema** (4 hours) - Load/validate SLO files, compliance checker
2. **Idempotency Manager** (3 hours) - In-memory cache with TTL and LRU eviction
3. **Controller Integration** (4 hours) - Add SLO + idempotency to `/route` endpoint
4. **CI Integration** (2 hours) - SLO compliance check in GitHub Actions

**Deliverables**:
- SLOManager class (loads YAML, checks compliance)
- IdempotencyManager class (cache with TTL, LRU)
- Enhanced `/route` endpoint (SLO-aware routing, idempotency checking)
- CI script (`scripts/check_slo_compliance.py`)
- GitHub Actions workflow
- Prometheus metrics
- Integration tests

**Proposal Origins**: [enhancement-roadmap.md lines 78-95](../proposals/enhancement-roadmap.md)

---

### 2. controller-policy-observability-plan.md
**Status**: ✅ Complete - Ready to Execute (Post-Phase 3)
**Path**: `docs/planning/controller-policy-observability-plan.md`

**Timeline**: 3-4 days (4 sessions)
**Blocks**: ADR-0027 acceptance, ADR-0024 full implementation
**Depends On**: Phase 3 Session 2 complete

**Sessions**:
- Session 1: OPA deployment + SPIFFE extraction (4 hours)
- Session 2: Controller policy integration (3 hours)
- Session 3: Jaeger/Tempo backend integration (4 hours)
- Session 4: Audit logging + migration strategy (3 hours)

**Deliverables**:
- OPA sidecar with Rego policies
- SPIFFE ID extraction from mTLS certs
- Worker manifests (capability declarations)
- Policy-as-code (version controlled)
- Distributed tracing (W3C Trace Context)
- Jaeger UI for trace visualization
- Audit trail for all decisions
- Migration playbook (shadow → enforcement)

**Proposal Origins**:
- [enterprise-security.md lines 41-115](../proposals/enterprise-security.md) - CAP/OPA
- [enhancement-roadmap.md lines 126-148](../proposals/enhancement-roadmap.md) - OpenTelemetry tracing
- [crank-mesh-access-model-evolution.md lines 147-155](../proposals/crank-mesh-access-model-evolution.md) - SPIFFE

---

### 3. capability-metadata-upgrade-plan.md
**Status**: ✅ Complete - Ready to Execute (Post-Phase 3)
**Path**: `docs/planning/capability-metadata-upgrade-plan.md`

**Timeline**: 1-2 days (4 sessions)
**Blocks**: None (incremental rollout safe)
**Depends On**: Phase 3 Session 1 complete

**Sessions**:
- Session 1: Hello world reference implementation - ALL fields (3 hours)
- Session 2: High-traffic workers (streaming, doc_conversion) - FaaS + SLO (3 hours)
- Session 3: ML workers (email_classifier, semantic_search) - FaaS + SLO + CAP (4 hours)
- Session 4: Zettel + image workers - FaaS baseline (3 hours)

**Deliverables**:
- All 10 workers upgraded with FaaS metadata
- 5 workers with SLO constraints
- 3 workers with identity metadata (CAP)
- 2 workers with economic routing metadata
- 2 workers with multi-controller affinity
- Validation script
- Integration tests
- Reference documentation

**Proposal Origins**:
- [faas-worker-metadata.md](../proposals/faas-worker-metadata.md) - FaaS runtime/env/constraints
- [enhancement-roadmap.md](../proposals/enhancement-roadmap.md) - SLO + economic routing

---

## Phase 3 Attack Plan Updates

**File**: `docs/planning/PHASE_3_ATTACK_PLAN.md`

**Changes Made** (earlier in conversation):
1. **Session 1**: Extended CapabilitySchema with 12 optional fields supporting 6 proposals
2. **Session 2**: Added OpenTelemetry instrumentation (W3C Trace Context)
3. **Session 3**: Added policy evaluation stubs, SLO routing parameters, idempotency hooks
4. **Session 5**: Added SLO directory structure, certificate rotation hooks
5. **Future-Proofing Strategy**: Section explaining all scaffolding and proposal integration
6. **Proposal Integration Map**: Table showing 12 proposals mapped to Phase 3 scaffolding

**Result**: Phase 3 now includes hooks for all high-value proposals without adding complexity to core routing logic.

---

## Next Steps

All planning documents are complete. Ready for GitHub issue creation and execution after Phase 3 completes.

### GitHub Issues to Create (After Phase 3 Complete)

**Issue #31: Implement Controller SLO + Idempotency**
- **Plan**: [controller-slo-idempotency-plan.md](controller-slo-idempotency-plan.md)
- **ADR**: [ADR-0026](../decisions/0026-controller-slo-and-idempotency.md)
- **Timeline**: 2-3 days (4 sessions)
- **Dependencies**: Phase 3 Session 3 complete
- **Milestones**: Enterprise readiness
- **Labels**: enhancement, controller, slo, reliability

**Issue #32: Add Policy Enforcement + Distributed Tracing to Controller**
- **Plan**: [controller-policy-observability-plan.md](controller-policy-observability-plan.md)
- **ADR**: [ADR-0027](../decisions/0027-controller-policy-enforcement.md) + [ADR-0024 (Extended)](../decisions/0024-observability-strategy.md)
- **Timeline**: 3-4 days (4 sessions)
- **Dependencies**: Phase 3 Session 2 complete
- **Milestones**: Enterprise security, observability
- **Labels**: enhancement, controller, security, policy, observability

**Issue #33: Upgrade Workers with Extended Capability Metadata**
- **Plan**: [capability-metadata-upgrade-plan.md](capability-metadata-upgrade-plan.md)
- **ADR**: [ADR-0006 (Extended)](../decisions/0006-verb-capability-registry.md)
- **Timeline**: 1-2 days (4 sessions)
- **Dependencies**: Phase 3 Session 1 complete
- **Milestones**: FaaS readiness
- **Labels**: enhancement, workers, metadata, faas

---

## Proposal → ADR → Plan → Issue Flow

### Example: SLO Enforcement

1. **Proposal**: [enhancement-roadmap.md lines 78-95](../proposals/enhancement-roadmap.md)
   - Identifies need for SLO files and idempotency
   - Strategic-level thinking

2. **ADR**: [ADR-0026](../decisions/0026-controller-slo-and-idempotency.md)
   - Architectural decision: YAML SLOs + in-memory cache
   - Rationale, alternatives, consequences

3. **Plan**: [controller-slo-idempotency-plan.md](controller-slo-idempotency-plan.md)
   - Tactical implementation: 4 sessions, specific files, tests
   - Timeline, dependencies, deliverables

4. **Issue**: (to be created after Phase 3 Session 3)
   - Assignable work item
   - Links to plan
   - Acceptance criteria

---

## Updated: Alignment with Proposals

All proposals now have complete ADR + Plan coverage:

| Proposal | ADR | Plan | Status |
|----------|-----|------|--------|
| **enhancement-roadmap.md (SLO)** | ADR-0026 | controller-slo-idempotency-plan.md | ✅ Complete |
| **enhancement-roadmap.md (Tracing)** | ADR-0024 (Extended) | controller-policy-observability-plan.md | ✅ Complete |
| **enterprise-security.md (CAP/OPA)** | ADR-0027 | controller-policy-observability-plan.md | ✅ Complete |
| **faas-worker-specification.md** | ADR-0006 (Extended) | capability-metadata-upgrade-plan.md | ✅ Complete |
| **faas-environment-profiles.md** | ADR-0006 (Extended) | capability-metadata-upgrade-plan.md | ✅ Complete |
| **crank-mesh-access-model-evolution.md** | ADR-0027 | controller-policy-observability-plan.md | ✅ Complete |
| **from-job-scheduling-to-capability-markets.md** | ADR-0006 (Extended) | ❓ Deferred | Post-Phase 3 |

---

## Updated: Documentation Structure

```
docs/
  decisions/              # Architectural decisions
    0026-controller-slo-and-idempotency.md  # NEW
    0027-controller-policy-enforcement.md   # NEW
    0006-verb-capability-registry.md        # UPDATED
    0024-observability-strategy.md          # UPDATED
    README.md                               # UPDATED (index)

  planning/               # Implementation plans
    PHASE_3_ATTACK_PLAN.md                      # UPDATED (future-proofing)
    controller-slo-idempotency-plan.md          # NEW
    controller-policy-observability-plan.md     # NEW
    capability-metadata-upgrade-plan.md         # NEW
    adr-planning-work-2025-11-16.md             # NEW (this summary)

  proposals/              # Strategic ideas
    enhancement-roadmap.md
    enterprise-security.md
    faas-worker-specification.md
    faas-environment-profiles.md
    crank-mesh-access-model-evolution.md
    from-job-scheduling-to-capability-markets.md
```

---

## Execution Readiness

All planning work is now complete. Ready to proceed with Phase 3 execution and subsequent enhancement implementations.

### Phase 3 Execution
1. **Execute Phase 3 Sessions 1-5** (controller extraction)
2. **Verify all scaffolding hooks work** (optional fields, API parameters, stubs)
3. **Test recovery mechanism** (controller restart → workers reregister)
4. **Validate OpenTelemetry console output** (basic tracing operational)

### Post-Phase 3 Implementation
1. **Create GitHub issues** for three enhancement tracks:
   - Issue #31: Controller SLO + Idempotency
   - Issue #32: Controller Policy + Observability
   - Issue #33: Capability Metadata Upgrade

2. **Execute implementation plans** in order:
   - capability-metadata-upgrade-plan.md (1-2 days) - extends worker metadata
   - controller-slo-idempotency-plan.md (2-3 days) - SLO enforcement + idempotency
   - controller-policy-observability-plan.md (3-4 days) - CAP/OPA + distributed tracing

3. **Update ADR statuses** to "Accepted" as implementations complete

4. **Update proposal index** showing complete flow:
   - Proposal → ADR → Plan → Issue → Implementation → Status

---

## Final Impact Summary

**Before This Work**:
- 6 high-value proposals with unclear implementation path
- Phase 3 plan had tactical issues (persistence, endpoints, recovery)
- No architectural decisions documented for enterprise features

**After This Work**:
- ✅ 2 new ADRs documenting architectural decisions (ADR-0026, ADR-0027)
- ✅ 2 ADRs extended with Phase 3 integration details (ADR-0006, ADR-0024)
- ✅ 3 comprehensive implementation plans (7-9 days total implementation time)
- ✅ Phase 3 plan updated with future-proof scaffolding (12 proposals mapped)
- ✅ Phase 3 plan issues fixed (persistence, endpoints, recovery mechanism)
- ✅ Clear path: Proposal → ADR → Plan → Issue → Implementation

**Result**: All high-value proposals now have architectural backing and tactical execution plans, ready to implement after Phase 3 foundation is complete. Controller extraction work is future-proof for enterprise requirements without adding complexity to core routing logic.
