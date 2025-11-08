# CRITICAL CONTEXT - ALWAYS REMEMBER

## Package Management
### ALWAYS USE UV, NEVER PIP
```bash
uv pip install package-name
uv pip list
uv pip freeze > requirements.txt
```

## Image Classifier Architecture
### TWO SEPARATE CLASSIFIERS - NOT ONE

### CPU Classifier (Basic)
- **File**: `services/relaxed-checking/crank_image_classifier.py`
- **Purpose**: Lightweight, CPU-friendly, edge deployments
- **Dependencies**: OpenCV, PIL, scikit-learn
- **Type Checking**: Relaxed (in relaxed-checking/ dir)

### GPU Classifier (Advanced)
- **File**: `services/crank_image_classifier_advanced.py`
- **Purpose**: Heavy ML, GPU-accelerated, datacenter deployments
- **Dependencies**: PyTorch, YOLO, CLIP, transformers
- **Type Checking**: May need relaxed for ML libraries

## Docker Architecture
- **Reason for separation**: Docker GPU access limitations on macOS
- **CPU version**: Runs everywhere
- **GPU version**: Requires NVIDIA CUDA, WSL2/Linux testing

## History
- Originally planned auto GPU detection
- Reverted to separate implementations due to Docker/Mac limitations
- GPU version was in archive/ but restored from commit c283152
- Both are production services, neither is "legacy"

## Error Handling Philosophy
- "Fix what we can, tolerate what we must"
- Graduated type checking for different service complexity levels
- Real functionality over perfect type checking

## Critical Issues Identified (2025-11-08 Code Review)

### 🚨 BLOCKING ISSUES - Fix First
- **Issue #18 - MeshInterface Receipt System**: Two conflicting MeshReceipt classes, MeshReceiptSystem.generate_receipt() reads fields that MeshResponse doesn't expose. NO service can emit receipts currently.
- **Issue #22 - Fragile Import Paths**: sys.path mutations in multiple services will break on any reorganization
- **Issue #14 - Package Structure**: Need to move services under src/ to eliminate sys.path hacking

### 🔧 ARCHITECTURAL CLEANUP
- **Issue #19 - Security Config**: Only GPU classifier uses initialize_security properly, others use ad-hoc patterns
- **Issue #17 - Demo Tests**: Many tests only assert built-ins, need real service tests via MeshInterface  
- **Issue #16 - Docker/Compose**: Legacy configs reference non-existent files

### 🏗️ INFRASTRUCTURE IMPROVEMENTS  
- **Issue #25/24 - Universal GPU**: Runtime detection unimplemented, CUDA-only containers exclude Apple Silicon
- **Issue #13 - .gitignore**: Missing standard Python artifacts
- **Issue #12 - Azure Deployment**: Manual process, needs proper CI/CD automation

## Testing Infrastructure (Updated 2025-11-08)
### Unified Test Runner
**PRIMARY TOOL**: `uv run python test_runner.py`
```bash
# Development workflow
uv run python test_runner.py --unit          # Fast unit tests (< 60s)
uv run python test_runner.py --smoke         # Critical path validation (< 2min)
uv run python test_runner.py --integration   # Full platform tests (< 15min)

# CI/CD workflow
uv run python test_runner.py --ci           # CI-optimized (unit + smoke)
uv run python test_runner.py --pr           # Pull request validation
uv run python test_runner.py --release      # Release validation

# Coverage & reporting
uv run python test_runner.py --unit --coverage --html
```

### Test Organization
- **Unit Tests**: `@pytest.mark.unit` - Fast, isolated, no dependencies
- **Smoke Tests**: `@pytest.mark.smoke` - Service validation, requires Docker
- **Integration Tests**: `@pytest.mark.integration` - Full platform, requires Docker + Network
- **Documentation**: `docs/development/testing-strategy.md`

### Key Test Files
- `tests/test_ml_boundary_shims.py` - ML isolation layer with type safety
- `tests/test_basic_validation.py` - Framework validation
- `tests/conftest.py` - Fixtures and test infrastructure
- `test_runner.py` - Unified test orchestration

### Legacy Test Integration
- Existing smoke tests: `enhanced_smoke_test.py`, `confidence_test_suite.py`
- Can be included with: `--include-legacy` flag
- Gradual migration to pytest framework ongoing
