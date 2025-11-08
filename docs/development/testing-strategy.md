# Testing Strategy for Crank Platform

## Overview

The Crank Platform uses a comprehensive, multi-tiered testing strategy designed for CI/CD workflows, development efficiency, and production reliability. Our approach balances speed, coverage, and confidence across different testing scenarios.

## Testing Pyramid

```
Integration Tests (Slow, High Confidence)
├── Full platform validation (confidence_test_suite.py)
├── Multi-service communication (enhanced_smoke_test.py) 
└── Security & certificate validation

Smoke Tests (Medium Speed, Critical Path)
├── Service health validation
├── API endpoint verification
└── Core functionality checks

Unit Tests (Fast, Isolated)
├── Business logic validation (services/*)
├── Boundary shim testing (ml_boundary_shims)
└── Framework validation (conftest, fixtures)
```

## Test Categories & Markers

### Primary Test Markers

| Marker | Purpose | Speed | Dependencies | CI Usage |
|--------|---------|-------|-------------|----------|
| `@pytest.mark.unit` | Fast, isolated tests | < 1s | None | Always |
| `@pytest.mark.smoke` | Critical path validation | < 30s | Docker | PR validation |
| `@pytest.mark.integration` | Multi-service tests | < 5min | Docker + Network | Release validation |
| `@pytest.mark.performance` | Benchmarks & load tests | Variable | Depends on test | Nightly builds |
| `@pytest.mark.security` | Security validation | < 2min | Docker | Release validation |

### Auxiliary Markers

| Marker | Purpose | Usage |
|--------|---------|-------|
| `@pytest.mark.gpu` | Requires GPU resources | Conditional execution |
| `@pytest.mark.network` | Requires network connectivity | Skip in isolated environments |
| `@pytest.mark.docker` | Requires Docker containers | Skip if Docker unavailable |
| `@pytest.mark.slow` | Long-running tests (>30s) | Skip in fast CI runs |

## CI/CD Integration

### Unified Test Runner

The `test_runner.py` provides a unified interface for all testing scenarios:
```bash
# Development workflow commands
python test_runner.py --unit                    # Fast feedback loop
python test_runner.py --smoke                   # Pre-commit validation
python test_runner.py --integration            # Pre-merge validation

# CI/CD pipelines
python test_runner.py --ci                     # Fast CI validation
python test_runner.py --pr                     # Pull request gate
python test_runner.py --release                # Release validation

# Coverage & reporting
python test_runner.py --unit --coverage        # Unit test coverage
python test_runner.py --all --coverage --html  # Full coverage report
```

### Test Pipeline Stages

#### 1. Fast Feedback (< 2 minutes)
```bash
# Unit tests only - fast developer feedback
python test_runner.py --unit --parallel
```
- **Target**: < 60 seconds
- **Coverage**: Business logic, type safety, error handling
- **Triggers**: Every commit, pre-commit hooks

#### 2. Pull Request Validation (< 5 minutes)
```bash
# Unit + Smoke tests - ensure changes don't break critical paths
python test_runner.py --pr --coverage --xml-output=junit.xml
```
- **Target**: < 300 seconds  
- **Coverage**: Critical paths, service health, API endpoints
- **Triggers**: Pull request creation/updates

#### 3. Integration Validation (< 15 minutes)
```bash
# Full test suite - comprehensive validation
python test_runner.py --release --coverage-html --json-report=results.json
```
- **Target**: < 900 seconds
- **Coverage**: Multi-service communication, security, performance
- **Triggers**: Merge to main, release branches

## Test Organization

### Directory Structure

```
tests/
├── test_basic_validation.py      # @pytest.mark.unit - Framework tests
├── test_ml_boundary_shims.py     # @pytest.mark.unit - ML isolation layer
├── test_framework_validation.py  # @pytest.mark.unit - Test infrastructure
├── conftest.py                   # Fixtures and configuration
├── enhanced_smoke_test.py        # @pytest.mark.smoke - Service validation
├── test_streaming_basic.py       # @pytest.mark.smoke - Streaming patterns
├── confidence_test_suite.py      # @pytest.mark.integration - Full platform
└── integration_test_suite.py     # @pytest.mark.integration - Service mesh
```

### Naming Conventions

- **Unit tests**: `test_[component].py` - Test individual components
- **Smoke tests**: `test_[service]_basic.py` - Test critical service paths
- **Integration tests**: `test_[feature]_integration.py` - Test multi-service features

## Test Quality Standards

### Unit Tests
- **Coverage Target**: 80%+ for business logic
- **Speed Target**: < 1 second per test
- **Dependencies**: None (mocked)
- **Isolation**: Complete - no shared state

### Smoke Tests  
- **Coverage Target**: Critical paths only
- **Speed Target**: < 30 seconds per service
- **Dependencies**: Docker containers
- **Isolation**: Service-level - containers isolated

### Integration Tests
- **Coverage Target**: End-to-end workflows
- **Speed Target**: < 5 minutes per scenario
- **Dependencies**: Full environment
- **Isolation**: Environment-level - clean state per test

## Coverage Reporting

### Development Workflow
```bash
# Generate coverage for specific components
python test_runner.py --unit --coverage
python test_runner.py --smoke --coverage --html

# View detailed coverage
open htmlcov/index.html
```

### CI Pipeline Integration
```bash
# Generate coverage reports for CI systems
python test_runner.py --ci --coverage --xml-output=coverage.xml
python test_runner.py --all --coverage --json-report=results.json
```

### Coverage Targets

| Component | Target | Rationale |
|-----------|---------|----------|
| ML Boundary Shims | 90%+ | Critical for type safety |
| Core Services | 80%+ | Business logic validation |
| Integration Tests | 70%+ | End-to-end scenarios |
| Overall Platform | 75%+ | Balanced coverage |

## Performance Testing

### Benchmarking Strategy
- **Unit Level**: Boundary shim overhead (< 1ms)
- **Service Level**: Response times (< 500ms for health checks)
- **Platform Level**: End-to-end workflows (< 30s)

### Load Testing Integration
```bash
# Performance benchmarks
python test_runner.py --performance

# Load testing (separate tooling)
python create_load_test_script.py --endpoint https://localhost:8443
python run_load_test_in_azure.py --script locust_script.py
```

## Development Workflow Integration

### Pre-commit Testing
```bash
# Fast validation before committing
python test_runner.py --unit
```

### Feature Development
```bash
# Test driven development cycle
python test_runner.py --unit --coverage  # Write tests first
# ... implement feature ...
python test_runner.py --smoke            # Verify integration
```

### Pre-merge Validation
```bash
# Complete validation before merge
python test_runner.py --pr --verbose
```

## Debugging & Troubleshooting

### Test Failures
```bash
# Verbose output for debugging
python test_runner.py --unit --verbose

# Individual test debugging
uv run pytest tests/test_ml_boundary_shims.py::TestMLBoundaryShims::test_safe_clip_analyze_success -v

# Coverage gap analysis
python test_runner.py --unit --coverage --html
```

### Environment Issues
```bash
# Check prerequisites
python test_runner.py --integration  # Validates Docker, network, etc.

# Legacy smoke test validation
python test_runner.py --smoke --include-legacy
```

## Best Practices

### Test Design
1. **Arrange-Act-Assert**: Clear test structure
2. **Descriptive Names**: Test names explain what/why
3. **Single Responsibility**: One concept per test
4. **Fast Feedback**: Unit tests run in < 1s
5. **Deterministic**: Tests always pass/fail consistently

### Mocking Strategy
1. **Isolate External Dependencies**: Mock network, file system, ML libraries
2. **Type-Safe Mocks**: Use proper typing with mocks
3. **Behavior Verification**: Test interactions, not just return values
4. **Realistic Data**: Mock data matches production patterns

### Pipeline Integration

1. **Fail Fast**: run fastest tests first
2. **Parallel Execution**: Use pytest-xdist when beneficial
3. **Proper Exit Codes**: 0 for success, 1 for failure
4. **Structured Reporting**: JSON/XML for automated processing
5. **Artifact Preservation**: Save coverage reports, logs

## Monitoring & Metrics

### Test Health Metrics
- **Pass Rate**: % of tests passing over time
- **Test Duration**: Trend analysis for performance regression
- **Coverage Trends**: Coverage percentage over time
- **Flaky Tests**: Tests with inconsistent results

### CI Pipeline Metrics
- **Build Time**: Total pipeline duration
- **Test Distribution**: Time spent in each test category
- **Failure Analysis**: Common failure patterns
- **Resource Usage**: CPU, memory, Docker container usage

## Migration Strategy

### Integrating Legacy Tests
1. **Gradual Migration**: Convert existing tests to pytest framework
2. **Marker Addition**: Add appropriate markers to existing tests
3. **Runner Integration**: Include legacy tests via `--include-legacy`
4. **Deprecation Path**: Plan removal of redundant legacy tests

### Continuous Improvement
1. **Regular Review**: Monthly assessment of test strategy effectiveness
2. **Coverage Analysis**: Identify gaps and improvement opportunities  
3. **Performance Optimization**: Optimize slow tests and CI pipeline
4. **Tool Updates**: Keep testing tools and dependencies current

## Conclusion

This testing strategy provides a scalable, maintainable approach to validating the Crank Platform across development, CI/CD, and production scenarios. The multi-tiered approach ensures fast feedback for developers while maintaining comprehensive validation for releases.

Key benefits:
- **Fast Development Cycle**: Unit tests provide immediate feedback
- **Reliable CI/CD**: Structured pipeline stages prevent regression
- **Production Confidence**: Comprehensive integration validation
- **Maintainable Tests**: Clear organization and consistent patterns
