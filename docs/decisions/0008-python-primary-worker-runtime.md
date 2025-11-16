# ADR-0008: Standardise on Python as Primary Worker Runtime

**Status**: Accepted
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Core Platform & Agent Architecture](../planning/adr-backlog-2025-11-16.md#core-platform--agent-architecture)

## Context and Problem Statement

Workers need to integrate with ML libraries (PyTorch, Transformers, YOLO), data processing tools (Pandas, NumPy), and document libraries (Pandoc, BeautifulSoup). We need to standardize on a primary runtime language for worker development to maximize library availability and developer productivity.

## Decision Drivers

- ML ecosystem: PyTorch, Transformers, scikit-learn are Python-native
- Library availability: Richest ecosystem for AI/ML
- Developer familiarity: Most AI developers know Python
- Prototyping speed: Fast iteration for agent development
- Type safety: Modern Python (3.9+) has strong typing
- Performance: Good enough for most workloads, can call native code

## Considered Options

- **Option 1**: Python as primary runtime (chosen)
- **Option 2**: Polyglot (any language)
- **Option 3**: Rust for performance-critical workers

## Decision Outcome

**Chosen option**: "Python as primary runtime", because it provides the best balance of ML library availability, developer productivity, and ecosystem maturity for AI-focused workers.

### Positive Consequences

- Access to entire ML/AI ecosystem (PyTorch, Transformers, etc.)
- Fast development iteration
- Large talent pool
- Rich tooling (pytest, mypy, ruff)
- Type safety with modern Python (3.9+)
- Easy integration with Jupyter for prototyping

### Negative Consequences

- Performance limitations for CPU-intensive tasks
- GIL limits true parallelism
- Memory overhead vs compiled languages
- Deployment size (Docker images larger)
- Slower startup than compiled languages

## Pros and Cons of the Options

### Option 1: Python as Primary Runtime

All workers written in Python 3.9+.

**Pros:**
- ML library ecosystem
- Fast development
- Type safety (mypy)
- Developer availability
- Prototyping speed
- Jupyter integration

**Cons:**
- Performance overhead
- GIL limitations
- Memory usage
- Deployment size

### Option 2: Polyglot (Any Language)

Workers can use any language with HTTP interface.

**Pros:**
- Choose best language per use case
- Performance optimization possible
- Flexibility

**Cons:**
- Fragmented tooling
- Harder to maintain
- Multiple build systems
- Inconsistent patterns
- Knowledge silos

### Option 3: Rust for Performance-Critical Workers

Use Rust for high-performance workers.

**Pros:**
- Excellent performance
- Memory safety
- No GIL
- Small binaries

**Cons:**
- Limited ML library ecosystem
- Steeper learning curve
- Slower development
- FFI complexity for Python ML libs
- Smaller talent pool

## Links

- [Related to] ADR-0001 (Controller/Worker model allows runtime choice per worker)
- [Related to] Existing worker implementations (all Python)
- [Refined by] Workers can use Rust extensions via PyO3 if needed

## Implementation Notes

**Python Version**: 3.9+ (modern type hints, performance improvements)

**Type Safety**:
- All workers use mypy strict mode
- Type annotations required (return `-> None` for tests)
- Pydantic for data validation

**Standard Libraries**:

```toml
[project.dependencies]
# Core framework
fastapi = ">=0.104.0"
uvicorn = ">=0.24.0"
pydantic = ">=2.5.0"
httpx = ">=0.25.0"

# ML/AI (optional, per worker)
torch = ">=2.1.0"          # GPU workers
transformers = ">=4.35.0"   # NLP workers
opencv-python = ">=4.8.0"   # Vision workers
```

**Performance Optimization**:
- Use NumPy/Pandas for data operations (native code)
- PyTorch/TensorFlow call native CUDA libraries
- Critical paths can use Cython/PyO3 extensions
- Async I/O for network operations

**Existing Implementation**:
- All 9 workers currently Python
- Proven pattern with `WorkerApplication` base class
- 40.4% code reduction achieved with Python patterns

## Review History

- 2025-11-16 - Initial decision (formalizing existing practice)
