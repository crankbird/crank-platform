# Container Test Suite

This directory contains comprehensive tests to validate the container-first architecture and ensure all services work correctly in both development and production environments.

## Test Categories

### 1. Build Validation Tests
- **`test_container_builds.py`** - Validates all containers build successfully from manifests
- **`test_manifest_validation.py`** - Ensures build manifests are consistent and complete

### 2. Service Health Tests  
- **`test_service_health.py`** - Validates all service health endpoints respond correctly
- **`test_service_startup.py`** - Tests service startup sequence and dependency ordering

### 3. Integration Tests
- **`test_service_communication.py`** - Validates inter-service communication works correctly
- **`test_platform_workers.py`** - Tests platform → worker API communication

### 4. Environment Tests
- **`test_development_environment.py`** - Validates development environment works correctly
- **`test_production_simulation.py`** - Tests local production simulation environment

### 5. Confidence Tests
- **`confidence_test_suite.py`** - Main test runner that executes full validation

## Running Tests

### Quick Confidence Check
```bash
python3 tests/confidence_test_suite.py
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
- `PLATFORM_URL` - Platform service URL (default: http://localhost:8000)
- `TEST_TIMEOUT` - HTTP request timeout (default: 30s)
- `DOCKER_COMPOSE_FILE` - Compose file to test (default: docker-compose.development.yml)

## Expected Test Results

### ✅ Passing Tests Indicate:
- All containers build successfully from standardized manifests
- All services start up and respond to health checks
- Inter-service communication works correctly  
- Platform can communicate with all workers
- GPU services are properly configured (when available)

### ❌ Failing Tests May Indicate:
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