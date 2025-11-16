# Testing Guide

Complete guide to setting up and running tests in the Crank Platform.

## Environment Setup (Critical)

**The test environment requires specific setup to resolve imports correctly.** This is not optional - tests will fail with import errors if skipped.

### Required Setup Steps

```bash
# 1. Create/activate virtual environment (uv automatically manages this)
cd crank-platform

# 2. Install ALL dependencies INCLUDING dev dependencies
uv sync --all-extras

# 3. Install package in EDITABLE mode (critical for imports)
uv pip install -e .
```

### Why These Steps Are Required

**Import Resolution**: The `src/crank/` package structure requires editable installation (`-e .`) to make imports like `from crank.controller import CapabilityRegistry` work correctly in tests.

**Dev Dependencies**: Testing requires `pytest`, `pytest-asyncio`, `pytest-cov`, and other tools defined in `pyproject.toml` under `[project.optional-dependencies.dev]`.

**All Extras**: Some tests may require optional dependencies (GPU libraries, specialized tools) defined in other extras groups.

### Common Setup Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'crank'` | Package not installed in editable mode | Run `uv pip install -e .` |
| `ModuleNotFoundError: No module named 'pytest'` | Dev dependencies not installed | Run `uv sync --all-extras` |
| `ModuleNotFoundError: No module named 'pydantic'` | Core dependencies not installed | Run `uv sync` then `uv pip install -e .` |
| Tests import different Python than expected | Wrong Python interpreter | Use `uv run pytest` not `pytest` directly |

### Verifying Setup

```bash
# Verify environment has all dependencies
uv pip list | grep -E 'pytest|pydantic|crank-platform'

# Should show:
# crank-platform    0.1.0      /path/to/crank-platform  (editable)
# pydantic          2.x.x
# pytest            8.x.x
# pytest-asyncio    x.x.x
# pytest-cov        x.x.x

# Verify imports work
uv run python -c "from crank.controller import CapabilityRegistry; print('✅ Imports OK')"
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/controller/test_capability_registry.py

# Run specific test function
uv run pytest tests/unit/controller/test_capability_registry.py::test_register_worker_minimal_capability

# Run with verbose output
uv run pytest -v

# Run with very verbose output (shows test names + PASSED/FAILED)
uv run pytest -vv
```

### Test Discovery

Pytest automatically discovers tests matching these patterns:

- Files: `test_*.py` or `*_test.py`
- Functions: `test_*()` functions
- Classes: `Test*` classes
- Methods: `test_*()` methods in `Test*` classes

### Test Organization

```text
tests/
├── unit/                   # Fast isolated unit tests
│   ├── controller/         # Controller components
│   │   ├── __init__.py
│   │   └── test_capability_registry.py
│   ├── worker_runtime/     # Worker runtime base classes
│   └── capabilities/       # Capability schemas
├── integration/            # Integration tests (multiple components)
└── e2e/                    # End-to-end tests (full system)
```

**Test Scope Guidelines**:

- **Unit tests** (`tests/unit/`): Test single class/function in isolation
  - Mock external dependencies
  - Fast execution (< 1 second per test)
  - No network calls, no file I/O except temp files

- **Integration tests** (`tests/integration/`): Test multiple components together
  - Real dependencies (databases, message queues)
  - Slower execution (1-10 seconds)
  - May require Docker services running

- **E2E tests** (`tests/e2e/`): Test complete user workflows
  - Full system deployment
  - Slowest execution (10+ seconds)
  - Requires all services running

## Coverage Reports

### Generating Coverage

```bash
# Run tests with coverage
uv run pytest --cov=src --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Configuration

Coverage settings in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    "*/site-packages/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

### Coverage Goals

- **New code**: 100% coverage required
- **Existing code**: Maintain or improve current coverage
- **Critical paths**: Security, data persistence, routing - always 100%

## Writing Tests

### Test Structure (AAA Pattern)

```python
def test_something() -> None:
    """Test description following Given/When/Then pattern."""
    # ARRANGE: Set up test fixtures
    registry = CapabilityRegistry(state_file="/tmp/test.jsonl")
    capability = CapabilitySchema(name="test", verb="invoke", version="1.0")

    # ACT: Execute the behavior under test
    registry.register("worker1", "https://localhost:8500", [capability])

    # ASSERT: Verify expected outcomes
    result = registry.route("invoke", "test")
    assert result is not None
    assert result["worker_id"] == "worker1"
```

### Required Patterns

**1. Type Annotations on All Test Functions**

```python
# ✅ Correct - return type required
def test_register_worker() -> None:
    assert True

# ❌ Wrong - type checker will complain
def test_register_worker():
    assert True
```

**2. Async Tests**

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation() -> None:
    result = await some_async_function()
    assert result is not None
```

**3. Fixtures for Shared Setup**

```python
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_state_file() -> Path:
    """Provide temporary state file for registry tests."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
        return Path(f.name)

def test_uses_fixture(temp_state_file: Path) -> None:
    assert temp_state_file.exists()
```

**4. Parametrized Tests**

```python
import pytest

@pytest.mark.parametrize("verb,capability,expected", [
    ("invoke", "email.classify", True),
    ("invoke", "missing.capability", False),
    ("query", "email.classify", False),
])
def test_routing(verb: str, capability: str, expected: bool) -> None:
    # Setup registry with email.classify capability
    # Test routing with parameters
    pass
```

### Common Testing Anti-Patterns

**❌ Don't use mutable default arguments**:

```python
# Wrong
def test_registry(capabilities=[]) -> None:  # ❌ Mutable default
    capabilities.append(...)

# Correct
def test_registry() -> None:
    capabilities: list[CapabilitySchema] = []  # ✅ Local variable
    capabilities.append(...)
```

**❌ Don't skip cleanup**:

```python
# Wrong
def test_with_file() -> None:
    f = open("/tmp/test.txt", "w")
    f.write("test")
    # ❌ File left open, not deleted

# Correct - use context managers
def test_with_file() -> None:
    with tempfile.NamedTemporaryFile(mode="w", delete=True) as f:
        f.write("test")
        # ✅ Automatically cleaned up
```

**❌ Don't test implementation details**:

```python
# Wrong - tests internal structure
def test_registry() -> None:
    registry = CapabilityRegistry()
    assert len(registry._workers) == 0  # ❌ Testing private attribute

# Correct - tests public behavior
def test_registry() -> None:
    registry = CapabilityRegistry()
    workers = registry.get_all_workers()
    assert len(workers) == 0  # ✅ Testing public API
```

## Logging in Tests

### Correct Logging Pattern

Python's standard `logging` module **does NOT support keyword arguments**. Use formatted strings:

```python
import logging

logger = logging.getLogger(__name__)

# ✅ Correct - formatted string arguments
logger.info("Worker registered: %s with %d capabilities", worker_id, len(capabilities))
logger.error("Failed to load state: %s", str(error))
logger.debug("Routing request: verb=%s capability=%s", verb, capability_name)

# ❌ Wrong - keyword arguments not supported
logger.info("Worker registered", worker_id=worker_id)  # TypeError!
logger.error("Failed", error=str(e))  # TypeError!
```

### Logging Levels

- **DEBUG**: Detailed diagnostic information (routing decisions, state changes)
- **INFO**: General informational messages (registration, heartbeats)
- **WARNING**: Unexpected but handled conditions (stale workers, unknown heartbeats)
- **ERROR**: Error conditions that prevent operation (state load failure)
- **CRITICAL**: System-level failures (controller crash)

### Testing Logging Output

```python
import logging
import pytest

def test_logs_registration(caplog: pytest.LogCaptureFixture) -> None:
    """Verify registration logs correct message."""
    with caplog.at_level(logging.INFO):
        registry = CapabilityRegistry()
        registry.register("worker1", "https://localhost:8500", [capability])

    assert "Worker registered: worker1" in caplog.text
```

## Debugging Tests

### Running Single Test with Debug Output

```bash
# Show print statements and logging
uv run pytest -s tests/unit/controller/test_capability_registry.py::test_register_worker

# Show full tracebacks on errors
uv run pytest --tb=long

# Drop into debugger on failure
uv run pytest --pdb
```

### Using VS Code Debugger

1. Set breakpoint in test file (click left of line number)
2. Open test file in editor
3. Click "Debug Test" code lens above test function
4. Or use Testing sidebar → right-click test → "Debug Test"

### Common Test Failures

| Failure | Likely Cause | Fix |
|---------|--------------|-----|
| `TypeError: Logger._log() got unexpected keyword` | Using keyword args in logger calls | Use `logger.info("msg %s", value)` not `logger.info("msg", value=value)` |
| `AssertionError: assert None is not None` | Function returned None instead of expected value | Check function logic, ensure return statement exists |
| `FileNotFoundError` in state load | Test didn't create expected file | Use `tempfile.NamedTemporaryFile()` or check file creation logic |
| `pydantic.ValidationError` | Invalid data passed to Pydantic model | Check required fields, use `model.model_validate()` for debugging |

## Continuous Integration

Tests run automatically on:

- **Pull Request**: All tests must pass before merge
- **Main branch push**: Full test suite + coverage report
- **Nightly**: Extended integration tests + performance benchmarks

### CI Configuration

See `.github/workflows/test.yml` for CI pipeline configuration.

**Local pre-commit checks**:

```bash
# Run what CI will run
uv run pytest --cov=src --cov-report=term
uv run mypy src/
uv run ruff check .
```

## Performance Testing

### Benchmarking Tests

```python
import pytest
import time

def test_routing_performance() -> None:
    """Verify routing completes in < 10ms."""
    registry = CapabilityRegistry()
    # ... setup workers ...

    start = time.perf_counter()
    result = registry.route("invoke", "test")
    elapsed = time.perf_counter() - start

    assert result is not None
    assert elapsed < 0.01  # 10ms threshold
```

### Load Testing

```python
import pytest

@pytest.mark.slow  # Mark for optional execution
def test_registry_handles_1000_workers() -> None:
    """Verify registry scales to 1000 workers."""
    registry = CapabilityRegistry()

    for i in range(1000):
        registry.register(f"worker{i}", f"https://localhost:{8500+i}", [capability])

    # Verify routing still fast
    start = time.perf_counter()
    result = registry.route("invoke", "test")
    elapsed = time.perf_counter() - start

    assert elapsed < 0.1  # 100ms with 1000 workers
```

Run slow tests explicitly:

```bash
uv run pytest -m slow  # Only slow tests
uv run pytest -m "not slow"  # Skip slow tests
```

## Test Data Management

### Using Fixtures for Test Data

```python
@pytest.fixture
def sample_capability() -> CapabilitySchema:
    """Minimal valid capability for testing."""
    return CapabilitySchema(
        name="test.capability",
        verb="invoke",
        version="1.0.0",
    )

@pytest.fixture
def extended_capability() -> CapabilitySchema:
    """Fully-populated capability with all optional fields."""
    return CapabilitySchema(
        name="advanced.capability",
        verb="invoke",
        version="2.0.0",
        runtime="python3.11",
        env_profile="gpu-required",
        constraints={"min_memory_mb": 4096},
        slo={"p99_latency_ms": 100},
    )
```

### Test Data Files

For complex test data (JSON fixtures, sample files):

```text
tests/
├── fixtures/
│   ├── sample_email.json
│   ├── worker_state.jsonl
│   └── capabilities/
│       ├── minimal.json
│       └── extended.json
```

Load in tests:

```python
from pathlib import Path
import json

def test_with_fixture_file() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "sample_email.json"
    with open(fixture_path) as f:
        data = json.load(f)
    # ... test with data ...
```

## Mascot Testing

Specialized testing with AI personas (see [Mascot README](../../mascots/README.md)):

```bash
# Security testing
uv run python scripts/run_mascot_tests.py --mascot wendy --target src/crank/controller/

# Portability testing
uv run python scripts/run_mascot_tests.py --mascot kevin --target src/crank/controller/

# Full council review
uv run python scripts/run_mascot_tests.py --council --target src/
```

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [Linting and Type Checking Guide](LINTING_AND_TYPE_CHECKING.md)

## Quick Reference

```bash
# Setup (one time)
uv sync --all-extras && uv pip install -e .

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test
uv run pytest tests/unit/controller/test_capability_registry.py -v

# Debug single test
uv run pytest -s --pdb tests/unit/controller/test_capability_registry.py::test_name

# Verify environment
uv pip list | grep -E 'pytest|crank'
```
