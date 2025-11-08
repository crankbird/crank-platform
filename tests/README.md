# Test Suite Organization

This directory contains the **unified test suite** for the Crank Platform with comprehensive CI/CD integration.

## 🚀 Quick Start - Unified Test Runner

**ALWAYS use the unified test runner for consistent, CI/CD-ready testing:**

```bash
# Development workflow (use UV!)
uv run python test_runner.py --unit          # Fast unit tests (< 60s)
uv run python test_runner.py --smoke         # Critical path validation
uv run python test_runner.py --integration   # Full platform validation

# CI/CD workflow
uv run python test_runner.py --ci           # CI pipeline (unit + smoke)
uv run python test_runner.py --pr           # Pull request validation
uv run python test_runner.py --release      # Release validation

# Coverage & reporting
uv run python test_runner.py --unit --coverage --html
uv run python test_runner.py --all --json-report=results.json
```

## 📋 Test Categories & Markers

### Primary Test Categories

| Category | Marker | Speed | Dependencies | Usage |
|----------|--------|--------|-------------|--------|
| **Unit Tests** | `@pytest.mark.unit` | < 1s | None | Development, CI |
| **Smoke Tests** | `@pytest.mark.smoke` | < 30s | Docker | PR validation |
| **Integration Tests** | `@pytest.mark.integration` | < 5min | Docker + Network | Release validation |
| **Performance Tests** | `@pytest.mark.performance` | Variable | Depends | Benchmarking |
| **Security Tests** | `@pytest.mark.security` | < 2min | Docker | Security validation |

### Directory Structure

```
tests/
├── test_runner.py                    # 🎯 UNIFIED TEST RUNNER (primary tool)
├── conftest.py                      # Fixtures and test infrastructure
├── pytest.ini                      # Test configuration and markers
│
├── test_basic_validation.py         # @pytest.mark.unit - Framework tests
├── test_ml_boundary_shims.py        # @pytest.mark.unit - ML isolation layer
├── test_framework_validation.py     # @pytest.mark.unit - Infrastructure
│
├── enhanced_smoke_test.py           # @pytest.mark.smoke - Service validation
├── test_streaming_basic.py          # @pytest.mark.smoke - Streaming patterns
├── quick_validation_test.py         # @pytest.mark.smoke - Quick validation
│
├── confidence_test_suite.py         # @pytest.mark.integration - Full platform
├── integration_test_suite.py        # @pytest.mark.integration - Service mesh
│
└── legacy/                          # Legacy tests (being migrated)
    ├── test_email_pipeline.py       # ⚠️ Hardcoded paths, needs cleanup
    ├── test_real_image.py           # ⚠️ Network dependencies
    └── test_gpu_cpu_performance.py  # ⚠️ Missing fixtures
```

## 📚 Documentation & Strategy

- **`docs/development/testing-strategy.md`** - Complete testing strategy guide
- **Testing pyramid**: Unit (fast) → Smoke (critical) → Integration (comprehensive)
- **Coverage targets**: 80%+ for core services, 90%+ for boundary shims
- **CI/CD integration**: Structured pipeline stages with proper reporting

## 🔄 Legacy Test Integration

Some existing tests are being gradually migrated to the unified framework:

### ✅ Integrated Tests
- `enhanced_smoke_test.py` - Can be run via `--include-legacy`
- `test_streaming_basic.py` - Available via legacy runner
- `quick_validation_test.py` - Available via legacy runner

### ⚠️ Tests Needing Cleanup
- `test_email_pipeline.py` - Hardcoded file paths, needs mocking
- `test_real_image.py` - Network dependencies, needs containerization
- `test_gpu_cpu_performance.py` - Missing fixtures, needs refactoring

## Development Workflow

## Testing Workflows

### Pre-commit Testing
```bash
# Fast validation before committing
uv run python test_runner.py --unit
```

### Feature Development
```bash
# Test-driven development cycle
uv run python test_runner.py --unit --coverage  # Write tests first
# ... implement feature ...
uv run python test_runner.py --smoke            # Verify integration
```

### Pre-merge Validation
```bash
# Complete validation before merge
uv run python test_runner.py --pr --verbose --coverage
```

## 🐛 Debugging & Troubleshooting

### Test Failures
```bash
# Verbose output for debugging
uv run python test_runner.py --unit --verbose

# Individual test debugging
uv run pytest tests/test_ml_boundary_shims.py::TestMLBoundaryShims::test_safe_clip_analyze_success -v

# Coverage gap analysis
uv run python test_runner.py --unit --coverage --html && open htmlcov/index.html
```

### Environment Issues
```bash
# Check prerequisites (Docker, network, etc.)
uv run python test_runner.py --integration

# Legacy smoke test validation
uv run python test_runner.py --smoke --include-legacy
```

## 🎯 Key Features

### Type Safety
- Complete type annotations with proper `-> None` returns
- TypedDict compatibility (YOLOResult, CLIPResult work with dict[str, Any])
- Comprehensive mocking for ML libraries (torch, transformers, etc.)

### CI/CD Ready
- Proper exit codes (0 success, 1 failure)
- Structured JSON/XML reporting for automation
- Coverage integration with configurable thresholds
- Parallel execution support when beneficial

### Performance Optimized
- Unit tests: < 1 second per test
- Smoke tests: < 30 seconds per service
- Integration tests: < 5 minutes per scenario
- Timeout protection and resource monitoring

## 📊 Test Quality Metrics

Current status (as of 2025-11-08):
- **48+ tests passing** ✅
- **Zero type checking errors** ✅
- **Complete ML boundary shim coverage** ✅
- **CI/CD pipeline integration** ✅

## 🔮 Future Roadmap

### Next Steps
1. **Unit tests for core services** (crank_image_classifier_advanced.py, crank_platform_service.py)
2. **Docker test environment** for reliable integration testing
3. **Legacy test cleanup** (remove hardcoded paths, network dependencies)
4. **Performance benchmarking** integration with load testing tools

### Migration Path
- Gradual conversion of legacy tests to pytest framework
- Addition of appropriate markers (@pytest.mark.smoke, etc.)
- Integration with unified test runner
- Deprecation of redundant standalone test scripts

## 💡 Best Practices for Contributors

1. **Always use UV**: `uv run python test_runner.py` (never pip!)
2. **Add proper markers**: Use `@pytest.mark.unit`, `@pytest.mark.smoke`, etc.
3. **Write fast unit tests**: < 1 second, no external dependencies
4. **Mock external dependencies**: Network, file system, ML libraries
5. **Test both success and failure paths**: Error handling is critical
6. **Use descriptive test names**: Explain what and why, not just how

## Platform-specific JSON output
python tests/enhanced_smoke_test.py --json
```

## Full Validation

```bash
# Complete confidence validation
python tests/confidence_test_suite.py

# Integration test suite
python tests/integration_test_suite.py
```

## Individual Test Categories

```bash
# Build validation
python3 -m pytest tests/test_container_builds.py -v

# Health checks
python3 -m pytest tests/test_service_health.py -v

# Integration testing
python3 -m pytest tests/test_service_communication.py -v
```

### Full Test Suite

```bash
# Run all tests with detailed output
python3 -m pytest tests/ -v --tb=short

# Run tests with coverage
python3 -m pytest tests/ --cov=services --cov-report=html
```

## Test Environment Setup

Tests assume you have the development environment running:

```bash
# Start development environment
docker-compose -f docker-compose.development.yml up -d

# Run confidence tests
python3 tests/confidence_test_suite.py

# Stop environment
docker-compose -f docker-compose.development.yml down
```

## Test Configuration

Tests use environment variables for configuration:

- `PLATFORM_URL` - Platform service URL (default: <http://localhost:8000>)
- `TEST_TIMEOUT` - HTTP request timeout (default: 30s)
- `DOCKER_COMPOSE_FILE` - Compose file to test (default: docker-compose.development.yml)

## Expected Test Results

### Passing Tests Indicate

- All containers build successfully from standardized manifests
- All services start up and respond to health checks
- Inter-service communication works correctly
- Platform can communicate with all workers
- GPU services are properly configured (when available)

### Failing Tests May Indicate

- Missing files referenced in build manifests
- Network connectivity issues between services
- Health check endpoint failures
- Dependency startup order problems
- Port conflicts or resource constraints

## Automated Testing

The confidence test suite is designed to be run:

- **After any container changes** - Validates builds still work
- **Before deployment** - Ensures environment is healthy
- **In CI/CD pipelines** - Automated validation
- **By AI agents** - Self-validation of changes
