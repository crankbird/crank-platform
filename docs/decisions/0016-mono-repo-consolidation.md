# ADR-0016: Consolidate Projects into Mono-Repo for Crankbird

**Status**: Proposed
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Documentation, Knowledge & Repo Structure](../planning/adr-backlog-2025-11-16.md#documentation-knowledge--repo-structure)

## Context and Problem Statement

Crankbird ecosystem includes multiple related projects (Crank-Platform, Agent13/Agent14, Docforge, Brand-Science tooling) with shared code, dependencies, and architectural patterns. Should we maintain separate repositories or consolidate into a mono-repo?

## Decision Drivers

- Code sharing: Reduce duplication across projects
- Atomic changes: Change multiple projects together
- Dependency management: Unified version control
- Discoverability: Easy to find related code
- CI/CD: Simplified pipeline configuration
- Team velocity: Faster cross-project refactoring

## Considered Options

- **Option 1**: Mono-repo with workspaces - Proposed
- **Option 2**: Multi-repo with shared libraries
- **Option 3**: Keep current separate repositories

## Decision Outcome

**Chosen option**: "Mono-repo with workspaces", because it enables atomic cross-project changes, reduces code duplication, and improves team velocity while maintaining logical separation.

### Positive Consequences

- Atomic cross-project changes
- Shared code easily reused
- Single CI/CD configuration
- Unified dependency versions
- Better code discoverability
- Simplified local development

### Negative Consequences

- Larger repository size
- More complex CI (need selective builds)
- Requires mono-repo tooling
- All-or-nothing access control
- Build time optimization needed

## Pros and Cons of the Options

### Option 1: Mono-Repo with Workspaces

Single repository with project subdirectories.

**Pros:**
- Atomic changes
- Code sharing
- Single CI/CD
- Unified versions
- Easy refactoring

**Cons:**
- Large repo
- Complex CI
- Tooling needed
- Access control

### Option 2: Multi-Repo with Shared Libraries

Separate repos, extract shared code to libraries.

**Pros:**
- Small repos
- Independent release cycles
- Fine-grained access control
- Simpler CI per repo

**Cons:**
- Cross-repo changes hard
- Library versioning overhead
- Code duplication
- Dependency hell risk

### Option 3: Keep Current Separate Repositories

Status quo.

**Pros:**
- No migration effort
- Known workflow
- Simple

**Cons:**
- Code duplication
- Cross-project changes difficult
- Inconsistent patterns
- Discovery problems

## Links

- [Related to] ADR-0019 (Documentation layout standardized across projects)
- [Enables] Shared capability registry, security modules, testing infrastructure

## Implementation Notes

**Proposed Structure**:

```
crankbird/
  README.md
  pyproject.toml           # Root workspace config

  packages/
    platform/              # Crank-Platform (controller + workers)
      pyproject.toml
      src/crank/
      services/
      tests/

    agent13/               # Agent13 (Codex-based)
      pyproject.toml
      src/agent13/

    agent14/               # Agent14 (Sonnet-based)
      pyproject.toml
      src/agent14/

    docforge/              # Document rendering pipeline
      pyproject.toml
      src/docforge/

    brand-science/         # Brand analysis tooling
      pyproject.toml
      src/brand_science/

    shared/                # Shared libraries
      capabilities/        # Capability schema
      security/            # Security modules
      testing/             # Test utilities

  docs/
    decisions/             # Cross-project ADRs
    architecture/          # System-wide architecture
    proposals/             # Strategic proposals

  .github/
    workflows/             # Unified CI/CD
```

**Python Workspace** (`pyproject.toml`):

```toml
[tool.uv.workspace]
members = [
  "packages/platform",
  "packages/agent13",
  "packages/agent14",
  "packages/docforge",
  "packages/brand-science",
  "packages/shared/*"
]
```

**Selective CI**:

```yaml
name: CI

on: [push, pull_request]

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      platform: ${{ steps.changes.outputs.platform }}
      agent13: ${{ steps.changes.outputs.agent13 }}
    steps:
      - uses: dorny/paths-filter@v2
        id: changes
        with:
          filters: |
            platform:
              - 'packages/platform/**'
              - 'packages/shared/**'
            agent13:
              - 'packages/agent13/**'
              - 'packages/shared/**'

  test-platform:
    needs: detect-changes
    if: needs.detect-changes.outputs.platform == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: pytest packages/platform/tests
```

**Migration Strategy**:
1. Create mono-repo structure
2. Migrate one project at a time
3. Extract shared code to `packages/shared/`
4. Update CI/CD pipelines
5. Archive old repositories (read-only)

## Review History

- 2025-11-16 - Initial proposal
