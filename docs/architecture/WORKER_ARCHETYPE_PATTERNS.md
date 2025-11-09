# 🏗️ Worker Archetype Patterns & Test Harness Architecture

## 🎯 Strategic Intent

**CORE MISSION**: Establish 6 proven worker archetype patterns that serve as replicable templates for any Python-based service, using successful patterns from `crank-email-classifier` and `crank-image-classifier-cpu` as the foundation.

**DUAL PURPOSE**: The crank-platform workers serve as:

1. **Reference Implementations**: Archetypal patterns for external worker development

2. **Test Harness**: Validation components for platform functionality

## 🎮 The 6 Core Worker Archetypes

These archetypes are designed to be **adaptable enough for pretty much any Python-based program**:

### 1. � **File Conversion (In-Memory)** - `crank-doc-converter`

- **Port**: 8100

- **Pattern**: Transform files that easily fit in memory

- **Use Cases**: PDF→text, image format conversion, small document processing

- **Memory Profile**: Single file operations, <100MB typical

- **Reference Implementation**: Based on proven email-classifier pattern

### 2. � **File Processing (Large Files)** - `crank-email-parser`

- **Port**: 8300

- **Pattern**: Parse/process arbitrarily large files with streaming

- **Use Cases**: Log file analysis, large dataset processing, archive parsing

- **Memory Profile**: Streaming operations, handles multi-GB files

- **Reference Implementation**: Established working pattern

### 3. 🏷️ **Message Text Classification** - `crank-email-classifier`

- **Port**: 8200

- **Pattern**: Classify discrete text units that fit in memory

- **Use Cases**: Email classification, sentiment analysis, text categorization

- **Memory Profile**: Per-message processing, <10MB typical

- **Reference Implementation**: ✅ **PROVEN SUCCESSFUL PATTERN**

### 4. 🖼️ **Still Image Classification (CPU)** - `crank-image-classifier-cpu`

- **Port**: 8401

- **Pattern**: CPU-only image processing with limited capability/speed

- **Use Cases**: Basic image recognition, fallback processing, development

- **Resource Profile**: CPU-bound, moderate performance

- **Reference Implementation**: ✅ **PROVEN SUCCESSFUL PATTERN**

### 5. 🚀 **Still Image Classification (GPU)** - `crank-image-classifier-gpu`

- **Port**: 8400

- **Pattern**: GPU-enabled processing with full capabilities

- **Use Cases**: High-performance computer vision, real-time inference

- **Resource Profile**: GPU-accelerated, high performance

- **Reference Implementation**: Based on proven CPU pattern

### 6. 📊 **Streaming Data Processing** - `crank-streaming`

- **Port**: 8500

- **Pattern**: Real-time data stream processing

- **Use Cases**: Live analytics, event processing, real-time dashboards

- **Memory Profile**: Continuous processing, bounded memory usage

- **Reference Implementation**: Needs alignment to proven patterns

## 🔧 Extraction Patterns for External Repos

### 📋 **Standard Worker Interface**

All workers implement:

```python
# Required endpoints

GET  /health          # Health check
POST /v1/workers      # Platform registration
GET  /api/docs        # API documentation
GET  /metrics         # Prometheus metrics
GET  /version         # Service version

```

### 🏗️ **Container Configuration Pattern**

```dockerfile
# Standard base pattern

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8xxx
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8xxx"]

```

### 🔐 **Security Pattern** (mTLS Integration)

```yaml
# Docker compose pattern

services:
  worker-name:
    build: .
    ports:

      - "8xxx:8xxx"
    environment:

      - PLATFORM_URL=https://crank-platform-dev:8443

      - SSL_CERT_PATH=/certs/client.crt

      - SSL_KEY_PATH=/certs/client.key
    volumes:

      - ./certs:/certs:ro

```

## 🧪 Test Harness Functionality

### ✅ **Platform Validation**

Each worker validates:

- **API Contract**: Worker registration endpoints

- **Security Model**: mTLS certificate handling

- **Resource Allocation**: CPU/GPU assignment

- **Health Monitoring**: Status and metrics endpoints

- **Error Handling**: Graceful failure patterns

### 📊 **Coverage Matrix**

| Worker Type | API Validation | Resource Tests | Security Tests | Performance Tests |
|-------------|---------------|----------------|----------------|------------------|
| Email Parser | ✅ | ✅ (CPU intensive) | ✅ | ✅ (throughput) |
| Doc Converter | ✅ | ✅ (I/O intensive) | ✅ | ✅ (latency) |
| Image Classifier | ✅ | ✅ (GPU/CPU dual) | ✅ | ✅ (inference) |
| Streaming | ✅ | ✅ (Memory intensive) | ✅ | ✅ (real-time) |

## 🚀 External Repository Development

### 📂 **Recommended Structure for External Workers**

```
my-worker-repo/
├── src/
│   ├── main.py              # FastAPI application
│   ├── worker_interface.py  # Platform integration
│   └── business_logic.py    # Core functionality
├── tests/
│   ├── test_integration.py  # Platform compatibility tests
│   └── test_business.py     # Business logic tests
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/
│   └── platform_integration.md
└── platform_test.py        # Validation against deployed platform

```

### 🔗 **Integration Testing Strategy**

1. **Local Development**: Test against local crank-platform

2. **CI/CD Pipeline**: Deploy worker to test platform instance

3. **Platform Validation**: Run worker against multiple platform versions

4. **Performance Benchmarking**: Compare against reference implementations

## 📈 **Benefits of This Architecture**

### 🎯 **For Platform Development**

- **Validation**: Workers test platform capabilities comprehensively

- **Regression Testing**: Worker patterns catch platform breaking changes

- **Performance Baselines**: Reference implementations provide benchmarks

### 👥 **For External Developers**

- **Clear Patterns**: Proven archetypal implementations

- **Testing Framework**: Validation tools for platform compatibility

- **Migration Path**: Extract patterns with confidence

### 🔧 **For Operations**

- **Deployment Validation**: Test harness validates platform deployments

- **Monitoring**: Worker patterns establish observability standards

- **Scaling Patterns**: Resource allocation and performance benchmarks

## 🎮 Mascot Ownership

- **🎭 Bella (Modularity)**: Worker interface standards and patterns

- **🐢 Gary (Testing)**: Test harness validation and benchmarking

- **🦙 Kevin (Portability)**: Container patterns and deployment strategies

- **🐰 Wendy (Security)**: mTLS integration and security patterns

## 🗺️ Future Roadmap

1. **Pattern Documentation**: Complete archetype extraction guides

2. **External Template**: Create template repository for new workers

3. **Validation Toolkit**: CLI tools for worker platform compatibility

4. **Performance Benchmarking**: Automated performance comparison suite

5. **Migration Tooling**: Automated extraction from platform to standalone repo
