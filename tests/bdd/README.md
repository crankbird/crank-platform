# BDD Test Suite — Gherkin Features

**Status**: Active  
**Type**: Behavior-Driven Development (BDD)  
**Last Updated**: 2025-11-10  
**Framework**: pytest-bdd  
**Purpose**: Living documentation and acceptance tests for controller/worker refactor

---

## Overview

This directory contains **Gherkin feature files** that define the acceptance criteria for the Crank Platform controller/worker architecture refactor (Issues #27-#31, Phases 0-4).

## Structure

```
tests/bdd/
├── README.md                          # This file
├── HEY-SONNET-READ-THIS.md           # ChatGPT's instructions for Sonnet
├── features/                          # Gherkin feature files
│   ├── gherkin-index.md              # Feature catalog
│   ├── security_trust_mtls.feature
│   ├── capability_routing.feature
│   ├── worker_sandboxing.feature
│   ├── controller_privilege_boundary.feature
│   ├── mesh_state_coordination.feature
│   ├── capability_schema_validation.feature
│   ├── developer_experience_quickstart.feature
│   └── deployment_models.feature
├── step_defs/                         # Step implementations (to be created)
│   ├── __init__.py
│   ├── security_steps.py
│   ├── capability_steps.py
│   ├── worker_steps.py
│   └── mesh_steps.py
└── conftest.py                        # pytest-bdd fixtures (to be created)
```

## Feature Files

### Security & Trust
**[security_trust_mtls.feature](features/security_trust_mtls.feature)**
- Tags: `@principle(Integrity)` `@phase(4)` `@issue(31)` `@component(security)`
- Owner: Wendy 🐰
- Scenarios: mTLS handshake, certificate rotation, trust verification

**[worker_sandboxing.feature](features/worker_sandboxing.feature)**
- Tags: `@principle(Integrity)` `@phase(2)` `@issue(29)` `@component(worker)`
- Owner: Wendy 🐰
- Scenarios: Filesystem restrictions, network egress control, resource limits

**[controller_privilege_boundary.feature](features/controller_privilege_boundary.feature)**
- Tags: `@principle(Legitimacy)` `@phase(1)` `@issue(28)` `@component(controller)`
- Owner: Wendy 🐰
- Scenarios: Privileged operations boundary, worker separation

### Capability Management
**[capability_schema_validation.feature](features/capability_schema_validation.feature)**
- Tags: `@principle(Integrity)` `@phase(0)` `@issue(27)` `@component(capability-schema)`
- Owner: Gary 🦆 (consistency)
- Scenarios: Schema validation, manifest signatures, version control

**[capability_routing.feature](features/capability_routing.feature)**
- Tags: `@principle(Efficiency)` `@phase(1)` `@issue(28)` `@component(controller)`
- Owner: Gary 🦆
- Scenarios: Capability discovery, request routing, load balancing

### Mesh & Coordination
**[mesh_state_coordination.feature](features/mesh_state_coordination.feature)**
- Tags: `@principle(Resilience)` `@phase(3)` `@issue(30)` `@component(mesh)`
- Owner: Gary 🦆
- Scenarios: State synchronization, controller failover, split-brain prevention

### Developer Experience
**[developer_experience_quickstart.feature](features/developer_experience_quickstart.feature)**
- Tags: `@principle(Empathy)` `@phase(0)` `@component(devx)`
- Owner: Kevin 🦙 (portability)
- Scenarios: Quick start, local development, deployment models

**[deployment_models.feature](features/deployment_models.feature)**
- Tags: `@principle(Resilience)` `@phase(4)` `@component(deployment)`
- Owner: Kevin 🦙
- Scenarios: Single-node, HA, multi-region deployment acceptance

## Traceability Tags

Each scenario includes metadata tags for traceability:

### Brand Science Principles
- `@principle(Integrity)` — Security, correctness, auditability
- `@principle(Empathy)` — Developer experience, usability
- `@principle(Efficiency)` — Performance, resource utilization
- `@principle(Legitimacy)` — Authorization, compliance, governance
- `@principle(Resilience)` — Fault tolerance, availability, recovery
- `@principle(Culture)` — Team practices, collaboration

### Architecture Phases
- `@phase(0)` — Foundation (capability schema, worker runtime)
- `@phase(1)` — Controller (privileged boundary, routing)
- `@phase(2)` — Mesh integration (worker sandboxing, state coordination)
- `@phase(3)` — High availability (multi-controller)
- `@phase(4)` — Production hardening (mTLS, deployment models)

### GitHub Issues
- `@issue(27)` — Capability schema foundation
- `@issue(28)` — Controller implementation
- `@issue(29)` — Worker sandboxing
- `@issue(30)` — Mesh state coordination
- `@issue(31)` — Security hardening

### Components
- `@component(controller)` — Controller service
- `@component(worker)` — Worker runtime
- `@component(mesh)` — Service mesh integration
- `@component(capability-schema)` — Capability definitions
- `@component(security)` — mTLS, PKI, sandboxing
- `@component(devx)` — Developer experience

## Scenario ID Convention

Each scenario has a unique ID: `CRNK-<FeatureCode>-###`

Examples:
- `CRNK-SEC-001` — Security feature, scenario 1
- `CRNK-SCHEMA-002` — Schema validation feature, scenario 2
- `CRNK-SBX-001` — Sandboxing feature, scenario 1

## Running BDD Tests

### Setup pytest-bdd

```bash
# Install pytest-bdd
uv pip install pytest-bdd

# Generate step definition stubs
pytest-bdd generate tests/bdd/features/*.feature > tests/bdd/step_defs/generated_steps.py
```

### Run Tests

```bash
# Run all BDD tests
pytest tests/bdd/ -v

# Run by phase
pytest tests/bdd/ -m "phase0" -v

# Run by component
pytest tests/bdd/ -m "controller" -v

# Run by principle
pytest tests/bdd/ -m "Integrity" -v

# Run specific feature
pytest tests/bdd/features/security_trust_mtls.feature -v
```

## Implementation Status

### Phase 0 (Current)
- [ ] `capability_schema_validation.feature` — Step definitions needed
- [ ] `developer_experience_quickstart.feature` — Step definitions needed

### Phase 1 (Next)
- [ ] `capability_routing.feature` — Not started
- [ ] `controller_privilege_boundary.feature` — Not started

### Phase 2
- [ ] `worker_sandboxing.feature` — Not started
- [ ] `mesh_state_coordination.feature` — Not started (Phase 3)

### Phase 4
- [ ] `security_trust_mtls.feature` — Not started
- [ ] `deployment_models.feature` — Not started

## Mascot Ownership

### Wendy 🐰 (Security)
- `security_trust_mtls.feature`
- `worker_sandboxing.feature`
- `controller_privilege_boundary.feature`

### Gary 🦆 (Consistency)
- `capability_schema_validation.feature`
- `capability_routing.feature`
- `mesh_state_coordination.feature`

### Kevin 🦙 (Portability)
- `developer_experience_quickstart.feature`
- `deployment_models.feature`

## Next Steps

1. **Create step definitions** for Phase 0 features:
   - `step_defs/capability_steps.py`
   - `step_defs/devx_steps.py`

2. **Wire into CI**:
   - Add BDD job to `.github/workflows/test.yml`
   - Mark as `allow_failure: true` initially
   - Graduate to required when Phase 0 complete

3. **Link to requirements traceability**:
   - Update `docs/planning/REQUIREMENTS_TRACEABILITY.md`
   - Add BDD scenarios to micronarrative catalog

4. **Implement fixtures**:
   - `conftest.py` with controller/worker test fixtures
   - Mock capability schema
   - Test certificate infrastructure

## Related Documentation

- [HEY-SONNET-READ-THIS.md](HEY-SONNET-READ-THIS.md) — Original instructions from ChatGPT
- [features/gherkin-index.md](features/gherkin-index.md) — Feature catalog
- [docs/planning/REQUIREMENTS_TRACEABILITY.md](../../docs/planning/REQUIREMENTS_TRACEABILITY.md) — Requirements mapping
- [docs/ARCHITECTURAL_MENAGERIE_GUIDE.md](../../docs/ARCHITECTURAL_MENAGERIE_GUIDE.md) — Mascot framework
- [.vscode/AGENT_CONTEXT.md](../../.vscode/AGENT_CONTEXT.md) — Controller/worker refactor context

---

**Generated**: 2025-11-10 (pickle jar v2 from ChatGPT)  
**Framework**: pytest-bdd  
**Coverage**: Controller/worker refactor (Issues #27-#31, Phases 0-4)
