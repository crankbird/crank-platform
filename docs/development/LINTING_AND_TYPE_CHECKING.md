# Linting and Type Checking Guide

This guide documents common linting and type checking patterns for the Crank Platform codebase.

## Tools Used

- **Pylance**: VS Code's Python language server (strict mode)
- **Mypy**: Static type checker
- **Ruff**: Fast Python linter (replaces flake8, isort, etc.)
- **markdownlint**: Markdown formatting rules

## Common Patterns and Solutions

### 1. FastAPI Route Handlers

**Problem**: Pylance flags nested route handlers as "not accessed" when using decorators.

```python
# ❌ Avoid - Pylance can't see decorator usage
@self.app.get("/health")
async def health_check() -> JSONResponse:
    return JSONResponse(...)
```

**Solution**: Use explicit binding after function definition:

```python
# ✅ Correct - Explicit binding makes usage visible
async def health_check() -> JSONResponse:
    return JSONResponse(...)

self.app.get("/health")(health_check)
```

**Why**: Decorators create an indirect reference that static analysis tools can't easily track. Explicit binding gives the language server a concrete usage site.

### 2. Optional Hooks in Abstract Base Classes

**Problem**: Ruff B027 flags empty methods in abstract classes without `@abstractmethod`.

```python
# ❌ Avoid - Ruff sees this as missing implementation
class Base(abc.ABC):
    async def on_startup(self) -> None:
        """Optional startup hook."""
```

**Solution**: Add explicit `return None` for optional hooks:

```python
# ✅ Correct - Explicit return satisfies linter
class Base(abc.ABC):
    async def on_startup(self) -> None:
        """Optional startup hook."""
        return None
```

**Why**: Empty methods without `@abstractmethod` look like incomplete implementations. Explicit return signals intentional no-op behavior.

### 3. Enum String Comparisons

**Problem**: Comparing enum members directly to strings fails type checking.

```python
# ❌ Avoid - Type mismatch
from enum import Enum

class Status(str, Enum):
    HEALTHY = "healthy"

assert Status.HEALTHY == "healthy"  # Type error
```

**Solution**: Use `.value` to access the string representation:

```python
# ✅ Correct - Compare enum value
assert Status.HEALTHY.value == "healthy"
```

**Why**: Enum members are not the same type as their values. `.value` extracts the underlying string for comparison.

### 4. Type Narrowing After Assertions

**Problem**: Pylance narrows types after assertions, causing false "non-overlapping" errors on subsequent checks.

```python
# ❌ Avoid - Type narrowed to literal after first assert
manager.set_status(HealthStatus.HEALTHY)
assert manager.status == HealthStatus.HEALTHY  # Type narrows to Literal[HEALTHY]

manager.set_status(HealthStatus.STOPPING)
assert manager.status == HealthStatus.STOPPING  # ❌ Always-false comparison
```

**Solution**: Re-fetch value with explicit type annotation to widen type:

```python
# ✅ Correct - Re-fetch with type annotation
manager.set_status(HealthStatus.HEALTHY)
assert manager.status == HealthStatus.HEALTHY

manager.set_status(HealthStatus.STOPPING)
current_status: HealthStatus = manager.status  # Widen type
assert current_status == HealthStatus.STOPPING
```

**Alternative**: Import alias can also widen type:

```python
from module import HealthStatus as HS
current_status: HS = manager.status
```

**Why**: After `assert x == A`, Pylance assumes `x` is always `A` for the rest of the scope. Re-fetching with explicit type annotation tells the type checker to consider all possible enum values again.

### 5. Optional Types Require Null Checks

**Problem**: Accessing attributes on `Optional[T]` without guards fails type checking.

```python
# ❌ Avoid - Task might be None
task: Optional[asyncio.Task] = get_task()
assert task.done()  # Type error: None has no attribute 'done'
```

**Solution**: Add explicit null checks before attribute access:

```python
# ✅ Correct - Null check first
task: Optional[asyncio.Task] = get_task()
assert task is not None  # Narrows type to Task
assert task.done()  # Safe to access
```

**Why**: Type checkers track control flow. After `assert x is not None`, the type narrows from `Optional[T]` to `T`.

### 6. Callable Type Annotations

**Problem**: Generic `Callable` without parameters triggers "missing type parameters" warnings.

```python
# ❌ Avoid - Missing type parameters
from collections.abc import Callable

callbacks: list[Callable] = []  # Type error
```

**Solution**: Use type aliases with full parameter specification:

```python
# ✅ Correct - Type alias with parameters
from collections.abc import Awaitable, Callable

# Supports both sync and async callbacks
ShutdownCallback = Callable[[], None] | Callable[[], Awaitable[None]]
callbacks: list[ShutdownCallback] = []
```

**Alternative**: If all callbacks are sync:

```python
callbacks: list[Callable[[], None]] = []
```

**Why**: `Callable` is a generic type that requires parameter and return type specification. Type aliases make complex signatures reusable and readable.

### 7. FastAPI Lifespan (Modern Pattern)

**Problem**: `@app.on_event()` is deprecated in FastAPI 0.109+.

```python
# ❌ Avoid - Deprecated
@app.on_event("startup")
async def startup():
    await initialize()

@app.on_event("shutdown")
async def shutdown():
    await cleanup()
```

**Solution**: Use `lifespan` context manager:

```python
# ✅ Correct - Lifespan context manager
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup phase
    await initialize()

    yield  # Application runs here

    # Shutdown phase
    await cleanup()

app = FastAPI(lifespan=lifespan)
```

**Why**: Lifespan provides better error handling, clearer control flow, and follows modern async context manager patterns. Deprecation warnings can become errors in future FastAPI versions.

## Markdown Formatting

### Fenced Code Blocks Must Specify Language

**Problem**: Bare code fences trigger MD040 linter warning.

````markdown
❌ Avoid - No language specified
```
worker_runtime/
├── __init__.py
└── base.py
```
````

**Solution**: Always specify a language tag:

````markdown
✅ Correct - Language specified
```text
worker_runtime/
├── __init__.py
└── base.py
```
````

**Common language tags**:

- `python`, `bash`, `zsh`, `json`, `yaml`, `toml`
- `dockerfile`, `sql`, `text`, `markdown`
- Use `text` for plain output, diagrams, or tree structures

## Running Linters

```bash
# Run all linters
ruff check .
mypy src/
markdownlint '**/*.md'

# Auto-fix what's possible
ruff check --fix .
markdownlint --fix '**/*.md'

# VS Code integration (automatic)
# - Pylance runs continuously in editor
# - Ruff runs on save (if configured)
# - markdownlint highlights issues inline
```

## Configuration Files

- `.vscode/settings.json` - Pylance strictness, Ruff integration
- `pyproject.toml` - Ruff rules, Mypy settings
- `.markdownlint.json` - Markdown formatting rules

## When to Suppress Warnings

**Legitimate suppressions**:

- Framework decorators that tools can't trace (use `# type: ignore[misc]` sparingly)
- Generated code or third-party stubs

**Never suppress**:

- Type safety violations (fix the types instead)
- Missing return types (add them)
- Unused imports (remove them)
- Deprecated APIs (migrate to modern alternatives)

## References

- [Pylance Settings](https://github.com/microsoft/pylance-release/blob/main/SETTINGS.md)
- [Ruff Rules](https://docs.astral.sh/ruff/rules/)
- [Mypy Type System](https://mypy.readthedocs.io/en/stable/type_inference_and_annotations.html)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
