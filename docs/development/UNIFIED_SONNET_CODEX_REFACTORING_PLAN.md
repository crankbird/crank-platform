# Unified Sonnet + Codex Worker Refactoring Plan

**Date**: November 14, 2025
**Purpose**: Synthesized refactoring roadmap incorporating insights from both AI analyses
**Scope**: All 9 Crank Platform workers with prioritized implementation strategy

## 🎯 **Executive Summary**

With complete coverage parity achieved between Sonnet and Codex analyses, we now have a comprehensive refactoring roadmap that combines tactical precision (Codex) with strategic framework (Sonnet). Both analyses identified the same critical issues, providing high confidence in our prioritization and approach.

## 📊 **Unified Conformance Assessment**

### **Tier A+ (Reference Standards) - 3 Workers**

| **Worker** | **Sonnet Grade** | **Codex Assessment** | **Unified Status** |
|------------|------------------|---------------------|-------------------|
| `crank_hello_world` | A+ Perfect | "Demonstrates almost every best-practice element" | ✅ **Reference Template** |
| `crank_sonnet_zettel_manager` | A+ Perfect | "Strong alignment: schema-first models, engine class" | ✅ **Multi-Operation Pattern** |
| `crank_philosophical_analyzer` | A+ Perfect | "Provides meaningful analysis" | ⚠️ **Needs decorator fix** |

### **Tier B+ (Good Foundation) - 4 Workers**

| **Worker** | **Sonnet Grade** | **Codex Assessment** | **Priority Action** |
|------------|------------------|---------------------|-------------------|
| `crank_email_classifier` | B+ Good | "Multi-classification logic lives in one mega-endpoint" | 🔥 **High - Split capabilities** |
| `crank_doc_converter` | B+ Good | "Contract + engine separation is solid" | 🔥 **High - Add testing/hooks** |
| `crank_email_parser` | B+ Good | "Multiple endpoints with explicit binding" | 🟡 **Medium - Add metadata strategy** |
| `crank_streaming` | B+ Good | "Covers SSE/WebSocket cases with explicit routes" | 🟡 **Medium - Extract orchestration** |

### **Tier D (Legacy Refactoring) - 2 Workers**

| **Worker** | **Sonnet Grade** | **Codex Assessment** | **Effort Estimate** |
|------------|------------------|---------------------|---------------------|
| `crank_image_classifier_advanced` | D Legacy | "Tier-D legacy workers that predate WorkerApplication" | 🚫 **Major - 3+ days** |
| `crank_image_classifier` (basic) | D Legacy | "Tier-D legacy workers that predate WorkerApplication" | 🚫 **Major - 2+ days** |

## 🔥 **Phase 1: Critical Path Fixes (Week 1)**

### **1.1 Philosophical Analyzer Quick Fix** ⏱️ *2 hours*

**Issue**: Decorator usage despite route-binding guidance (line 191)
**Codex**: "Replace decorator usage, adopt Pydantic request model"
**Sonnet**: "Uses decorator route binding vs explicit pattern"

**Implementation**:

```python
# Current (problematic)
@self.app.post("/analyze")
async def analyze_endpoint(request: dict[str, Any]) -> JSONResponse:

# Target (aligned)
async def analyze_endpoint(request: PhilosophicalRequest) -> PhilosophicalResponse:
    # Implementation

# Explicit binding
self.app.post("/analyze")(analyze_endpoint)
```

### **1.2 Email Classifier Capability Separation** ⏱️ *1 day*

**Issue**: "Multiplexed classifier endpoint" (line 352)
**Codex**: "Split capability scopes (spam/bill/etc.)"
**Sonnet**: "No retrieval capability built-in, dict-based validation"

**Implementation**:

```python
# Current: Single EMAIL_CLASSIFICATION capability
# Target: Separate capabilities
EMAIL_SPAM_DETECTION = CapabilityDefinition(...)
EMAIL_BILL_DETECTION = CapabilityDefinition(...)
EMAIL_SENTIMENT_ANALYSIS = CapabilityDefinition(...)

# Per-classifier extension hooks
def _preprocess_spam_features(self, text: str) -> dict: ...
def _postprocess_bill_confidence(self, result: dict) -> dict: ...
```

**Downstream Migration Requirements**:

- **Controller contract updates** - Route new capability IDs to appropriate worker endpoints
- **Routing config updates** - Update mesh routing tables for new capability scope
- **Plugin manifests** - Update capability declarations in worker deployment configs
- **Migration/shim strategy** - Maintain existing `/classify` endpoint during transition
- **Backward compatibility matrix** - Test existing clients against new capability structure
- **Capability retirement plan** - Phase out old EMAIL_CLASSIFICATION ID after validation

### **1.3 Universal Testing Infrastructure** ⏱️ *2 days*

**Issue**: Multiple workers lack `--test` modes
**Codex**: "Add lightweight `--test` harnesses"
**Sonnet**: "No testing mode - cannot validate without dependencies"

**Target Workers**:

- Document Converter
- Email Parser
- Streaming Worker

**Implementation Pattern**:

```python
**Implementation Pattern**:

```python
# Use the IMPLEMENTED crank.testing helper
from crank.testing import ensure_dependency

def test_worker():
    """Test core functionality with environment-specific skip handling."""
    ensure_dependency("pandoc", skip_message="Pandoc not available, skipping conversion tests")
    ensure_dependency("torch.cuda", skip_message="CUDA not available, skipping GPU tests")

    engine = WorkerEngine()
    # Test domain logic
    # Validate error scenarios
    print("✅ All tests passed!")
```

**Environment-Specific Skip Strategy**:

The `crank.testing.ensure_dependency` helper is IMPLEMENTED in `src/crank/testing/dependency_checker.py` and provides:

- **Pandoc dependencies** - Skip document conversion tests gracefully
- **GPU libraries** - Skip CUDA/PyTorch tests on CPU-only systems
- **Network services** - Skip external API tests in isolated environments
- **Consistent output format** - Standardized skip messages via `crank.testing.ensure_dependency`

## 🏗️ **Phase 2: Architecture Enhancement (Week 2)**

### **2.1 Document Converter Structure** ⏱️ *1 day*

**Codex Recommendations**:

- "Introduce `ConversionPlan` dataclass"
- "Add `_select_engine`/`_post_process` hooks"

**Implementation**:

```python
@dataclass
class ConversionPlan:
    input_format: str
    output_format: str
    options: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

class DocumentConverter:
    def _select_engine(self, plan: ConversionPlan) -> str:
        """Override for custom conversion engine selection."""

    def _post_process(self, content: bytes, plan: ConversionPlan) -> bytes:
        """Override for custom post-processing."""
```

**Repository/Front-Matter Strategy**:

- **Conversion artifact storage** - Follow zettel worker pattern for converted documents
- **Metadata preservation** - YAML frontmatter for source document attributes
- **Publication pipeline contract** - Standardized metadata schema for downstream consumers
- **Version tracking** - Original format, conversion parameters, timestamp metadata
- **Future pipeline integration** - Consistent artifact location and metadata format

### **2.2 Email Parser Metadata Strategy** ⏱️ *1 day*

**Codex**: "Add `ParsedArchive` model with JSON/YAML serialization"
**Sonnet**: "No built-in search/filtering, requires filesystem scanning"

**Implementation**:

```python
class ParsedArchive(BaseModel):
    archive_id: str
    format: Literal["mbox", "eml"]
    message_count: int
    metadata_format: Literal["json", "yaml"]
    parsed_at: datetime

    def to_json_frontmatter(self) -> str: ...
    def to_yaml_frontmatter(self) -> str: ...
```

### **2.3 Streaming Orchestration Extraction** ⏱️ *1 day*

**Codex**: "Introduce `StreamingCoordinator` service"
**Sonnet**: "In-memory index needs synchronization for concurrency"

**Implementation**:

```python
class StreamingCoordinator:
    """Extracted orchestration logic for easier extension."""

    def handle_text_stream(self, request: StreamingRequest) -> AsyncGenerator: ...
    def manage_websocket_broadcast(self, connections: list[WebSocket]): ...
    def _customize_transport(self, stream_type: str) -> dict: ...
```

**Concurrency/Backpressure Strategy**:

- **Concurrency goals** - Define max concurrent streams, connection limits, memory bounds
- **Backpressure handling** - Implement client-side buffering and graceful degradation
- **SSE/WebSocket testing** - Simulation harness for testing without live connections
- **Test infrastructure** - Mock connection framework similar to universal `--test` pattern
- **Performance monitoring** - Stream latency, throughput, and error rate tracking

## 🚫 **Phase 3: Legacy Migration (Weeks 3-4)**

### **3.1 Basic Image Classifier Migration** ⏱️ *2 days*

**Current**: 656 lines in `relaxed-checking/` with legacy patterns
**Target**: Modern WorkerApplication with proper patterns

**Migration Steps**:

1. **WorkerApplication adoption** - Replace FastAPI direct instantiation
2. **Capability definitions** - Create `BASIC_IMAGE_CLASSIFICATION`
3. **Service extraction** - Separate GPU detection and inference logic
4. **CLI tests** - Add `--test` mode with fixture loading

```python
class BasicImageClassifier(WorkerApplication):
    def __init__(self):
        super().__init__(service_name="crank-image-classifier-basic")
        self.classifier = ImageClassificationEngine()

    def get_capabilities(self) -> list[CapabilityDefinition]:
        return [BASIC_IMAGE_CLASSIFICATION]
```

**Deployment Follow-up Tasks**:

- **Plugin YAML updates** - Update capability declarations in deployment manifests
- **Build manifest updates** - Ensure Docker build includes new WorkerApplication patterns
- **CI job scheduling** - Configure basic inference testing in pipeline
- **GPU-capable CI** - Add GPU nodes for advanced classifier testing (if needed)

### **3.2 Advanced Image Classifier Migration** ⏱️ *3 days*

**Current**: 732 lines with GPU dependencies and complex patterns
**Target**: Modern architecture with GPU service layer

**Migration Steps**:

1. **GPU service extraction** - Separate CUDA/PyTorch logic
2. **Multiple capability definitions** - YOLO, CLIP, scene classification
3. **Extension hooks** - Model loading, inference customization
4. **Comprehensive testing** - Mock GPU for CI, real GPU for integration

```python
class AdvancedImageClassifier(WorkerApplication):
    def __init__(self):
        super().__init__(service_name="crank-image-classifier-advanced")
        self.gpu_service = GPUInferenceService()

    def get_capabilities(self) -> list[CapabilityDefinition]:
        return [GPU_YOLO_DETECTION, GPU_CLIP_ANALYSIS, GPU_SCENE_CLASSIFICATION]
```

**Advanced Deployment Follow-up Tasks**:

- **Plugin YAML updates** - Update GPU capability declarations and resource requirements
- **Build manifest updates** - Ensure Docker builds include CUDA/PyTorch layers properly
- **GPU-capable CI jobs** - Schedule GPU nodes for comprehensive model testing
- **Deployment artifact validation** - Test WorkerApplication patterns ship successfully
- **Resource management** - Update container limits and GPU allocation policies

## 🎯 **Success Metrics & Validation**

### **Phase 1 Success Criteria**

- ✅ Zero linting errors across all Phase 1 workers
- ✅ Philosophical analyzer uses explicit route binding
- ✅ Email classifier has separate capability definitions
- ✅ All workers have functional `--test` modes

### **Phase 2 Success Criteria**

- ✅ Document converter has structured request models
- ✅ Email parser has consistent metadata format strategy
- ✅ Streaming worker has extracted orchestration service
- ✅ All extension hooks documented and tested

### **Phase 3 Success Criteria**

- ✅ Both image classifiers inherit from WorkerApplication
- ✅ Capability definitions exist for all inference types
- ✅ GPU logic properly abstracted into service layers
- ✅ CI/CD tests pass without GPU dependencies

### **Overall Platform Success**

- ✅ **Pattern Consistency**: All 9 workers follow identical patterns
- ✅ **Type Safety**: Complete Pydantic models throughout
- ✅ **Testing Coverage**: Domain + integration testing for all workers
- ✅ **Extension Ready**: Hook points available for future enhancements
- ✅ **Documentation**: Updated guides reflect real implementation patterns

## 📋 **Implementation Checklist**

### **Week 1 - Critical Fixes**

- [ ] Fix philosophical analyzer decorator usage
- [ ] Split email classifier capabilities
- [ ] Add `--test` modes to doc converter, email parser, streaming
- [ ] Validate all linting passes cleanly

### **Week 2 - Architecture Enhancement**

- [ ] Implement document converter structured models
- [ ] Add email parser metadata strategy
- [ ] Extract streaming orchestration service
- [ ] Document extension hook patterns

### **Week 3-4 - Legacy Migration**

- [ ] Migrate basic image classifier to WorkerApplication
- [ ] Migrate advanced image classifier to WorkerApplication
- [ ] Create image classification capability definitions
- [ ] Implement GPU service abstraction layer

### **Validation & Documentation**

- [ ] Run full test suite across all workers
- [ ] Update AI assistant development guides
- [ ] Create migration templates for future workers
- [ ] Performance benchmark validation

## 🎉 **Expected Outcomes**

Upon completion, the Crank Platform will have:

1. **Unified Architecture**: All 9 workers following identical modern patterns
2. **Comprehensive Testing**: Domain + integration coverage for reliable development
3. **Extension Ready**: Standardized hook points for future AI assistant enhancements
4. **Technical Debt Eliminated**: No legacy FastAPI patterns remaining
5. **AI Assistant Friendly**: Clear, consistent patterns for future worker generation

This unified plan leverages the precision of Codex's technical recommendations with the systematic approach of Sonnet's architectural framework, ensuring both immediate improvement and long-term maintainability! 🚀

## 📚 **Reference Materials**

- **Sonnet Analysis**: `docs/development/SONNET_WORKER_PATTERN_ANALYSIS_REPORT.md`
- **Codex Analysis**: `docs/reports/codex_worker_alignment_report.md`
- **Meta-Comparison**: `docs/development/SONNET_CODEX_META_COMPARISON_ANALYSIS.md`
- **Best Practices**: `docs/development/AI_ASSISTANT_WORKER_GENERATION_GUIDE.md`
