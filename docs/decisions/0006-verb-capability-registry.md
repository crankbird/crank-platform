# ADR-0006: Introduce Verb/Capability Registry as the Integration Layer

**Status**: Accepted
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Core Platform & Agent Architecture](../planning/adr-backlog-2025-11-16.md#core-platform--agent-architecture)

## Context and Problem Statement

Workers provide diverse capabilities (email classification, document conversion, image analysis). We need a way for agents and controllers to discover what capabilities exist, route requests appropriately, and ensure type-safe communication. How should we represent and discover capabilities?

## Decision Drivers

- Discoverability: Agents must find capabilities without hardcoding
- Type safety: Input/output schemas enforced
- Routing correctness: Requests go to capable workers
- Extensibility: New capabilities added without platform changes
- Introspection: Humans and tools can understand what's available
- MCP alignment: Model Context Protocol compatibility

## Considered Options

- **Option 1**: Verb/Capability Registry with schemas (chosen)
- **Option 2**: REST API with OpenAPI specs
- **Option 3**: Service mesh with DNS-based discovery

## Decision Outcome

**Chosen option**: "Verb/Capability Registry with schemas", because it provides centralized capability discovery, type safety, and enables routing correctness while aligning with MCP standards.

### Positive Consequences

- Single source of truth for capabilities
- Type-safe capability invocation
- Routing decisions based on declared capabilities
- Agents discover capabilities programmatically
- Schema validation prevents integration errors
- MCP-compatible capability declaration

### Negative Consequences

- Registry must be kept in sync with workers
- Schema evolution requires versioning
- Central registry is single point of failure (mitigated by file-backing)
- Manual schema definition burden on worker authors

## Pros and Cons of the Options

### Option 1: Verb/Capability Registry with Schemas

Central registry maps capability names to schemas and worker addresses.

**Pros:**
- Centralized capability catalog
- Schema validation enforced
- Enables smart routing
- Programmatic discovery
- Version control (file-backed YAML)
- MCP alignment

**Cons:**
- Registry sync overhead
- Schema evolution complexity
- Single point of truth (must be reliable)
- Manual schema authoring

### Option 2: REST API with OpenAPI Specs

Each worker exposes OpenAPI spec at `/openapi.json`.

**Pros:**
- Industry standard
- Auto-generated from code
- Rich tooling (Swagger, etc.)
- Self-documenting

**Cons:**
- No central catalog (discovery problem)
- Must query each worker individually
- API-centric (not capability-centric)
- Doesn't support routing by capability
- Not MCP-compatible

### Option 3: Service Mesh with DNS-Based Discovery

Service mesh (Consul, Istio) handles discovery.

**Pros:**
- Industry standard
- Battle-tested
- Rich feature set
- Automatic health checking

**Cons:**
- Complex infrastructure
- Service-centric not capability-centric
- DNS doesn't encode schemas
- Overkill for small deployments
- Doesn't solve capability routing

## Links

- [Refines] ADR-0001 (Controller/Worker model needs capability routing)
- [Related to] Phase 0 implementation (capability schema foundation)
- [Related to] `src/crank/capabilities/` module
- [Enables] ADR-0023 (Capability publishing protocol)
- [Extended by] Phase 3 Session 1 (FaaS metadata, SLO constraints, identity fields - see PHASE_3_ATTACK_PLAN.md)

## Implementation Notes

**Extended Capability Schema** (Phase 3):

As of Phase 3 (November 2025), the capability schema has been extended to support:
- **FaaS workers**: `runtime`, `env_profile`, `constraints` ([faas-worker-specification.md](../proposals/faas-worker-specification.md))
- **SLO enforcement**: `slo` field with latency/availability targets ([ADR-0026](0026-controller-slo-and-idempotency.md))
- **Identity-based auth**: `spiffe_id`, `required_capabilities` ([ADR-0027](0027-controller-policy-enforcement.md))
- **Economic routing**: `cost_tokens_per_invocation`, `slo_bid` ([from-job-scheduling-to-capability-markets.md](../proposals/from-job-scheduling-to-capability-markets.md))
- **Multi-controller mesh**: `controller_affinity` ([enhancement-roadmap.md](../proposals/enhancement-roadmap.md))

All extended fields are **optional** and backward-compatible with Phase 0-2 workers. See [PHASE_3_ATTACK_PLAN.md](../planning/PHASE_3_ATTACK_PLAN.md) for complete schema definition.

**Capability Registry Format** (`capabilities.yaml`):

```yaml
capabilities:
  - verb: classify_email
    version: "1.0"
    schema:
      input:
        type: object
        properties:
          email_text: {type: string}
          subject: {type: string}
      output:
        type: object
        properties:
          category: {type: string, enum: [spam, important, normal]}
          confidence: {type: number, minimum: 0, maximum: 1}
    workers:
      - worker_id: email-classifier-01
        address: https://localhost:8501
        load: 0.3

  - verb: convert_document
    version: "1.0"
    schema:
      input:
        type: object
        properties:
          source_format: {type: string}
          target_format: {type: string}
          document: {type: string}
      output:
        type: object
        properties:
          converted_document: {type: string}
    workers:
      - worker_id: doc-converter-01
        address: https://localhost:8502
```

**Routing Algorithm:**
1. Agent requests capability by verb name
2. Controller looks up verb in registry
3. Validates input against schema
4. Selects worker (least loaded, health check passed)
5. Routes request to worker
6. Validates output against schema
7. Returns to agent

## Review History

- 2025-11-16 - Initial decision
