# AI Assistant Worker Generation Best Practices

**Version**: 1.0
**Date**: November 14, 2025
**Purpose**: Guide future AI assistants in creating high-quality Crank Platform workers

## 🎯 **Executive Summary**

Through comparative analysis of Claude Sonnet vs GitHub Codex worker implementations, we've identified proven patterns that maximize worker quality while minimizing integration friction. This guide provides actionable recommendations for AI assistants working on the Crank Platform.

## 📋 **Essential Pre-Work Checklist**

Before generating any worker code:

1. **Read the architectural context**: `.vscode/AGENT_CONTEXT.md`
2. **Review the refactor phase**: Check GitHub Issues #27-#31 for current phase
3. **Study reference implementations**:
   - `services/crank_hello_world.py` (template)
   - `services/crank_philosophical_analyzer.py` (comprehensive service)
   - `services/crank_sonnet_zettel_manager.py` (CRUD operations)
4. **Follow the development guide**: `docs/development/WORKER_DEVELOPMENT_GUIDE.md`

## 🏗️ **Architecture Decision Framework**

### **Choose Sonnet Pattern (Multi-Operation) When:**

- Building comprehensive CRUD services
- Fast retrieval and complex filtering needed
- Type safety is critical requirement
- Performance matters more than memory usage
- Client needs unified API with multiple operations

### **Choose Codex Pattern (Single-Operation) When:**

- Building focused single-purpose services
- Stateless operation is preferred
- Extension hooks more important than pre-defined fields
- Simplicity preferred over performance optimization
- Service has one primary responsibility

### **Implementation Signature Patterns**

```python
# Sonnet Pattern: Multi-operation with discriminated union
class MultiOperationRequest(BaseModel):
    operation: Literal["store", "retrieve", "list"]
    # Union of operation-specific data

# Codex Pattern: Single operation with direct payload
class SingleOperationRequest(BaseModel):
    # Direct operation data only
```

### **Capability Scope Decision Matrix (Codex Insights)**

Choose capability granularity carefully:

| **Scenario** | **Pattern** | **Reasoning** |
|--------------|-------------|---------------|
| Single workflow (e.g., ingestion only) | Separate capability per workflow | Controller can route independently |
| Related operations (CRUD suite) | Multi-operation capability | Operations naturally compose |
| Independent concerns | Multiple capabilities | Enables composition over bloat |

**Example**: `ZETTEL_INGEST` + `ZETTEL_SEARCH` capabilities can be composed by controller vs single `ZETTEL_MANAGEMENT` handling everything.

### **Extension Strategy Patterns**

**Schema Fields (Planned Features)**:

```python
class ZettelMetadata(BaseModel):
    auto_generated_title: bool = Field(default=False)  # Type-safe, known structure
    similarity_cluster: str | None = Field(default=None)
```

**Method Hooks (Experimental Features)**:

```python
def _generate_title(self, record: ZettelRecord) -> str:
    """Extension hook for auto-title generation."""
    # Override for custom behavior

def _resolve_category(self, record: ZettelRecord) -> str:
    """Extension hook for categorization strategies."""
```

**Guidance**: Use schema fields for planned data, method hooks for experimental behaviors.

### **Metadata Format Selection (Codex Insights)**

**JSON Front Matter** (machine-friendly):

```yaml
---
{
  "category": "inbox",
  "created_at": "2025-11-14T10:01:16.123456",
  "zettel_id": "zk20251114101016"
}
---
```

**YAML Front Matter** (human-readable):

```yaml
---
id: sonnet-20251114-100116-5e720bd3
title: Test Zettel
created_at: 2025-11-14T10:01:16.190126
---
```

**Selection Criteria**:

- **JSON**: Pipeline-heavy contexts, automated processing, strict parsing
- **YAML**: Human-facing workflows, manual editing, readability

### **Route Binding Standards**

Use explicit route binding to avoid decorator lint issues:

```python
def setup_routes(self):
    """Configure FastAPI routes explicitly"""

    @app.post("/process")
    async def process_endpoint(request: ProcessRequest) -> ProcessResponse:
        # Route handler implementation
        ...

    # Explicit binding (preferred)
    self.app.post("/process")(process_endpoint)
```

This pattern aligns with worker runtime philosophy and avoids decorator noise.

## 🔧 **Code Generation Rules**

### **Type Safety Requirements**

```python
# ✅ CORRECT: Modern Python 3.9+ typing
from typing import Any
def process(data: dict[str, Any]) -> list[str]: ...

# ❌ INCORRECT: Legacy typing that causes linting errors
from typing import Dict, List
def process(data: Dict[str, Any]) -> List[str]: ...
```

### **Pydantic Model Standards**

```python
# ✅ CORRECT: Complete field definitions with descriptions
class WorkerRequest(BaseModel):
    text: str = Field(description="Input text to process")
    options: dict[str, Any] = Field(default_factory=dict)

# ❌ INCORRECT: Bare types without Field() descriptions
class WorkerRequest(BaseModel):
    text: str
    options: dict
```

### **Error Handling Patterns**

```python
# ✅ CORRECT: Comprehensive HTTP exception mapping
try:
    result = self._engine.process(request.text)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    raise HTTPException(status_code=500, detail="Processing failed")

# ❌ INCORRECT: Generic exception handling
except Exception:
    return {"error": "Something went wrong"}
```

## 📊 **Schema Design Principles**

### **Capability Schema Structure**

```python
# Follow this exact pattern for all capabilities
CAPABILITY_NAME = CapabilityDefinition(
    name="Human Readable Name",
    description="Clear purpose description",
    input_schema={
        "type": "object",
        "properties": { ... },
        "required": [ ... ]
    },
    output_schema={
        "type": "object",
        "properties": { ... },
        "required": [ ... ]
    }
)
```

### **Multi-Operation Schema (Sonnet Pattern)**

```python
# Use oneOf for operation discrimination
input_schema = {
    "type": "object",
    "oneOf": [
        {
            "properties": {
                "operation": {"const": "store"},
                "data": { ... }  # Operation-specific schema
            }
        },
        {
            "properties": {
                "operation": {"const": "retrieve"},
                "id": {"type": "string"}
            }
        }
    ]
}
```

## 🗄️ **Storage Strategy Guidelines**

### **In-Memory + Filesystem (High Performance)**

- Use for services requiring fast retrieval
- Implement proper synchronization for concurrency
- Plan for memory growth with data volume
- Include index rebuild logic for restarts

### **Pure Filesystem (Stateless)**

- Use for simple ingest-focused services
- Organize with clear directory structures
- Support scanning operations for queries
- Maintain human-readable file formats

### **Hybrid Approach (Recommended)**

```python
class StorageEngine:
    def __init__(self, enable_indexing: bool = True):
        self.use_index = enable_indexing
        self._index = {} if enable_indexing else None

    def retrieve(self, id: str):
        if self.use_index:
            return self._index.get(id)
        return self._scan_filesystem(id)
```

## 🧪 **Testing Requirements**

Every worker MUST include:

```python
# Comprehensive --test mode
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_worker()
    else:
        uvicorn.run(app, host="0.0.0.0", port=8080)

def test_worker():
    """Validate all core functionality"""
    print("🧪 Testing Worker Functionality...")

    # 1. Engine instantiation test
    engine = WorkerEngine()
    assert engine is not None

    # 2. Core operation tests
    # ... comprehensive validation

    # 3. Error handling tests
    # ... exception scenarios

    print("✅ All tests passed!")
```

### **Testing Strategy Patterns (Codex Insights)**

**Domain-First Testing** (lightweight):

```python
# Test core logic without FastAPI dependencies
def test_worker():
    """Test domain service directly"""
    engine = WorkerEngine()
    result = engine.process("test input")
    assert result.success
```

**Integration Testing** (comprehensive):

```python
# Test full service stack including FastAPI
def test_worker():
    """Test complete worker integration"""
    worker = WorkerApplication()
    # Test HTTP endpoints, dependencies, error handling
```

**Recommendation**: Support both patterns - domain-first for CI/CD, integration for development validation.

## 🔄 **Extension Strategy Best Practices**

### **Schema-Based Extensions (Type Safe)**

```python
class WorkerMetadata(BaseModel):
    # Ready for AI enhancements
    auto_generated: bool = Field(default=False)
    ai_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    processing_hints: list[str] = Field(default_factory=list)
```

### **Method Hook Extensions (Flexible)**

```python
class ExtensibleWorker:
    def _pre_process_hook(self, data: dict) -> dict:
        """Override for custom preprocessing"""
        return data

    def _post_process_hook(self, result: dict) -> dict:
        """Override for custom postprocessing"""
        return result
```

## 📝 **Code Quality Standards**

### **Required Patterns**

1. **Complete type annotations** on all functions and methods
2. **Docstrings** for all public methods with clear parameter descriptions
3. **Comprehensive error handling** with appropriate HTTP status codes
4. **Validation functions** that test all core functionality
5. **Clean imports** organized by standard library, third-party, local

### **Pylance Configuration**

```python
# Use pyright ignore comments sparingly and only for FastAPI limitations
@app.post("/analyze")
async def analyze_endpoint(request: AnalyzeRequest) -> AnalyzeResponse:  # pyright: ignore[misc]
    """FastAPI endpoint requires this ignore for route handler typing"""
```

## 🎯 **Implementation Workflow**

Follow the proven 4-phase development pattern:

### **Phase A: Schema Definition**

- Define all Pydantic models with complete type annotations
- Create capability schema with proper input/output validation
- Add schema to central registry

### **Phase B: Business Logic**

- Implement engine class with core algorithms
- Add comprehensive error handling and validation
- Write unit tests for all business logic

### **Phase C: Service Integration**

- Implement WorkerApplication interface completely
- Add FastAPI route handlers with proper typing
- Configure all required abstract methods

### **Phase D: Testing & Validation**

- Create comprehensive --test mode
- Validate all error scenarios
- Ensure clean linting (no warnings/errors)

## 🚨 **Common AI Assistant Mistakes**

1. **Type Annotation Shortcuts**: Using bare `dict` instead of `dict[str, Any]`
2. **Import Path Errors**: Mismatched function names between modules
3. **Incomplete Abstract Methods**: Missing required WorkerApplication methods
4. **Generic Error Handling**: Not distinguishing different error types
5. **Missing Test Validation**: No --test mode or incomplete testing
6. **Legacy Typing**: Using `typing.Dict` instead of `dict` (Python 3.9+)

## 🎉 **Success Metrics**

A well-generated worker will:

- ✅ Pass all type checking (mypy + pylance) with zero errors
- ✅ Include comprehensive --test mode with validation
- ✅ Follow established patterns from reference implementations
- ✅ Support both core functionality and future extensions
- ✅ Handle errors gracefully with appropriate HTTP status codes
- ✅ Include complete documentation and clear type hints

## 📚 **Required Reading for AI Assistants**

Before generating workers, AI assistants should read:

1. `docs/development/WORKER_DEVELOPMENT_GUIDE.md` - Core development patterns
2. `docs/development/AI_DEPLOYMENT_OPERATIONAL_PATTERNS.md` - Deployment and operational lessons learned
3. `docs/development/IMPLEMENTATION_STATUS_DEPLOYMENT_PATTERNS.md` - What's implemented vs conceptual
4. `docs/development/SONNET_VS_CODEX_ZETTEL_COMPARISON.md` - Architecture trade-offs
5. `docs/development/UNIFIED_SONNET_CODEX_REFACTORING_PLAN.md` - Current platform refactoring status
6. `services/crank_hello_world.py` - Reference implementation template
7. `src/crank/capabilities/schema.py` - Capability registry patterns
8. `.vscode/AGENT_CONTEXT.md` - Platform architectural context

**Remember**: The goal is not just working code, but code that integrates seamlessly with established patterns while supporting future enhancement and maintenance. Quality over speed! 🚀
