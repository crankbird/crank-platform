# Worker Certificate Pattern - Architecture Guide

## Problem Solved
Eliminates timing issues between async FastAPI startup and certificate initialization that caused "No CA certificate available" warnings and potential security vulnerabilities.

## Pattern Overview

### ❌ **WRONG Pattern (Async Certificate Loading)**
```python
def main():
    app = create_fastapi()  # Creates app first
    uvicorn.run(app)        # Certificates loaded during async startup
    
@app.on_event("startup") 
async def startup():
    initialize_security()  # ASYNC - causes timing issues
```

### ✅ **CORRECT Pattern (Synchronous Certificate Loading)**
```python  
def main():
    # 1. Load certificates SYNCHRONOUSLY before FastAPI
    cert_pattern = WorkerCertificatePattern("service-name")
    cert_store = cert_pattern.initialize_certificates()
    
    # 2. Create FastAPI with pre-loaded certificates
    app = create_worker_app(cert_store=cert_store)
    
    # 3. Start server (certificates already in memory)
    cert_pattern.start_server(app, port=8201)
```

## Implementation Steps

### Option A: Use Worker Certificate Library (Recommended)
```python
from worker_cert_pattern import WorkerCertificatePattern, create_worker_fastapi_with_certs

def main():
    cert_pattern = WorkerCertificatePattern("crank-my-service")
    cert_store = cert_pattern.initialize_certificates()
    
    worker_config = create_worker_fastapi_with_certs(
        title="My Service",
        service_name="crank-my-service",
        cert_store=cert_store
    )
    
    setup_my_routes(worker_config["app"], worker_config)
    cert_pattern.start_server(worker_config["app"], port=8201)
```

### Option B: Manual Implementation  
If you prefer not to use the library, follow this exact pattern:

1. **Environment Setup**: Ensure `HTTPS_ONLY=true`, `CA_SERVICE_URL`, `SERVICE_NAME`
2. **Synchronous Cert Loading**: Call `asyncio.run(init_certificates())` in `main()` BEFORE FastAPI
3. **Pass cert_store**: Modify constructor to accept `cert_store` parameter
4. **Remove Async Cert Init**: Remove any `initialize_security()` calls from FastAPI startup events
5. **Use Pre-loaded Certs**: Access `cert_store._temp_cert_file` and `cert_store._temp_key_file` for uvicorn

## Docker Configuration Requirements

### docker-compose.yml
```yaml
crank-my-service:
  environment:
    - SERVICE_NAME=crank-my-service
    - HTTPS_ONLY=true  
    - CA_SERVICE_URL=https://crank-cert-authority:9090
  volumes:
    - crank-ca-certs:/shared/ca-certs:ro  # Standardized CA path
  depends_on:
    crank-cert-authority:
      condition: service_healthy
```

### Key Requirements
- **Volume Mount**: `/shared/ca-certs` for Root CA certificate
- **SERVICE_NAME**: Individual service identity for SAN certificates  
- **Dependency**: Wait for Certificate Authority Service health check

## Security Features Provided

- **Subject Alternative Names (SAN)**: Supports multiple DNS names per certificate
- **CSR Pattern**: Private keys generated locally, never transmitted
- **Enterprise Verification**: Full hostname verification for production
- **Standardized CA**: Single Root CA certificate location
- **Zero Timing Issues**: Synchronous loading eliminates race conditions

## Certificate DNS Names by Service

| Service | Primary DNS | Alternative DNS Names |
|---------|-------------|----------------------|
| platform | platform | localhost, crank-platform |
| crank-email-classifier | crank-email-classifier | localhost, email-classifier |
| crank-doc-converter | crank-doc-converter | localhost, doc-converter |

Add new services following the same pattern: `SERVICE_NAME`, `localhost`, `SHORT_NAME`

## Troubleshooting

### "No CA certificate available" Warning
- **Cause**: Using async certificate loading pattern
- **Fix**: Switch to synchronous certificate loading in `main()`

### "Certificate initialization completed but no certificates in memory"  
- **Cause**: `SERVICE_NAME` environment variable not set
- **Fix**: Ensure `SERVICE_NAME=crank-service-name` in docker-compose

### SSL Hostname Verification Failures
- **Cause**: Certificate missing SAN extensions
- **Fix**: Ensure latest `initialize_certificates.py` with SAN support

## Future Workers

All new workers MUST use this pattern. No exceptions for certificate loading timing.