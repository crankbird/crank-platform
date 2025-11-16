# ADR-0017: Use Zettelkasten Notes with YAML Front-Matter as Primary Knowledge System

**Status**: Accepted
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Documentation, Knowledge & Repo Structure](../planning/adr-backlog-2025-11-16.md#documentation-knowledge--repo-structure)

## Context and Problem Statement

AI agents (Agent13/Codex, Agent14/Sonnet) accumulate knowledge through conversations, code analysis, and problem-solving. This knowledge needs to be preserved, linked, and retrievable across sessions. How should we store and organize accumulated knowledge?

## Decision Drivers

- Knowledge persistence: Survive across agent sessions
- Linkability: Connect related concepts
- Human-readable: Developers can read and edit
- Version control: Git-friendly format
- Searchability: Find knowledge by topic/tags
- Agent-friendly: Easy for AI to parse and generate

## Considered Options

- **Option 1**: Zettelkasten with YAML front-matter - Accepted
- **Option 2**: Database with full-text search
- **Option 3**: Wiki system (Obsidian/Notion)

## Decision Outcome

**Chosen option**: "Zettelkasten with YAML front-matter", because it provides Git-compatible, human-readable knowledge storage with rich linking while being easy for AI agents to parse and generate.

### Positive Consequences

- Git-native knowledge versioning
- Human-readable markdown
- AI agents can parse/generate easily
- Rich linking between concepts
- Tag-based organization
- Works offline
- YAML front-matter provides structured metadata

### Negative Consequences

- Manual linking required
- No built-in search (need tooling)
- File-based (not optimized for large scale)
- Requires discipline to maintain links

## Pros and Cons of the Options

### Option 1: Zettelkasten with YAML Front-Matter

Markdown files with YAML metadata and [[wiki-links]].

**Pros:**
- Git-compatible
- Human-readable
- AI-friendly
- Rich linking
- Version controlled
- Offline-first

**Cons:**
- Manual maintenance
- Need search tooling
- File-based limits scale
- Link integrity not enforced

### Option 2: Database with Full-Text Search

PostgreSQL/SQLite with FTS.

**Pros:**
- Fast search
- Referential integrity
- Optimized for scale
- Query capabilities

**Cons:**
- Not Git-friendly
- Binary format
- Harder for humans to browse
- Requires database server

### Option 3: Wiki System (Obsidian/Notion)

Dedicated knowledge management tool.

**Pros:**
- Rich UI
- Built-in search
- Graph visualization
- Easy linking

**Cons:**
- Vendor lock-in
- Not always Git-compatible
- May not work offline
- AI integration harder

## Links

- [Related to] ADR-0005 (File-backed state representation)
- [Related to] Existing zettel workers (`crank_sonnet_zettel_manager.py`, `crank_codex_zettel_repository.py`)
- [Related to] `golden/zettels-old-messy/` (prior implementation)

## Implementation Notes

**Zettel Format**:

```markdown
---
id: 20251116-controller-worker-pattern
title: "Controller/Worker Architectural Pattern"
created: 2025-11-16T10:00:00Z
updated: 2025-11-16T12:00:00Z
tags: [architecture, patterns, controller, worker]
related:
  - 20251115-capability-routing
  - 20251109-mtls-security
agent: agent14-sonnet
status: active
---

# Controller/Worker Architectural Pattern

## Core Concept

The controller/worker pattern separates privileged coordination (controller)
from untrusted execution (workers). The controller manages routing, trust,
and mesh coordination while workers provide capabilities.

## Key Benefits

- Clear privilege boundary
- Workers fully sandboxed
- Hybrid deployment (containers + native)
- Capability-based routing

## Implementation

See [[20251115-capability-routing]] for routing algorithm.
See [[20251109-mtls-security]] for trust model.

## References

- ADR-0001: Use Controller/Worker Model
- `docs/architecture/CONTROLLER_WORKER_MODEL.md`
```

**Directory Structure**:

```
~/.crank/
  zettels/
    agent13/                    # Codex's zettels
      20251116-topic.md
    agent14/                    # Sonnet's zettels
      20251116-topic.md
    shared/                     # Cross-agent knowledge
      20251116-topic.md
```

**Zettel Worker Pattern**:

```python
class ZettelManager:
    def create_zettel(
        self,
        title: str,
        content: str,
        tags: list[str],
        related: list[str] = []
    ) -> str:
        """Create new zettel with YAML front-matter."""
        zettel_id = datetime.now().strftime("%Y%m%d-%H%M%S")

        front_matter = {
            "id": zettel_id,
            "title": title,
            "created": datetime.now().isoformat(),
            "tags": tags,
            "related": related,
            "agent": self.agent_id,
            "status": "active"
        }

        zettel = f"---\n{yaml.dump(front_matter)}---\n\n{content}"

        path = self.zettel_dir / f"{zettel_id}.md"
        path.write_text(zettel)

        return zettel_id

    def find_related(self, tags: list[str]) -> list[str]:
        """Find zettels by tags."""
        # Grep YAML front-matter for matching tags
        matches = []
        for zettel_path in self.zettel_dir.glob("*.md"):
            with open(zettel_path) as f:
                if f.read(4) == "---\n":
                    front_matter = yaml.safe_load(
                        f.read().split("---")[0]
                    )
                    if any(tag in front_matter.get("tags", []) for tag in tags):
                        matches.append(zettel_path.stem)
        return matches
```

**Search Integration**:
- Use `ripgrep` for fast search across zettels
- Index tags in capability registry for agent queries
- Future: Embedding-based semantic search

## Review History

- 2025-11-16 - Initial decision (formalizing existing zettel workers)
