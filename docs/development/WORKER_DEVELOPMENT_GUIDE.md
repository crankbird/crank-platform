# Worker Development Guide

## 📋 Overview

This guide provides proven patterns for creating new workers in the Crank Platform's controller/worker architecture. Based on lessons learned from the philosophical analyzer integration (Nov 2025), this approach minimizes type errors, linting issues, and integration friction.

## 🎯 Core Principles

1. **Schema-First Development**: Define all types and interfaces before implementation
2. **Contract-Driven Design**: Implement abstract methods completely before testing
3. **Incremental Integration**: Test each layer in isolation before combining
4. **Type Safety First**: Never ignore linting - it reveals architectural issues

## 🚀 Development Phases

### Phase A: Schema Definition (Type-Safe Foundation)

**Before writing any business logic**, define all data structures with complete type annotations.

```python
# 1. Create Pydantic models with explicit types
class WorkerRequest(BaseModel):
    text: str = Field(description="Input text to process")
    options: dict[str, Any] = Field(default_factory=dict, description="Processing options")

class WorkerResponse(BaseModel):
    result: str = Field(description="Processed output")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")

# 2. Define capability schema
WORKER_CAPABILITY = CapabilityDefinition(
    name="Example Worker",
    description="Processes text and returns analysis",
    input_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "options": {"type": "object"}
        },
        "required": ["text"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "result": {"type": "string"},
            "metadata": {"type": "object"},
            "confidence": {"type": "number"}
        },
        "required": ["result", "confidence"]
    }
)
```

**✅ Validation Steps:**

- All Pydantic models validate correctly
- Type checker passes on schema definitions
- JSON schema matches Pydantic structure

### Phase B: Business Logic (Isolated Testing)

Create core processing logic independent of web framework.

```python
class ExampleEngine:
    """Core business logic - no FastAPI dependencies."""

    def __init__(self) -> None:
        # Initialize any required resources
        self._initialize_resources()

    def process_text(self, text: str, options: dict[str, Any] | None = None) -> WorkerResponse:
        """
        Main processing function.

        Returns:
            WorkerResponse with results and metadata
        """
        # Implementation here
        return WorkerResponse(
            result=processed_text,
            metadata={"processing_time": elapsed},
            confidence=confidence_score
        )

    def _initialize_resources(self) -> None:
        """Load any required models, configs, etc."""
        pass
```

**✅ Validation Steps:**

- Unit tests for core logic pass
- No web framework dependencies in engine
- All edge cases handled with proper error messages

### Phase C: Worker Runtime Integration

Implement the WorkerApplication contract completely.

```python
from crank.capabilities.schema import CapabilityDefinition
from crank.worker_runtime.base import WorkerApplication

class ExampleWorker(WorkerApplication):
    """Worker providing example text processing capabilities."""

    def __init__(self, worker_id: str | None = None) -> None:
        """
        Initialize worker with proper WorkerApplication constructor.

        Args:
            worker_id: Optional unique identifier for this worker instance
        """
        super().__init__(worker_id=worker_id)
        self.engine = ExampleEngine()
        logger.info("Example worker initialized")

    def get_capabilities(self) -> list[CapabilityDefinition]:
        """Return capabilities this worker provides."""
        return [WORKER_CAPABILITY]

    def setup_routes(self) -> None:
        """Register FastAPI routes for business logic."""

        # Use explicit binding to avoid Pylance "not accessed" warnings
        async def process_endpoint(request: WorkerRequest) -> JSONResponse:
            """Main processing endpoint matching capability contract."""
            try:
                result = self.engine.process_text(
                    text=request.text,
                    options=request.options
                )
                return JSONResponse(content=result.model_dump())

            except ValueError as e:
                logger.warning(f"Invalid request: {e}")
                raise HTTPException(status_code=400, detail=str(e)) from e
            except Exception as e:
                logger.exception("Processing failed")
                raise HTTPException(status_code=500, detail="PROCESSING_FAILED") from e

        # Register route with explicit binding
        self.app.post("/process")(process_endpoint)
```

**✅ Validation Steps:**

- Worker instantiates without errors
- All abstract methods implemented
- Capabilities list returns expected values
- Routes register correctly

### Phase D: End-to-End Integration

Test complete request/response cycle.

```python
# Integration test example
async def test_worker_integration():
    worker = ExampleWorker(worker_id="test-worker")

    # Test capability registration
    capabilities = worker.get_capabilities()
    assert len(capabilities) == 1
    assert capabilities[0].name == "Example Worker"

    # Test route setup
    worker.setup_routes()

    # Test actual processing (requires test client)
    # This validates the complete request → response cycle
```

## 🧱 Common Patterns & Solutions

### Import Resolution Strategy

**❌ Problematic Approach:**

```python
from some.module import get_data  # Function name mismatch
from other import SomeType        # Missing from __init__.py
```

**✅ Correct Approach:**

```python
# 1. Design import structure first
# src/crank/my_module/__init__.py
from .core import MyEngine, MyRequest, MyResponse
from .capability import MY_CAPABILITY

__all__ = ["MyEngine", "MyRequest", "MyResponse", "MY_CAPABILITY"]

# 2. Use consistent naming
from crank.my_module import MyEngine, MY_CAPABILITY  # Names match exactly
```

### Type-Safe JSON Processing

**❌ Problematic Approach:**

```python
def load_config() -> dict:  # Too generic
    data = json.load(f)     # Type information lost
    return data
```

**✅ Correct Approach:**

```python
def _expect_string(value: Any, label: str) -> str:
    """Type-safe string extraction with clear error messages."""
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    return value

def load_config() -> MyConfigModel:
    """Load configuration with full type safety."""
    with open(config_path) as f:
        raw_data: dict[str, Any] = json.load(f)

    return MyConfigModel(
        name=_expect_string(raw_data.get("name"), "config.name"),
        # ... explicit validation for every field
    )
```

### Exception Handling in FastAPI Routes

**✅ Correct Pattern:**

```python
async def endpoint(request: MyRequest) -> JSONResponse:
    try:
        result = self.engine.process(request.data)
        return JSONResponse(content=result.model_dump())

    except ValueError as e:
        # Client errors - invalid input
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        # Server errors - unexpected failures
        logger.exception("Processing failed")
        raise HTTPException(status_code=500, detail="PROCESSING_FAILED") from e
```

## 📋 Pre-Integration Checklist

### Before Writing Code

- [ ] Read worker runtime base class contract (`src/crank/worker_runtime/base.py`)
- [ ] Define all Pydantic models with complete type annotations
- [ ] Create capability definition with matching input/output schemas
- [ ] Set up module structure with proper `__init__.py` exports

### During Implementation

- [ ] Test each component in isolation (engine → worker → integration)
- [ ] Run type checker after each major change (`mypy src/`)
- [ ] Verify import resolution works in multiple contexts
- [ ] Test error handling paths with invalid inputs

### Before Pull Request

- [ ] All abstract methods implemented completely
- [ ] Type checker passes with zero errors
- [ ] All imports resolve cleanly
- [ ] Basic unit tests pass for all components
- [ ] Integration test validates complete request cycle

## 🎯 Quality Gates

**Phase A Complete:** Schema definition passes type checking
**Phase B Complete:** Business logic works with test data
**Phase C Complete:** Worker integrates with runtime framework
**Phase D Complete:** End-to-end request/response cycle works

Each phase must be **fully validated** before proceeding to the next.

## 📚 Reference Implementation

See `services/crank_hello_world.py` for a complete reference implementation following these patterns.

## 🚨 Common Pitfalls

1. **Type Annotation Laziness**: Using `dict` instead of `dict[str, Any]` loses type information
2. **Import Name Mismatches**: Function names don't match between modules
3. **Missing Abstract Methods**: Forgetting to implement required WorkerApplication methods
4. **Generic Exception Handling**: Not distinguishing client vs server errors
5. **Skip Type Checking**: Ignoring linting errors instead of fixing root cause

**Remember**: Linting errors reveal architectural issues, not cosmetic problems. Fix them, don't ignore them.
