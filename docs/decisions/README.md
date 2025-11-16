# Architecture Decision Records (ADRs)

**Purpose**: Document significant architectural and design decisions
**Format**: Numbered sequential records following ADR pattern
**Status**: Active

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences. ADRs help teams understand:

- **What** decision was made
- **When** it was made
- **Why** it was made (context and constraints)
- **Who** was involved
- **What** alternatives were considered
- **What** are the consequences (positive and negative)

## When to Create an ADR

Create an ADR when you make a decision that:

- Affects the structure of the system
- Is difficult or expensive to reverse
- Impacts non-functional requirements (performance, security, scalability)
- Violates or extends existing patterns
- Establishes a new pattern others should follow

**Examples:**
- Choosing a communication protocol
- Adopting a new architectural pattern
- Security model changes
- Database/storage decisions
- Deployment strategy changes

## ADR Lifecycle

```
Proposed → Accepted → Deprecated → Superseded
```

- **Proposed**: Under discussion, not yet implemented
- **Accepted**: Approved and being implemented or already implemented
- **Deprecated**: No longer recommended but not yet replaced
- **Superseded**: Replaced by a newer ADR (link to replacement)

## Naming Convention

```
NNNN-brief-title.md
```

- `NNNN`: Zero-padded sequential number (0001, 0002, etc.)
- `brief-title`: Lowercase with hyphens, descriptive

**Examples:**
- `0001-use-controller-worker-model.md`
- `0002-adopt-mtls-for-all-services.md`
- `0003-consolidate-security-module.md`

## ADR Template

Use the template in `0000-template.md` for new ADRs.

## Current ADRs

### Core Platform

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [0001](0001-use-controller-worker-model.md) | Use Controller/Worker Model | Accepted | 2025-11-09 |
| [0004](0004-prefer-local-first-agent-execution.md) | Prefer Local-First Agent Execution | Accepted | 2025-11-16 |
| [0005](0005-file-backed-state-representation.md) | Use File-Backed State Representation | Accepted | 2025-11-16 |
| [0006](0006-verb-capability-registry.md) | Verb/Capability Registry Integration | Accepted | 2025-11-16 |
| [0007](0007-message-bus-async-orchestration.md) | Message Bus for Async Orchestration | Proposed | 2025-11-16 |
| [0008](0008-python-primary-worker-runtime.md) | Python as Primary Runtime | Accepted | 2025-11-16 |
| [0009](0009-separate-cpu-gpu-workers.md) | Separate CPU and GPU Workers | Accepted | 2025-11-16 |
| [0010](0010-containers-primary-deployment.md) | Containers as Primary Deployment | Accepted | 2025-11-16 |

### Security

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [0002](0002-adopt-mtls-for-all-services.md) | Adopt mTLS for All Services | Accepted | 2025-11-15 |
| [0003](0003-consolidate-security-module.md) | Consolidate Security Module | Accepted | 2025-11-15 |
| [0011](0011-abac-agent-permissions.md) | ABAC for Agent Permissions | Proposed | 2025-11-16 |
| [0012](0012-default-deny-network-egress.md) | Default-Deny Network Egress | Proposed | 2025-11-16 |
| [0013](0013-shift-left-security-scanning.md) | Shift-Left Security Scanning | Proposed | 2025-11-16 |
| [0014](0014-secrets-management-standard.md) | Secrets Management Standard | Proposed | 2025-11-16 |

### Documentation

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [0015](0015-use-adrs-for-decisions.md) | Use ADRs for Architectural Decisions | Accepted | 2025-11-16 |
| [0016](0016-mono-repo-consolidation.md) | Mono-Repo Consolidation for Crankbird | Proposed | 2025-11-16 |
| [0017](0017-zettelkasten-knowledge-system.md) | Zettelkasten Notes as Knowledge System | Accepted | 2025-11-16 |
| [0018](0018-docforge-semantic-rendering.md) | Use Docforge for Semantic Document Rendering | Accepted | 2025-11-16 |
| [0019](0019-documentation-layout-standard.md) | Documentation Layout Standard | Accepted | 2025-11-16 |

### Developer Experience

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [0020](0020-git-based-ci-pipelines.md) | Git-Based CI Pipelines | Accepted | 2025-11-16 |
| [0021](0021-multi-platform-development.md) | Support macOS, Linux, Windows (WSL) | Accepted | 2025-11-16 |
| [0022](0022-agent-assisted-development.md) | Agent-Assisted Development as First-Class | Accepted | 2025-11-16 |

### Platform Services

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [0023](0023-capability-publishing-protocol.md) | Capability Publishing and Discovery Protocol | Proposed | 2025-11-16 |
| [0024](0024-observability-strategy.md) | Observability Strategy (Logs, Metrics, Traces) | Proposed (Extended) | 2025-11-16 |
| [0025](0025-plugin-based-agent-extensions.md) | Plugin-Based Extension Model for Agents | Proposed | 2025-11-16 |
| [0026](0026-controller-slo-and-idempotency.md) | Controller-Level SLO Enforcement and Idempotency Manager | Proposed | 2025-11-16 |
| [0027](0027-controller-policy-enforcement.md) | Controller Policy Enforcement (CAP/OPA Integration) | Proposed | 2025-11-16 |

## Relationship to Other Documentation

- **Proposals** (`docs/proposals/`) - Strategic ideas, may lead to ADRs
- **ADRs** (`docs/decisions/`) - Committed architectural decisions
- **Planning** (`docs/planning/`) - Implementation plans following ADRs
- **Architecture Docs** (`docs/architecture/`) - Current state reflecting ADRs
- **Archive** (`docs/archive/`) - Superseded ADRs move here with "Superseded by ADR-XXXX" status

## References

- [ADR GitHub Organization](https://adr.github.io/)
- [Michael Nygard's ADR article](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions)
