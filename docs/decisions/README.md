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

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [0001](0001-use-controller-worker-model.md) | Use Controller/Worker Model | Accepted | 2025-11-09 |
| [0002](0002-adopt-mtls-for-all-services.md) | Adopt mTLS for All Services | Accepted | 2025-11-15 |
| [0003](0003-consolidate-security-module.md) | Consolidate Security Module | Accepted | 2025-11-15 |

## Relationship to Other Documentation

- **Proposals** (`docs/proposals/`) - Strategic ideas, may lead to ADRs
- **ADRs** (`docs/decisions/`) - Committed architectural decisions
- **Planning** (`docs/planning/`) - Implementation plans following ADRs
- **Architecture Docs** (`docs/architecture/`) - Current state reflecting ADRs
- **Archive** (`docs/archive/`) - Superseded ADRs move here with "Superseded by ADR-XXXX" status

## References

- [ADR GitHub Organization](https://adr.github.io/)
- [Michael Nygard's ADR article](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions)
