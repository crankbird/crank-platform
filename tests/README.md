# Test Suite Organization

This directory contains the **authoritative test suite** for the Crank Platform. All functional tests, validation tests, and integration tests belong here.

## Directory Structure Philosophy

- **`tests/`** ← **All test code belongs here**
- **`scripts/`** ← Operational utilities only (setup, deployment, maintenance)

## Test Categories

### 1. Core Integration Tests

- **`enhanced_smoke_test.py`** - **Primary test suite** - Universal smoke test with platform detection
- **`integration_test_suite.py`** - Service mesh integration validation
- **`confidence_test_suite.py`** - Full platform confidence validation

### 2. Service-Specific Tests

- **`test-hello-world.py`** - Basic mesh connectivity validation
- **`test_streaming_basic.py`** - Streaming service functionality
- **`test_email_pipeline.py`** - Email processing pipeline
- **`test_kevin_runtime.py`** - Container runtime abstraction

### 3. Build Validation Tests

- **`test_container_builds.py`** - Validates all containers build successfully from manifests
- **`test_manifest_validation.py`** - Ensures build manifests are consistent and complete

### 4. Performance & GPU Tests

- **`test_cuda_regression.py`** - CUDA/GPU functionality validation
- **`test_gpu_cpu_performance.py`** - Performance benchmarks
- **`intensive_benchmark.py`** - Resource-intensive performance tests

### 5. Security & Certificate Tests

- **`test-certificate-architecture.sh`** - Certificate authority validation
- **`test_certificate_fix.py`** - Certificate functionality tests

## Primary Test Entry Points

### Development Workflow

```bash
# Quick smoke test (recommended for development)
python tests/enhanced_smoke_test.py

# With optional container rebuild
python tests/enhanced_smoke_test.py --rebuild

# Platform-specific JSON output
python tests/enhanced_smoke_test.py --json
```

### Full Validation

```bash
# Complete confidence validation
python tests/confidence_test_suite.py

# Integration test suite
python tests/integration_test_suite.py
```

### Individual Test Categories

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
