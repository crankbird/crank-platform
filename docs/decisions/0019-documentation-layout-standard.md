# ADR-0019: Documentation Layout Standard

**Status**: Accepted
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Documentation, Knowledge & Repo Structure](../planning/adr-backlog-2025-11-16.md#documentation-knowledge--repo-structure)

## Context and Problem Statement

Documentation serves multiple audiences (developers, operators, AI agents) and covers multiple lifecycle phases (proposals, decisions, plans, architecture, operations). How should we organize documentation to support clear workflows and discoverability?

## Decision Drivers

- Workflow integration: Align with dev process (propose→decide→plan→implement)
- Audience clarity: Easy to find relevant docs
- Lifecycle separation: Distinguish active vs historical
- AI-friendly: Agents can navigate structure
- Version control: Git-friendly organization
- Searchability: Clear directory hierarchy

## Considered Options

- **Option 1**: Workflow-based layout (proposals→decisions→planning→architecture→archive) - Accepted
- **Option 2**: Audience-based layout (developer/operator/architect)
- **Option 3**: Flat structure with metadata tags

## Decision Outcome

**Chosen option**: "Workflow-based layout", because it mirrors the development lifecycle and makes it clear what phase each document represents, supporting both human workflows and AI agent navigation.

### Positive Consequences

- Clear workflow mapping
- Easy to find documents by phase
- Historical tracking (archive/)
- Template integration
- AI agents understand lifecycle
- Supports contribution workflow

### Negative Consequences

- Documents may fit multiple categories
- Requires discipline to maintain
- Cross-cutting concerns need linking
- Larger directory tree

## Pros and Cons of the Options

### Option 1: Workflow-Based Layout

Organize by development lifecycle phase.

**Pros:**
- Mirrors dev process
- Clear lifecycle
- Template support
- Workflow integration
- Historical tracking

**Cons:**
- Multi-category docs
- Requires maintenance
- Needs cross-linking

### Option 2: Audience-Based Layout

Organize by reader role.

**Pros:**
- Reader-focused
- Role clarity
- Targeted content

**Cons:**
- Doesn't match workflow
- Duplicate content likely
- Harder to track lifecycle

### Option 3: Flat Structure with Metadata

Single directory with YAML front-matter tags.

**Pros:**
- Simple structure
- Flexible categorization
- Tag-based search

**Cons:**
- No visual organization
- Harder to browse
- Requires search tooling
- No hierarchy

## Links

- [Related to] ADR-0015 (Use ADRs for decisions)
- [Related to] ADR-0017 (Zettelkasten knowledge system)
- [Related to] ADR-0018 (Docforge rendering)
- [Implements] `.github/CONTRIBUTING.md` workflow
- [Implements] Diátaxis framework

## Implementation Notes

**Directory Structure** (Current):

```
docs/
  README.md                      # Documentation index
  ARCHITECTURE.md                # High-level platform overview
  VISION.md                      # Long-term vision

  proposals/                     # Strategic ideas (pre-decision)
    .template.md
    YYYY-MM-DD-proposal-name.md

  decisions/                     # Architectural decisions (ADRs)
    0000-template.md
    README.md
    0001-use-controller-worker-model.md
    0002-enforce-mtls-everywhere.md
    ...

  planning/                      # Implementation plans (post-decision)
    .template.md
    phase-1-worker-migration.md
    test-data-corpus.md

  architecture/                  # Canonical architecture docs
    CONTROLLER_WORKER_MODEL.md
    SECURITY_MODULE_CONSOLIDATION.md
    REQUIREMENTS_TRACEABILITY.md

  development/                   # Developer guides
    CODE_QUALITY_STRATEGY.md
    TESTING_STRATEGY.md
    ML_DEVELOPMENT_GUIDE.md
    PYLANCE_ML_CONFIGURATION.md

  operations/                    # Operational runbooks
    deployment-procedures.md
    monitoring-setup.md

  reports/                       # Status reports and reviews
    2025-11-integration-report.md
    documentation-review.md

  knowledge/                     # Cross-cutting knowledge
    concepts/
    patterns/

  archive/                       # Deprecated/historical docs
    2025-11-09-pre-controller-refactor/
    superseded-proposals/

  schemas/                       # JSON schemas and contracts
    capability-schema.json

  security/                      # Security documentation
    threat-model.md
```

**Workflow Mapping**:

1. **Proposal Phase** → `docs/proposals/`
   - New ideas, RFCs, strategic initiatives
   - Use proposal template
   - Discuss in GitHub Discussions

2. **Decision Phase** → `docs/decisions/`
   - ADRs documenting choices
   - Use ADR template (0000-template.md)
   - Status: Proposed → Accepted/Rejected

3. **Planning Phase** → `docs/planning/`
   - Implementation plans, phase breakdowns
   - Use planning template
   - Link to ADRs and GitHub Issues

4. **Implementation Phase** → Code + `docs/architecture/`
   - Canonical architecture docs
   - Updated as code evolves

5. **Operations Phase** → `docs/operations/`
   - Runbooks, deployment guides
   - Monitoring and troubleshooting

6. **Archival Phase** → `docs/archive/`
   - Superseded documents
   - Historical snapshots
   - Keep for context

**File Naming Conventions**:

- **Proposals**: `YYYY-MM-DD-descriptive-name.md`
- **ADRs**: `NNNN-descriptive-name.md` (sequential)
- **Plans**: `phase-N-name.md` or `descriptive-name.md`
- **Architecture/Development**: `ALL_CAPS_DESCRIPTIVE.md`
- **Reports**: `YYYY-MM-descriptive-name.md`

**Cross-Linking**:

```markdown
## Related Documents

- [ADR-0001](../decisions/0001-use-controller-worker-model.md) - Architecture decision
- [Controller/Worker Architecture](../architecture/CONTROLLER_WORKER_MODEL.md) - Implementation
- [Phase 3 Plan](../planning/phase-3-controller-extraction.md) - Execution plan
```

**AI Agent Navigation**:

```python
# Agents use directory structure to understand workflow phase
def get_architectural_decisions() -> list[Path]:
    """Get all ADRs."""
    return list(Path("docs/decisions").glob("[0-9]*.md"))

def get_active_plans() -> list[Path]:
    """Get current implementation plans."""
    planning = Path("docs/planning")
    return [p for p in planning.glob("*.md") if not p.name.startswith(".")]

def get_canonical_architecture() -> list[Path]:
    """Get authoritative architecture docs."""
    return list(Path("docs/architecture").glob("*.md"))
```

**Diátaxis Integration**:

While our primary organization is workflow-based, we follow Diátaxis principles within categories:

- **Tutorials** → `docs/development/` (getting started guides)
- **How-to guides** → `docs/operations/` (task-oriented)
- **Reference** → `docs/architecture/` + `docs/schemas/` (information-oriented)
- **Explanation** → `docs/decisions/` + `docs/knowledge/` (understanding-oriented)

## Review History

- 2025-11-16 - Initial decision (formalizing existing layout)
