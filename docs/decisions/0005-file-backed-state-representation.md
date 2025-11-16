# ADR-0005: Represent Agent and Platform State as File-Backed JSONL/YAML

**Status**: Accepted
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Core Platform & Agent Architecture](../planning/adr-backlog-2025-11-16.md#core-platform--agent-architecture)

## Context and Problem Statement

Agent state (conversation history, context, preferences) and platform state (worker registry, capability catalog) need to be persisted and synchronized. We need a storage format that supports version control, human readability, and efficient incremental updates.

## Decision Drivers

- Version control: Git-friendly formats enable state tracking
- Human readability: Debugging and manual inspection
- Incremental updates: Append-only for conversation logs
- Simplicity: Avoid database complexity for small-scale deployments
- Portability: Easy to backup, migrate, sync across devices
- Tooling: Standard formats have rich ecosystem

## Considered Options

- **Option 1**: File-backed JSONL/YAML (chosen)
- **Option 2**: SQLite database
- **Option 3**: Redis/in-memory store

## Decision Outcome

**Chosen option**: "File-backed JSONL/YAML", because it provides Git compatibility, human readability, and simplicity while meeting performance needs for agent-scale workloads.

### Positive Consequences

- Git-native versioning of agent state
- Human-readable for debugging
- Easy backup/restore (just files)
- No database server to manage
- Works offline automatically
- JSONL append-only perfect for conversation logs
- YAML ideal for configuration/registry data

### Negative Consequences

- File locking complexity for concurrent writes
- Less efficient for complex queries
- No built-in indexing
- Need manual schema evolution
- File size growth requires rotation strategy

## Pros and Cons of the Options

### Option 1: File-Backed JSONL/YAML

JSONL for append-only logs, YAML for structured state.

**Pros:**
- Git-compatible
- Human-readable
- Simple tooling (cat, grep, jq)
- No server dependencies
- Easy to backup
- Append-only JSONL efficient for logs

**Cons:**
- Manual file management
- Limited query capabilities
- File locking needed
- Not ideal for high concurrency

### Option 2: SQLite Database

Embedded SQL database in local file.

**Pros:**
- ACID transactions
- Indexing and query optimization
- Schema enforcement
- Mature tooling
- Good performance

**Cons:**
- Binary format (not Git-friendly)
- Harder to manually inspect
- Schema migrations needed
- Overkill for simple state
- Not human-readable

### Option 3: Redis/In-Memory Store

External key-value store with persistence.

**Pros:**
- Very fast
- Rich data structures
- Pub/sub capabilities
- Good for caching

**Cons:**
- Requires server process
- Not Git-compatible
- Memory-intensive
- Persistence is secondary concern
- Complexity for simple use cases

## Links

- [Related to] ADR-0018 (Zettelkasten uses YAML front-matter)
- [Related to] ADR-0020 (Git-based CI depends on file-backed state)
- [Enables] Version control of agent conversations and context

## Implementation Notes

**File Structure:**

```
~/.crank/
  agents/
    agent-123/
      config.yaml          # Agent configuration
      conversation.jsonl   # Append-only conversation log
      context.yaml         # Current context/state
  platform/
    workers.yaml           # Worker registry
    capabilities.yaml      # Capability catalog
    mesh.yaml             # Mesh state
```

**JSONL Format** (conversations):

```jsonl
{"ts":"2025-11-16T10:00:00Z","role":"user","content":"Hello"}
{"ts":"2025-11-16T10:00:02Z","role":"assistant","content":"Hi!"}
```

**YAML Format** (configuration):

```yaml
agent_id: agent-123
model: claude-sonnet-4
capabilities: [email, docs]
```

**File Locking:**
- Use flock() for exclusive writes
- Read-only operations lockless
- JSONL appends use O_APPEND for atomicity

## Review History

- 2025-11-16 - Initial decision
