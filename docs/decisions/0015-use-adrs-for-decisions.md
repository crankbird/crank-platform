# ADR-0015: Use ADRs as Canonical Record of Architectural Decisions

**Status**: Accepted
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Documentation, Knowledge & Repo Structure](../planning/adr-backlog-2025-11-16.md#documentation-knowledge--repo-structure)

## Context and Problem Statement

Architectural decisions are made continuously but often lost in emails, chat, or tribal knowledge. Future team members need to understand why decisions were made, what alternatives were considered, and what tradeoffs were accepted. How should we capture and preserve architectural decisions?

## Decision Drivers

- Preservation: Decisions survive team turnover
- Context: Understand why decisions were made
- Discoverability: Easy to find past decisions
- Version control: Track decision evolution
- Accountability: Clear decision ownership
- Learning: New team members understand rationale

## Considered Options

- **Option 1**: Architecture Decision Records (ADRs) - Accepted
- **Option 2**: Wiki documentation
- **Option 3**: Design documents in Google Docs

## Decision Outcome

**Chosen option**: "Architecture Decision Records (ADRs)", because they provide version-controlled, discoverable, and standardized documentation of architectural decisions.

### Positive Consequences

- Decisions version controlled with code
- Standard format (easy to scan)
- Git-searchable
- Clear decision ownership
- Context preservation
- Supports decision review

### Negative Consequences

- Discipline required to create ADRs
- Can become stale if not maintained
- Need education on when to create ADR
- Overhead for simple decisions

## Pros and Cons of the Options

### Option 1: Architecture Decision Records

Markdown files in `docs/decisions/` following ADR pattern.

**Pros:**
- Version controlled
- Standard format
- Git-searchable
- Lives with code
- Easy to review in PRs

**Cons:**
- Requires discipline
- Overhead
- Can go stale

### Option 2: Wiki Documentation

Confluence, GitHub Wiki, Notion.

**Pros:**
- Easy to edit
- Rich formatting
- Search features
- Collaborative

**Cons:**
- Not version controlled with code
- Can drift from reality
- Access control issues
- Not in PRs

### Option 3: Design Documents in Google Docs

Shared documents folder.

**Pros:**
- Familiar tool
- Easy collaboration
- Comments/suggestions

**Cons:**
- Not version controlled
- Not searchable with code
- Access control
- Orphaned docs

## Links

- [Implements] This ADR itself (meta-ADR)
- [Related to] `docs/decisions/README.md` (ADR index)
- [Related to] `docs/decisions/0000-template.md` (ADR template)

## Implementation Notes

**When to Create an ADR**:
- Technology choice (language, framework, database)
- Architectural pattern adoption
- Security model decision
- Deployment strategy
- Significant tradeoff decision
- Breaking change to existing patterns

**When NOT to Create an ADR**:
- Implementation details (how to write a function)
- Tactical bug fixes
- Obvious/uncontroversial choices
- Temporary workarounds

**ADR Lifecycle**:

```
Proposed → Accepted → (Deprecated → Superseded)
```

**Directory Structure**:

```
docs/decisions/
  README.md              # Index and guidelines
  0000-template.md       # Template for new ADRs
  0001-*.md              # First ADR
  0002-*.md              # Second ADR
  ...
```

**Format**:
- Sequential numbering (0001, 0002, ...)
- Descriptive filename (lowercase-with-hyphens)
- Standard sections (Context, Decision, Consequences, Alternatives)
- Status tracking (Proposed/Accepted/Deprecated/Superseded)

**Integration with Workflow**:
1. Proposal phase → Create ADR with Status: Proposed
2. Discussion happens in PR comments
3. Approval → Status: Accepted, merge PR
4. Implementation references ADR in commit messages
5. Review → ADRs reviewed quarterly, updated if needed

**Example ADR Reference in Commit**:

```
feat: implement local-first agent execution

Implements ADR-0004 (Prefer Local-First Agent Execution).
Routes agent requests to local workers by default, with
cloud escalation for resource-intensive tasks.
```

## Review History

- 2025-11-16 - Initial decision (formalizing existing practice)
