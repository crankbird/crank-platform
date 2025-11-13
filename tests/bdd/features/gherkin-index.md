# Crank Platform — Gherkin Pickle Jar (v2)

This set is derived from the root `README.md` and aligned to the controller/worker refactor plan.
Each feature includes traceability tags for **Brand Science principles**, **Phase**, **Issues**, and **Components**.

> **Sonnet:** see `../HEY-SONNET-READ-THIS.md` for placement and CI wiring instructions.

## Feature Files
1. `security_trust_mtls.feature` — PKI, mTLS, rotation
2. `capability_routing.feature` — capability source-of-truth
3. `worker_sandboxing.feature` — least-privilege execution
4. `controller_privilege_boundary.feature` — privileged boundary
5. `mesh_state_coordination.feature` — state over execution
6. `capability_schema_validation.feature` — versioned schema & signatures
7. `developer_experience_quickstart.feature` — DX quickstart invariants
8. `deployment_models.feature` — acceptance for post-refactor targets

### Tagging Conventions
- `@principle(Integrity)` `@principle(Efficiency)` `@principle(Empathy)` `@principle(Legitimacy)` `@principle(Resilience)` `@principle(Culture)`
- `@phase(0..4)` → matches refactor roadmap phases
- `@issue(27..31)` → GitHub issues called out in README
- `@component(controller|worker|mesh|capability-schema|security|devx)`
- Scenario IDs follow `CRNK-<FeatureCode>-###`

**Generated:** 2025-11-10
