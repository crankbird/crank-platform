# Worker Security Pattern Guide

**Status**: Complete ✅ (Issue #19, Nov 15, 2025)  
**Module**: `src/crank/security/` (7 files)  
**Coverage**: All 9 workers using unified security with HTTPS+mTLS

## Overview

This guide documents the unified security pattern established during Issue #19 (Security Configuration Scattered). The pattern provides **automatic HTTPS+mTLS** for all workers via the `WorkerApplication.run()` method.

## The Clean Minimal Pattern

**Reference Implementation**: `services/crank_hello_world.py`

```python
from crank.worker_runtime import WorkerApplication
import os

class MyWorker(WorkerApplication):
    """Worker with automatic HTTPS+mTLS security."""
    
    def __init__(
        self,
        worker_id: str | None = None,
        service_name: str | None = None,
        https_port: int = 8500
    ):
        """Initialize worker.
        
        Args:
            worker_id: Unique worker identifier (auto-generated if None)
            service_name: Service name for registration (default: my-service)
            https_port: HTTPS port for this worker
        """
        super().__init__(
            worker_id=worker_id,
            service_name=service_name or "my-service",
            https_port=https_port
        )
        
        # Setup your routes
        async def health_handler() -> JSONResponse:
            return JSONResponse({"status": "healthy"})
        
        self.app.get("/health")(health_handler)

def main() -> None:
    """Main entry point - sync function, not async."""
    port = int(os.getenv("MY_WORKER_HTTPS_PORT", "8500"))
    worker = MyWorker(https_port=port)
    worker.run()  # Handles SSL, certificates, uvicorn automatically

if __name__ == "__main__":
    main()
```

## Key Requirements

### 1. Worker Class Must Inherit from WorkerApplication

```python
from crank.worker_runtime import WorkerApplication

class MyWorker(WorkerApplication):  # ✅ Correct
    pass

class BadWorker:  # ❌ Missing base class - no security
    pass
```

### 2. Constructor Must Accept https_port Parameter

```python
def __init__(self, https_port: int = 8500):  # ✅ Required
    super().__init__(
        service_name="my-service",
        https_port=https_port  # Pass to parent
    )

def __init__(self):  # ❌ Missing https_port
    super().__init__(service_name="my-service")
```

### 3. Main Function Must Be Sync

```python
def main() -> None:  # ✅ Sync function
    worker = MyWorker()
    worker.run()

async def main() -> None:  # ❌ Async causes issues
    worker = MyWorker()
    await worker.run()  # Wrong pattern
```

### 4. Call worker.run() - Never Configure Uvicorn Manually

```python
# ✅ CORRECT: Use worker.run()
def main() -> None:
    worker = MyWorker(https_port=8500)
    worker.run()  # Automatic SSL, certificates, everything

# ❌ WRONG: Manual uvicorn bypasses security
def main() -> None:
    worker = MyWorker()
    import uvicorn
    uvicorn.run(worker.app, host="0.0.0.0", port=8500)
```

## What worker.run() Does For You

The `WorkerApplication.run()` method (from `src/crank/worker_runtime/application.py`) automatically:

1. **Certificate Bootstrap**: Checks for existing certificate, generates CSR if needed
2. **CA Registration**: Sends CSR to certificate authority on port 9090
3. **Certificate Storage**: Saves signed certificate to appropriate location
4. **Path Detection**: Auto-detects container vs native execution environment
5. **SSL Configuration**: Configures uvicorn with correct cert/key paths
6. **HTTPS Server**: Starts uvicorn with SSL on specified port
7. **Heartbeat Registration**: Registers with platform and sends periodic heartbeats

You write **3 lines of code** and get production-grade security.

## Certificate Path Detection

The security module automatically detects the best certificate directory:

1. `CERT_DIR` environment variable (highest priority)
2. `/etc/certs` if writable (for containers with proper permissions)
3. `/etc/certs` fallback (containers with root bootstrap)
4. `~/.crank/certs` (native execution on macOS/Linux)

No manual configuration needed - works in containers and native execution.

## Docker Integration

**Dockerfile Pattern**:

```dockerfile
FROM crank-worker-base:latest

# Copy worker code with correct ownership
COPY --chown=worker:worker requirements-my-worker.txt /app/
COPY --chown=worker:worker services/crank_my_worker.py /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements-my-worker.txt

# Bootstrap certificates then start worker
CMD python3 /app/crank_cert_initialize.py && \
    python3 -c "import crank_my_worker; crank_my_worker.main()"
```

**docker-compose.yml**:

```yaml
my-worker:
  build:
    context: .
    dockerfile: services/Dockerfile.crank-my-worker
  environment:
    - MY_WORKER_HTTPS_PORT=8500
    - HTTPS_ONLY=true
    - CERT_DIR=/etc/certs
  ports:
    - "8500:8500"
  volumes:
    - certs:/etc/certs
  healthcheck:
    test: ["CMD", "curl", "-f", "-k", "https://localhost:8500/health"]
    interval: 10s
    timeout: 5s
    retries: 3
```

## Common Pitfalls and Solutions

### Issue: Worker Runs HTTP Instead of HTTPS

**Symptom**: Health checks fail, `curl http://localhost:8500/health` works but HTTPS doesn't

**Cause**: Not using `worker.run()` method

**Solution**:
```python
# ✅ Use worker.run()
def main() -> None:
    worker = MyWorker(https_port=8500)
    worker.run()

# ❌ Don't configure uvicorn manually
uvicorn.run(worker.app, host="0.0.0.0", port=8500)
```

### Issue: Worker Unhealthy in Docker

**Symptom**: Container starts but health check fails with connection refused

**Causes & Solutions**:

1. **Async main function**:
   ```python
   # ❌ Wrong
   async def main() -> None:
       worker = MyWorker()
       worker.run()
   
   # ✅ Correct
   def main() -> None:
       worker = MyWorker()
       worker.run()
   ```

2. **Missing https_port parameter**:
   ```python
   # ❌ Wrong - worker doesn't know port
   worker = MyWorker()
   
   # ✅ Correct - pass port from environment
   port = int(os.getenv("MY_WORKER_HTTPS_PORT", "8500"))
   worker = MyWorker(https_port=port)
   ```

3. **Permission denied** (Docker v28+):
   ```dockerfile
   # ❌ Wrong - files owned by root
   COPY requirements.txt /app/
   
   # ✅ Correct - proper ownership
   COPY --chown=worker:worker requirements.txt /app/
   ```

### Issue: 422 Heartbeat Errors

**Symptom**: Worker starts but shows "422 Unprocessable Entity" in logs

**Cause**: Platform expects form data (service_type, load_score) in heartbeat POST

**Solution**: This is handled automatically by `WorkerApplication.run()` - if you see this error, you're likely not using the base class correctly.

## Testing Your Worker

### Local Testing (Native)

```bash
# Install in development mode
uv pip install -e .

# Set environment variables
export MY_WORKER_HTTPS_PORT=8500
export HTTPS_ONLY=true

# Run worker
python services/crank_my_worker.py

# Test health endpoint (in another terminal)
curl -k https://localhost:8500/health
```

### Docker Testing

```bash
# Build and start
docker-compose -f docker-compose.development.yml up --build my-worker

# Check health
docker-compose ps my-worker  # Should show "healthy"

# View logs
docker-compose logs -f my-worker

# Test endpoint
curl -k https://localhost:8500/health
```

### Verify HTTPS+mTLS

```bash
# Check certificate
openssl s_client -connect localhost:8500 -showcerts

# Should show:
# - Certificate from Crank CA
# - Subject: CN=my-worker
# - SSL handshake successful
```

## Migration Checklist

Migrating an existing worker to unified security:

- [ ] Worker class inherits from `WorkerApplication`
- [ ] Constructor accepts `https_port` parameter
- [ ] Constructor passes `https_port` to `super().__init__()`
- [ ] `main()` function is sync (not async)
- [ ] `main()` reads port from environment variable
- [ ] `main()` creates worker with `https_port=port`
- [ ] `main()` calls `worker.run()` (not manual uvicorn)
- [ ] Dockerfile uses `--chown=worker:worker` on all COPY commands
- [ ] Dockerfile CMD bootstraps certificates then calls `main()`
- [ ] docker-compose sets `HTTPS_PORT` environment variable
- [ ] docker-compose health check uses HTTPS endpoint
- [ ] Requirements include `aiohttp` for async HTTP client
- [ ] Remove any manual SSL/certificate configuration code

## Architecture Reference

For complete architecture documentation:
- **Controller/Worker Model**: `docs/architecture/controller-worker-model.md`
- **Security Module Code**: `src/crank/security/`
- **Worker Runtime Code**: `src/crank/worker_runtime/`
- **Example Workers**: `services/crank_*.py` (all 9 workers use this pattern)

## Troubleshooting

See main troubleshooting guide in `.github/copilot-instructions.md` for:
- Import errors
- Type checking issues
- Docker permission errors
- Certificate initialization failures

## History

- **Nov 15, 2025**: Issue #19 completed - all 9 workers using unified security
- **Nov 10, 2025**: Phase 0-2 complete - worker runtime foundation
- **Pattern established**: 3-line main function with automatic HTTPS+mTLS
- **Code removed**: 675 lines of duplicated security configuration
- **Result**: Clean, maintainable, consistent security across all workers
