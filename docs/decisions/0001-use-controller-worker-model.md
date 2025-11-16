# ADR-0001: Use Controller/Worker Model

**Status**: Accepted
**Date**: 2025-11-09
**Deciders**: Platform Team
**Technical Story**: Phase 0-2 Architecture Refactor (Issues #27-29)

## Context and Problem Statement

The platform started as a monolithic service but needed better separation of concerns for GPU resource management, worker isolation, and distributed capability routing. How should we architect the system to support multiple execution strategies (containers, native, hybrid) while maintaining security and trust?

## Decision Drivers

- Need to support hybrid deployment (macOS Metal native + containerized workers)
- GPU resources require privileged access conflicting with worker sandboxing
- Capability-based routing more reliable than service discovery
- Workers should be logical providers, not tied to container boundaries
- Controller must be single point of trust per node

## Considered Options

- **Option 1**: Controller + Worker + Capability model
- **Option 2**: Pure microservices mesh
- **Option 3**: Maintain platform-centric monolith

## Decision Outcome

**Chosen option**: "Controller + Worker + Capability model", because it provides the right balance of isolation, flexibility, and security while supporting our hybrid deployment requirements.

### Positive Consequences

- Workers can run as containers, native processes, or hybrid
- Clear separation: controller = privileged, workers = sandboxed
- Capability-based routing is deterministic and testable
- Supports macOS Metal native execution for GPU workloads
- Foundation for distributed mesh (future)

### Negative Consequences

- More complexity than pure monolith
- Need to manage controller lifecycle
- Workers depend on controller for certificate bootstrap
- Migration effort for existing services

## Pros and Cons of the Options

### Option 1: Controller + Worker + Capability Model

Workers are logical service providers. Controller supervises per-node.

**Pros:**
- Supports hybrid deployment strategies
- Clear privilege boundary (controller trusted, workers sandboxed)
- Capability routing more reliable than DNS-based discovery
- Execution strategy can vary by platform (containers/native/hybrid)
- Foundation for future distributed mesh

**Cons:**
- More complex than monolith
- Controller becomes critical dependency
- Need certificate bootstrap flow
- Migration effort for existing code

### Option 2: Pure Microservices Mesh

Each service independently deployed with service mesh (Istio/Linkerd).

**Pros:**
- Industry standard pattern
- Rich tooling ecosystem
- Clear service boundaries
- Easy to scale individual services

**Cons:**
- All workers must be containerized (blocks macOS Metal native)
- Complex mesh configuration
- Overhead for small deployments
- Doesn't solve GPU privilege escalation problem
- Service discovery unreliable for capability routing

### Option 3: Maintain Platform-Centric Monolith

Single platform service manages all capabilities internally.

**Pros:**
- Simplest architecture
- No distributed systems complexity
- Easy to develop and debug
- Single deployment unit

**Cons:**
- Can't support hybrid execution (containers + native)
- GPU access requires entire platform to be privileged
- No worker isolation
- Difficult to scale individual capabilities
- Not aligned with future distributed vision

## Links

### Architecture References

- [Refined by] ADR-0002 (mTLS security model)
- [Refined by] ADR-0006 (Capability registry integration)
- [Refined by] ADR-0009 (CPU/GPU worker separation)
- [Related to] ADR-0010 (Containers as primary deployment)

### Upstream Context

- [Informed by] docs/knowledge/philosophy/governed-service-fabric-agentic-economy.md
- [Aligned with] docs/knowledge/personas/zk20251112-002_upn-systems-architect.md (distributed systems thinkers)

### Behavioral Specifications

- [Validated by] F-CONTROLLER-PRIVILEGE (tests/bdd/features/controller_privilege_boundary.feature)
- [Validated by] F-WORKER-SANDBOXING (tests/bdd/features/worker_sandboxing.feature)
- [Validated by] F-CAPABILITY-ROUTING (tests/bdd/features/capability_routing.feature)

### Planning & Implementation

- [Architecture doc] docs/architecture/CONTROLLER_WORKER_MODEL.md
- [Roadmap] docs/planning/phase-3-controller-extraction.md
- [Implemented in] src/crank/worker_runtime/, src/crank/capabilities/

### Agent Guidance

- [Constrains] .vscode/AGENT_CONTEXT.md (Sections: Architecture Refactor, Worker Development Pattern)

## Implementation Notes

Implemented in three phases:
- **Phase 0** (Issue #27): Capability schema + worker runtime foundation
- **Phase 1** (Issue #28): 8 workers migrated to `WorkerApplication` pattern
- **Phase 2** (Issue #29): Base worker image + hybrid deployment
- **Phase 3** (Issue #30): Controller extraction (in progress)

## Review History

- 2025-11-09 - Initial decision during Phase 0 planning
- 2025-11-10 - Reaffirmed after Phase 1 completion (40.4% code reduction achieved)
- 2025-11-15 - Validated by successful security consolidation (Issue #19)
