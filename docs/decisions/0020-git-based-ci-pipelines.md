# ADR-0020: Git-Based CI Pipelines as Single Source of Automation

**Status**: Accepted
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Developer Experience & CI/CD](../planning/adr-backlog-2025-11-16.md#developer-experience--ci-cd)

## Context and Problem Statement

Automation (builds, tests, deployments) can be defined in CI/CD platforms (GitHub Actions, Jenkins, CircleCI) or in repository scripts (Makefiles, shell scripts). Duplication leads to drift. How should we define and execute automation?

## Decision Drivers

- Single source of truth: No duplicate definitions
- Portability: Works locally and in CI
- Version control: Automation versioned with code
- Visibility: Easy to see what automation exists
- Debugging: Can run locally
- Platform flexibility: Not locked to one CI vendor

## Considered Options

- **Option 1**: Git-based pipelines (CI YAML invokes repo scripts) - Accepted
- **Option 2**: Platform-specific CI definitions
- **Option 3**: External CI/CD orchestrator

## Decision Outcome

**Chosen option**: "Git-based pipelines", because automation definitions live in the repository as scripts/Makefiles, and CI platforms simply invoke them. This provides portability, local execution, and version control while avoiding vendor lock-in.

### Positive Consequences

- Automation versioned with code
- Runs identically locally and in CI
- No CI vendor lock-in
- Easy debugging (run scripts locally)
- Visible in repository
- Portable across CI platforms

### Negative Consequences

- CI YAML still needed (though minimal)
- Scripts must handle environment differences
- Less leverage of CI platform features
- Manual secret management

## Pros and Cons of the Options

### Option 1: Git-Based Pipelines (CI Invokes Scripts)

Repository contains Makefiles/scripts, CI just runs them.

**Pros:**
- Single source of truth
- Portable
- Version controlled
- Local execution
- Easy debugging
- Platform-agnostic

**Cons:**
- Still need CI YAML
- Environment handling
- Less platform features
- Secret management

### Option 2: Platform-Specific CI Definitions

Define automation in CI platform (GitHub Actions, Jenkins).

**Pros:**
- Rich platform features
- Integrated secrets
- Native UI
- Matrix builds

**Cons:**
- Vendor lock-in
- Hard to run locally
- Not version controlled same way
- Duplication if multi-platform

### Option 3: External CI/CD Orchestrator

Dedicated tool (Tekton, Argo Workflows).

**Pros:**
- Powerful orchestration
- Kubernetes-native
- Complex workflows

**Cons:**
- Additional infrastructure
- Learning curve
- Overkill for most tasks
- Still need repo integration

## Links

- [Related to] ADR-0021 (Local dev environments)
- [Implements] `Makefile` (worker management)
- [Implements] `scripts/dev-universal.sh` (development setup)
- [Related to] `.github/workflows/` (GitHub Actions)

## Implementation Notes

**Pattern**: Repository scripts are the source of truth, CI invokes them.

**Makefile** (Primary Interface):

```makefile
# Makefile - Single source of automation truth

.PHONY: test
test:  ## Run all tests
 uv run pytest

.PHONY: lint
lint:  ## Run linters
 uv run ruff check src/
 uv run mypy src/

.PHONY: format
format:  ## Format code
 uv run ruff format src/

.PHONY: worker-build
worker-build:  ## Build worker container
 @if [ -z "$(WORKER)" ]; then \
  echo "Usage: make worker-build WORKER=<name>"; \
  exit 1; \
 fi
 docker build -f workers/$(WORKER)/Dockerfile \
  -t crank-$(WORKER):latest .

.PHONY: worker-run
worker-run:  ## Run worker natively
 @if [ -z "$(WORKER)" ]; then \
  echo "Usage: make worker-run WORKER=<name>"; \
  exit 1; \
 fi
 python -m services.crank_$(WORKER)

.PHONY: setup
setup:  ## Setup development environment
 ./scripts/dev-universal.sh setup

.PHONY: help
help:  ## Show this help
 @grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
  awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
```

**GitHub Actions** (Minimal - Invokes Makefile):

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install UV
        run: pip install uv

      - name: Setup Environment
        run: make setup

      - name: Run Tests
        run: make test

      - name: Run Linters
        run: make lint

  docker:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        worker: [streaming, document_conversion, email_classifier]
    steps:
      - uses: actions/checkout@v4

      - name: Build Worker
        run: make worker-build WORKER=${{ matrix.worker }}
```

**Development Scripts** (Complex Setup):

```bash
#!/usr/bin/env bash
# scripts/dev-universal.sh - Universal development setup

set -euo pipefail

setup() {
    echo "Setting up development environment..."

    # Install UV
    if ! command -v uv &> /dev/null; then
        pip install uv
    fi

    # Sync dependencies
    uv sync --all-extras

    # Install in editable mode
    uv pip install -e .

    # Initialize certificates
    python scripts/initialize-certificates.py

    echo "Setup complete!"
}

case "${1:-}" in
    setup) setup ;;
    *) echo "Usage: $0 {setup}"; exit 1 ;;
esac
```

**Local Execution**:

```bash
# Developer runs locally (same as CI)
make test
make lint
make worker-build WORKER=streaming

# CI runs same commands
# .github/workflows/test.yml: run: make test
```

**Benefits**:

1. **Portability**: Works on macOS, Linux, Windows (WSL), CI
2. **Debugging**: Run exact CI commands locally
3. **Version Control**: Automation changes reviewed in PRs
4. **Visibility**: `make help` shows all automation
5. **Flexibility**: Switch CI platforms (GitHub → GitLab) easily

**Anti-Pattern** (Avoid):

```yaml
# ❌ BAD: Automation defined in CI platform
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install pytest ruff mypy
      - run: pytest
      - run: ruff check src/
      - run: mypy src/

# Problem: Can't run this locally, hard to debug, vendor lock-in
```

**Good Pattern**:

```yaml
# ✅ GOOD: CI invokes repository scripts
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make setup  # Setup from Makefile
      - run: make test   # Test from Makefile
      - run: make lint   # Lint from Makefile

# Benefit: `make test` works locally and in CI
```

## Review History

- 2025-11-16 - Initial decision (formalizing existing Makefile pattern)
