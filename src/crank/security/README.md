# Crank Security Module

Unified security module for certificate management and mTLS across all Crank Platform services.

## Quick Start

### Production (Docker/Kubernetes)

Certificates are mounted at `/etc/certs` (default). No environment variables needed.

```python
from crank.security import initialize_worker_certificates, create_mtls_client

# Bootstrap certificates from CA service
cert, key, ca = await initialize_worker_certificates("streaming-worker-1")

# Create mTLS-enabled HTTP client
client = create_mtls_client()
async with client.get("https://platform:8443/health") as response:
    data = await response.json()
```

### Development (Local)

Set `CERT_DIR=./certs` for user-writable certificate storage:

```bash
# Option 1: Export in your shell
export CERT_DIR=./certs
python scripts/initialize-certificates.py

# Option 2: Use helper script
source scripts/dev-setup-certs.sh
python scripts/initialize-certificates.py

# Option 3: Set inline
CERT_DIR=./certs python scripts/initialize-certificates.py
```

Then use the same `CERT_DIR` when running workers:

```bash
CERT_DIR=./certs python services/crank_streaming.py
```

## Architecture

### Certificate Paths

**Production Default:** `/etc/certs`
- Stable absolute path
- Works across all contexts (repo root, workers, containers)
- Matches Docker volume mounts in `docker-compose.*.yml`
- Matches Kubernetes ConfigMap/Secret mounts

**Development Override:** `CERT_DIR=./certs`
- User-writable without root
- Relative to project root
- Must be consistent across bootstrap and runtime

### Module Structure

```
src/crank/security/
├── __init__.py           # Public API exports
├── certificates.py       # CertificateManager, CertificateBundle
├── config.py            # SecurityConfig (environment-aware)
├── constants.py         # DEFAULT_CERT_DIR, cert filenames
├── events.py            # Certificate lifecycle events
├── initialization.py    # CSR-based bootstrap from CA
├── mtls_client.py       # HTTPS-only mTLS client factory
└── README.md           # This file
```

### Certificate Files

All workers use standardized filenames in `CERT_DIR`:

- `client.crt` - Worker certificate (signed by CA)
- `client.key` - Worker private key (never transmitted)
- `ca.crt` - CA root certificate (for verification)

## Usage Patterns

### Worker Bootstrap (CSR-based)

```python
from crank.security import initialize_worker_certificates

# Generate local key pair, submit CSR to CA, receive signed cert
cert_file, key_file, ca_file = await initialize_worker_certificates(
    worker_id="streaming-worker-1",
    ca_service_url="https://cert-authority:9090",  # Optional, defaults from env
    additional_san_names=["streaming.local"],       # Optional SANs
)

# Certificates written to CERT_DIR/{client.crt, client.key, ca.crt}
```

### Certificate Loading (Runtime)

```python
from crank.security import CertificateManager

manager = CertificateManager("streaming-worker-1")

# Check if certificates exist
if not manager.certificates_exist():
    raise RuntimeError("Certificates not initialized")

# Get validated certificate bundle
bundle = manager.ensure_certificates()

# Use for uvicorn HTTPS server
ssl_config = bundle.to_uvicorn_config()
uvicorn.run(app, **ssl_config)
```

### mTLS HTTP Client

```python
from crank.security import create_mtls_client

# HTTPS-only client with automatic mTLS
async with create_mtls_client() as client:
    async with client.get("https://platform:8443/health") as response:
        assert response.status == 200
```

### Observability

```python
from crank.security import CertificateEvent, emit_certificate_event, register_event_handler

# Custom event handler
def log_cert_event(event: CertificateEvent, context: dict):
    print(f"Certificate event: {event.value} - {context}")

register_event_handler(log_cert_event)

# Events emitted automatically during bootstrap:
# - CSR_GENERATED (with san_names metadata)
# - CSR_SUBMITTED
# - CERT_ISSUED (after files persisted)
# - CA_UNAVAILABLE (on retry failures)
# - CSR_FAILED (on terminal failures with phase/CA context)
```

## Migration from Old Security Modules

### Before (Scattered)

```python
# Old: services/security_config.py
from security_config import CertificateManager  # ❌ Deprecated

# Old: src/crank_platform/security/
from crank_platform.security import initialize_certificates  # ❌ Deprecated

# Old: src/crank/worker_runtime/security.py
from crank.worker_runtime.security import SecurityConfig  # ❌ Deprecated
```

### After (Unified)

```python
# New: src/crank/security/
from crank.security import (
    initialize_worker_certificates,  # ✅ Bootstrap
    CertificateManager,              # ✅ Runtime loading
    create_mtls_client,              # ✅ mTLS client
    CertificateEvent,                # ✅ Observability
)
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CERT_DIR` | `/etc/certs` | Certificate directory (use `./certs` for dev) |
| `CA_SERVICE_URL` | `https://cert-authority:9090` | Certificate Authority endpoint |
| `CRANK_ENVIRONMENT` | `development` | Environment name (for logging) |

## Security Guarantees

- ✅ **HTTPS/mTLS Only** - No HTTP fallback exists
- ✅ **Private Keys Local** - Generated locally, never transmitted
- ✅ **CSR-based Provisioning** - Only public key sent to CA
- ✅ **Certificate Verification** - All connections verify against CA cert
- ✅ **Retry Logic** - Exponential backoff for transient failures
- ✅ **Async-Safe** - RSA generation in thread pool
- ✅ **Observability** - Structured events for all lifecycle stages

## Troubleshooting

### PermissionError: Cannot create /etc/certs

**Development:** Set `CERT_DIR=./certs`

```bash
export CERT_DIR=./certs
python scripts/initialize-certificates.py
```

**Production:** Ensure Docker mounts or Kubernetes volumes are configured

### FileNotFoundError: Certificates not found

**Mismatch between bootstrap and runtime:**

```bash
# Ensure same CERT_DIR for both
export CERT_DIR=./certs
python scripts/initialize-certificates.py  # Bootstrap
CERT_DIR=./certs python services/crank_streaming.py  # Runtime
```

### CA Service Unavailable

Check CA service health:

```bash
curl -k https://cert-authority:9090/health
```

Bootstrap includes retry logic (3 attempts, exponential backoff).

## Related Documentation

- Architecture: `docs/architecture/security-module-consolidation.md`
- Enterprise Security: `docs/security/enterprise-security.md`
- Certificate Operations: `docs/operations/certificate-management.md`
