# Contributing to Crank Platform

**Status**: Active
**Last Updated**: 2025-11-16

## 🎯 Development Workflow

### 1. Understanding Strategic Direction

Start by reviewing the documentation hierarchy:

1. **[docs/proposals/](../docs/proposals/)** - Strategic ideas and future vision
2. **[docs/planning/](../docs/planning/)** - Active work decomposition
3. **[docs/issues/](../docs/issues/)** or [GitHub Issues](https://github.com/crankbird/crank-platform/issues) - Execution tracking
4. **[docs/operations/](../docs/operations/)** - Production procedures
5. **[docs/development/](../docs/development/)** - Coding standards

### 2. Before You Start

- Check [proposals/enhancement-roadmap.md](../docs/proposals/enhancement-roadmap.md) for strategic roadmap
- Review [planning/phase-3-controller-extraction.md](../docs/planning/phase-3-controller-extraction.md) for active refactor work
- Read [ARCHITECTURE.md](../docs/ARCHITECTURE.md) for system design principles
- Check existing GitHub issues to avoid duplicate work

### 3. Development Standards

All code must follow the patterns documented in:

- **[development/README.md](../docs/development/README.md)** - Comprehensive development guide
- **[development/CODE_QUALITY_STRATEGY.md](../docs/development/CODE_QUALITY_STRATEGY.md)** - Type safety requirements
- **[development/WORKER_DEVELOPMENT_GUIDE.md](../docs/development/WORKER_DEVELOPMENT_GUIDE.md)** - Worker patterns
- **[.vscode/AGENT_CONTEXT.md](../.vscode/AGENT_CONTEXT.md)** - AI agent coding rules
- **[.github/copilot-instructions.md](copilot-instructions.md)** - Copilot context

### 4. Setting Up Your Environment

```bash
# Clone and setup
git clone https://github.com/crankbird/crank-platform.git
cd crank-platform

# Setup development environment
./scripts/dev-universal.sh setup

# Or manual setup
uv sync --all-extras
uv pip install -e .

# Initialize certificates (required for workers)
python scripts/initialize-certificates.py

# Run tests
pytest
```

### 5. Making Changes

#### Code Changes

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Follow the established patterns (see `src/crank/worker_runtime/` for examples)
3. Add type annotations to all functions (including test functions: `def test_foo() -> None:`)
4. Run linting: `mypy src/` and `ruff check src/`
5. Add tests for new functionality
6. Ensure all tests pass: `pytest`

#### Documentation Changes

1. Update relevant documentation in `docs/`
2. Follow ALL_CAPS.md naming for canonical reference docs
3. Add status headers to all new documents:
   ```markdown
   **Status**: Active | Draft | Historical | Deprecated
   **Type**: AS-IS | TO-BE | HISTORICAL
   **Last Updated**: YYYY-MM-DD
   **Owner**: Team/Person name
   **Purpose**: One-sentence description
   ```
4. Update the appropriate directory's README if adding new categories

### 6. Submitting Changes

1. Ensure all tests pass and linting is clean
2. Update documentation to reflect your changes
3. Commit with descriptive messages following [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `refactor:` Code restructuring
   - `test:` Test additions/changes
   - `chore:` Maintenance tasks
4. Push to your fork: `git push origin feature/your-feature-name`
5. Open a Pull Request with:
   - Clear description of changes
   - Link to related issue/proposal
   - Screenshots/examples if applicable

### 7. Pull Request Review Process

- PRs require approval from project maintainers
- All CI checks must pass
- Documentation must be updated
- Tests must maintain or improve coverage

## 🔒 Security

- All workers must use the unified `crank.security` module
- Never commit certificates, keys, or secrets
- Use `.env` files (already in `.gitignore`) for local configuration
- Report security issues privately to [security contact]

## 📋 Code Standards

### Type Safety

- All functions require type annotations
- Test functions must return `-> None`
- Enum comparisons require `.value` (e.g., `status.value == "healthy"`)
- Use `from typing import *` for complex types

### Worker Development

- Subclass `WorkerApplication` from `crank.worker_runtime`
- Use `worker.run()` for automatic HTTPS+mTLS setup
- Never manually configure uvicorn SSL
- See `services/crank_hello_world.py` for reference pattern

### Testing

- Use pytest for all tests
- Use mascot testing for specialized validation:
  - `🐰 Wendy` - Security/zero-trust testing
  - `🦙 Kevin` - Portability testing
  - `🤝 Collaboration` - Multi-mascot testing
  - `🏛️ Full Council` - Complete review

## 📚 Documentation Philosophy

Documentation flows through lifecycle stages:

```
Proposal → Planning → Issue → Implementation → Operations/Development Docs → Archive
```

- **Proposals**: Ideas and strategic vision (not yet committed)
- **Planning**: Decomposed work ready for execution
- **Issues**: Active tracking with context
- **Operations**: Production runbooks (how to keep it running)
- **Development**: Coding standards (how to build it)
- **Archive**: Completed work and historical decisions

## 🤝 Questions?

- Check [docs/README.md](../docs/README.md) for navigation
- Review [docs/knowledge/](../docs/knowledge/) for cross-cutting patterns
- Look at recent commits for examples
- Ask in GitHub Issues

## 📄 License

This is proprietary software. See [LICENSE](../LICENSE) for details.

All contributions require agreement to the Contributor License Agreement (CLA) - contact project maintainers for details.
