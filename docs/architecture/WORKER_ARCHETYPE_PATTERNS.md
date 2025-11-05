# 🏗️ Worker Archetype Patterns & Test Harness Architecture

## 🎯 Overview

The crank-platform workers serve a dual purpose:

1. **Reference Implementations**: Archetypal patterns for external worker development
2. **Test Harness**: Validation components for platform functionality

## 🎮 Current Worker Archetypes

### 📧 **Email Processing Pattern** (`crank-email-parser-dev`)

- **Port**: 8300
- **Pattern**: Stream processing with classification
- **Archetype**: High-throughput document ingestion
- **Reference for**: Mail archive processing, document pipelines
- **Test Validation**: Streaming APIs, worker registration, health checks

### 📄 **Document Conversion Pattern** (`crank-doc-converter-dev`)

- **Port**: 8100
- **Pattern**: Transformation services with format conversion
- **Archetype**: Document processing workflows
- **Reference for**: File format conversion, content transformation
- **Test Validation**: File upload/download, format handling, error recovery

### 🖼️ **Image Classification Pattern** (`crank-image-classifier-*-dev`)

- **Ports**: 8400 (GPU), 8401 (CPU)
- **Pattern**: ML inference with resource allocation
- **Archetype**: AI model deployment (dual CPU/GPU)
- **Reference for**: Computer vision, ML inference services
- **Test Validation**: GPU allocation, model loading, inference APIs

### 📊 **Streaming Analytics Pattern** (`crank-streaming-dev`)

- **Port**: 8500
- **Pattern**: Real-time data processing
- **Archetype**: Event-driven analytics
- **Reference for**: Real-time dashboards, event processing
- **Test Validation**: WebSocket connections, real-time data flow

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
