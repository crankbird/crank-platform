# Security Module Consolidation Architecture

**Issue**: #19 - Security Configuration Scattered
**Status**: In Progress
**Sprint**: Sprint 1 (Foundation)
**Priority**: Critical (Blocks #30 Controller Extraction)

## Problem Statement

Security and certificate management is currently fragmented across 4 locations:

1. **`services/security_config.py`** (430 lines)
   - Legacy location from pre-controller-refactor era
   - Contains: `SecurityConfig`, `AdaptiveSecurityConfig`, `ResilientCertificateManager`
   - Used by: `crank_image_classifier_advanced.py` only
   - Issues: Wrong location, duplicates functionality

2. **`src/crank/worker_runtime/security.py`** (211 lines)
   - Modern worker-focused certificate management
   - Contains: `CertificateManager`, `CertificateBundle`
   - Purpose: Workers retrieve certs from controller (correct architecture)
   - Issues: Limited to workers, doesn't handle initialization

3. **`src/crank_platform/security/`** (3 files)
   - `cert_initialize.py` (368 lines): CSR-based cert initialization
   - `cert_worker_pattern.py` (153 lines): Worker convenience wrapper
   - `__init__.py`: Public API exports
   - Purpose: Secure certificate provisioning from CA service
   - Issues: Different namespace (`crank_platform` vs `crank`), overlaps with worker_runtime

4. **`scripts/initialize-certificates.py`** (148 lines)
   - Standalone CLI certificate initialization script
   - Duplicates logic from `cert_initialize.py`
   - Used in Docker entrypoints and manual initialization

### Critical Issues

- **No single source of truth** for security configuration
- **Namespace confusion**: `crank_platform.security` vs `crank.worker_runtime.security`
- **Duplicated logic**: Certificate generation in 3+ places
- **Import chaos**: Workers don't know which security module to import
- **Architecture misalignment**: Pre-controller code mixed with new worker patterns

## Proposed Architecture

### Unified Module: `src/crank/security/`

Consolidate all security concerns into single authoritative module with clear separation:

```
src/crank/security/
├── __init__.py                 # Public API exports
├── certificates.py             # Certificate lifecycle management
├── mtls_client.py              # HTTP client factory with mTLS
├── config.py                   # Environment-aware security settings
├── initialization.py           # Certificate initialization patterns
└── constants.py                # Security constants (paths, timeouts)
```

### Module Responsibilities

#### `certificates.py` - Certificate Lifecycle

**Purpose**: Core certificate management for all components with observability and policy hooks

```python
from crank.security import CertificateManager, CertificateBundle, CertificateEvent

# Worker usage
cert_mgr = CertificateManager(worker_id="streaming")
bundle = cert_mgr.ensure_certificates()
ssl_config = bundle.to_uvicorn_config()

# Controller usage (CA privileges)
ca_mgr = CertificateAuthorityManager(cert_dir="/etc/certs")
ca_mgr.generate_ca_certificate()
ca_mgr.sign_worker_certificate(csr_pem)

# Observability hook registration
cert_mgr.on_event(CertificateEvent.EXPIRING_SOON, lambda cert: alert_ops(cert))
```

**Classes**:

- `CertificateBundle`: Validated cert/key/ca bundle (from worker_runtime)
- `CertificateManager`: Worker cert management (from worker_runtime)
- `CertificateAuthorityManager`: Controller-only CA operations (new)
- `CertificateInitializer`: CSR-based initialization (from cert_initialize)
- `CertificateEvent`: Observable events enum (new)

**Certificate Events** (for observability/metrics):

- `CERT_ISSUED`: New certificate successfully obtained
- `CERT_RENEWED`: Existing certificate renewed before expiry
- `CERT_EXPIRING_SOON`: Certificate within renewal window (default: 30 days)
- `CERT_EXPIRED`: Certificate has expired
- `CERT_REVOKED`: Certificate was revoked
- `CERT_VALIDATION_FAILED`: Certificate failed validation checks
- `CSR_GENERATED`: Certificate Signing Request created
- `CSR_SUBMITTED`: CSR sent to CA service
- `CSR_FAILED`: CSR rejected by CA service

**Metrics** (exposed for Prometheus/OpenTelemetry):

- `crank_cert_expiration_seconds`: Histogram of certificate expiration times
- `crank_cert_issuance_total`: Counter of certificates issued
- `crank_cert_renewal_total`: Counter of successful renewals
- `crank_cert_errors_total`: Counter of certificate errors by type
- `crank_ca_unavailable_total`: Counter of CA service unavailability

**Policy Integration Points** (for future OPA/CAP):

- `can_issue_certificate(worker_id, capabilities)`: Policy decision for cert issuance
- `certificate_validity_period(worker_id, environment)`: Policy-driven TTL
- `should_renew_certificate(cert_metadata)`: Policy-driven renewal timing
- `revoke_certificate(worker_id, reason)`: Policy-enforced revocation

**Note**: Policy hooks are defined but currently use default implementations.
Full OPA/CAP integration planned for Enterprise Security Phase 2 (Q2 2026).

#### `mtls_client.py` - mTLS-Only HTTP Client Factory

**Purpose**: Create HTTPS clients with mandatory mTLS - **NO HTTP CAPABILITY**

```python
from crank.security import create_mtls_client

# All clients require valid certificates - fail fast if unavailable
async with create_mtls_client(cert_dir="/etc/certs") as client:
    response = await client.post(worker_url, json=data)

# Certificate validation is ALWAYS enforced
async with create_mtls_client(ca_cert_path="/etc/certs/ca.crt") as client:
    response = await client.get(platform_url)
```

**Functions**:

- `create_mtls_client()`: Factory for httpx.AsyncClient with **mandatory** mTLS
- `verify_certificate_chain()`: Validate complete cert chain exists
- `get_cert_expiration()`: Check certificate validity periods

**Guarantees**:

- ✅ All connections use HTTPS with mTLS
- ✅ Certificate verification always enabled
- ✅ Fails fast if certificates missing or invalid
- ✅ No `verify=False` anti-pattern
- ✅ No HTTP fallback under any circumstances

#### `config.py` - Environment Configuration

**Purpose**: Centralized security configuration - **HTTPS-only enforced**

```python
from crank.security import SecurityConfig, get_security_config

# Global config (singleton pattern)
config = get_security_config()
print(config.environment)  # "development" | "production"
print(config.cert_dir)     # Path("/etc/certs")
print(config.require_mtls)  # Always True - no exceptions
```

**Classes**:

- `SecurityConfig`: HTTPS-only environment settings
- `CertificatePaths`: Standard cert file locations
- `CAServiceConfig`: Certificate Authority Service connection settings

**Enforced Policies**:

- ✅ `HTTPS_ONLY=true` always (no override)
- ✅ `require_mtls=True` always
- ✅ `verify_certificates=True` always
- ✅ No development-specific security relaxation

#### `initialization.py` - Setup Patterns

**Purpose**: Certificate initialization for different components

```python
from crank.security import initialize_worker_certificates, initialize_controller_certificates

# Worker initialization (CSR-based)
await initialize_worker_certificates(
    worker_id="streaming",
    ca_service_url="https://cert-authority:9090"
)

# Controller initialization (CA generation)
await initialize_controller_certificates(
    cert_dir="/etc/certs",
    environment="production"
)
```

**Functions**:

- `initialize_worker_certificates()`: CSR-based cert retrieval
- `initialize_controller_certificates()`: CA + cert generation
- `wait_for_ca_service()`: Retry logic for CA availability
- `generate_csr()`: Local CSR generation (private key never leaves)

### Migration Path

#### Phase 1: Create Unified Module ✅

1. Create `src/crank/security/` directory
2. Migrate `CertificateManager`, `CertificateBundle` from `worker_runtime/security.py`
3. Migrate initialization logic from `crank_platform/security/cert_initialize.py`
4. Add mTLS client factory from `services/security_config.py`
5. Add environment config from `services/security_config.py`

#### Phase 2: Update Workers

1. Update `services/crank_streaming.py` imports
2. Update `services/crank_image_classifier_advanced.py` imports
3. Update future workers to use new module

#### Phase 3: Deprecate Old Locations

1. Add deprecation warnings to `services/security_config.py`
2. Add deprecation warnings to `src/crank_platform/security/`
3. Keep `worker_runtime/security.py` as thin wrapper (re-exports from `crank.security`)
4. Update `scripts/initialize-certificates.py` to call `crank.security.initialization`

#### Phase 4: Controller Extraction Integration (Issue #30)

1. Controller uses `CertificateAuthorityManager` (CA privileges)
2. Workers use `CertificateManager` (no CA privileges)
3. Clear security boundary enforced by module API

## Implementation Plan

### Step 1: Create Module Structure (30 min)

```bash
mkdir -p src/crank/security
touch src/crank/security/{__init__.py,certificates.py,mtls_client.py,config.py,initialization.py,constants.py}
```

### Step 2: Migrate Core Types (1 hour)

Copy and refactor:

- `CertificateBundle` → `certificates.py`
- `CertificateManager` → `certificates.py`
- `SecurityConfig` → `config.py`
- `SecurityLevel` (new enum) → `config.py`

### Step 3: Consolidate Initialization (1 hour)

Merge logic from:

- `src/crank_platform/security/cert_initialize.py`
- `scripts/initialize-certificates.py`

Into: `initialization.py` with clear worker vs controller paths

### Step 4: Create mTLS Client Factory (45 min)

**Extract ONLY the mTLS functionality**, removing all HTTP fallback:

From `services/security_config.py`:
- Extract `create_secure_http_client()` mTLS path → `create_mtls_client()`
- **Remove**: `verify=False` branches
- **Remove**: "development-https" vs "production" split
- **Remove**: Optional certificate verification
- **Remove**: HTTP fallback logic

Result: Single mTLS-only client factory with mandatory certificate verification

### Step 5: Update Worker Imports (30 min)

Update all workers:

```python
# OLD (scattered)
from security_config import initialize_security
from crank.worker_runtime.security import CertificateManager
from crank_platform.security import WorkerCertificatePattern

# NEW (unified)
from crank.security import (
    CertificateManager,
    initialize_worker_certificates,
    create_mtls_client,
)
```

### Step 6: Add Deprecation Warnings (15 min)

```python
# services/security_config.py
import warnings

warnings.warn(
    "services/security_config.py is deprecated. "
    "Use 'from crank.security import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)
```

### Step 7: Update Documentation (30 min)

- Update `.github/copilot-instructions.md`
- Update architecture docs
- Create migration guide in docs/development/

### Step 8: Test Everything (1 hour)

- Unit tests for certificate management
- Integration tests for mTLS client
- Worker startup tests
- Certificate generation tests

**Total Estimated Time**: ~6 hours (fits 2-3 day sprint estimate)

## Security Guarantees

### Preserved from Current Implementation

- ✅ **HTTPS-only architecture**: No HTTP fallback capability anywhere
- ✅ **Private keys never transmitted** over network
- ✅ **CSR-based certificate provisioning**: Private keys generated locally
- ✅ **mTLS everywhere**: All service-to-service communication uses mutual TLS
- ✅ **Certificate Authority Service**: Centralized cert management
- ✅ **Certificate validation**: Health checks for cert infrastructure
- ✅ **Zero-trust principles**: Certificate verification required

### New Guarantees

- ✅ **Single source of truth** for security configuration
- ✅ **Clear privilege separation**: Workers vs controller CA operations
- ✅ **Consistent import patterns** across codebase
- ✅ **Type-safe certificate handling**
- ✅ **No legacy HTTP code paths**: Removes all HTTP fallback logic
- ✅ **Explicit security failure**: Fail fast if certificates unavailable

### Removed Anti-Patterns

- ❌ `verify=False` HTTP clients (from legacy security_config.py)
- ❌ HTTP fallback modes (development, development-https split)
- ❌ "Graceful degradation" to insecure connections
- ❌ Optional certificate verification
- ❌ Mixed HTTP/HTTPS endpoint support

### Certificate Authority Strategy

**Local CA is authoritative for all mesh communications** (development AND production):

- **Development**: Local CA generates self-signed root (bootstrap trust)
- **Production**: Local CA uses externally-signed root from established PKI
- **Lock-in avoidance**: Mesh identity is Crank-defined, not provider-defined
- **Edge providers** (Cloudflare, etc.): Public ingress only, NOT mesh identity
- **Certificate lifecycle**: Fully managed by Crank CA service and controller agents

This ensures:
- ✅ Switching edge providers requires no internal mesh changes
- ✅ All certificate flows testable with local fixtures
- ✅ External providers are replaceable adapters, not sources of trust
- ✅ Mesh security independent of vendor lock-in

## Certificate Lifecycle & Failure Modes

### Normal Operation Flow

1. **Worker Startup**:
   - Check for existing valid certificates
   - If missing/invalid: Generate CSR locally (private key never leaves)
   - Submit CSR to CA service
   - Receive signed certificate
   - Emit `CERT_ISSUED` event
   - Start service with mTLS

2. **Ongoing Operation**:
   - Background task monitors certificate expiration
   - When < 30 days remaining: Emit `CERT_EXPIRING_SOON` event
   - When < 7 days remaining: Attempt automatic renewal
   - Successful renewal: Emit `CERT_RENEWED` event
   - Failed renewal: Emit `CERT_VALIDATION_FAILED` event, alert operators

### Failure Modes & Recovery

#### Scenario 1: Worker starts with invalid/missing certificates

**Behavior**:

```python
# certificates.py implementation
def ensure_certificates() -> CertificateBundle:
    if not self.certificates_exist() or not self.certificates_valid():
        logger.warning("Certificates invalid, initiating CSR flow")
        success = await self.request_new_certificate()
        if not success:
            raise CertificateUnavailableError(
                "Cannot start without valid certificates. "
                "CA service unavailable or CSR rejected."
            )
    return self.load_certificate_bundle()
```

**Recovery**: Worker fails fast and logs clear error. External orchestration (Docker, K8s) restarts worker after CA service is available.

#### Scenario 2: CA service temporarily unavailable

**Behavior**:
- Workers with valid certs: Continue operating normally
- Workers needing renewal: Retry with exponential backoff (1s, 2s, 4s, 8s... max 60s)
- New workers: Fail to start (see Scenario 1)
- Emit `crank_ca_unavailable_total` metric

**Recovery**: CA service comes back online, pending renewals complete automatically.

#### Scenario 3: Certificate near expiration (< 30 days)

**Behavior**:

```python
# Background task in worker runtime
async def monitor_certificate_expiration():
    while True:
        days_remaining = cert_mgr.days_until_expiration()

        if days_remaining < 30:
            emit_event(CertificateEvent.EXPIRING_SOON, cert_metadata)

        if days_remaining < 7:
            logger.warning(f"Certificate expiring in {days_remaining} days, renewing...")
            await cert_mgr.renew_certificate()

        await asyncio.sleep(3600)  # Check hourly
```

**Recovery**: Automatic renewal via CSR process. If renewal fails, continue with existing cert and alert operators.

#### Scenario 4: Certificate expires during operation

**Behavior**:
- Service continues running (doesn't crash)
- New mTLS connections rejected by peers (handshake failure)
- Existing connections may continue (depends on peer validation)
- Emit `CERT_EXPIRED` event
- Alert operators with CRITICAL severity

**Recovery**: Manual intervention required if automatic renewal failed. Operator investigates CA service logs, policy rejections, or network issues.

#### Scenario 5: Certificate revoked (future - post OPA/CAP integration)

**Behavior**:
- CA service notifies mesh of revocation
- Controller updates CRL (Certificate Revocation List)
- Worker receives revocation notice
- Worker immediately requests new certificate
- Emit `CERT_REVOKED` event

**Recovery**: Automatic re-issuance if policy allows. If policy blocks (e.g., compromised worker), manual intervention required.

### Observability Requirements

All certificate lifecycle events MUST include:

- **Correlation ID**: Trace request across CA service, controller, worker
- **Worker ID**: Identity of requesting component
- **Timestamp**: ISO8601 format with timezone
- **Certificate Metadata**: Expiration, issuer, subject, serial number
- **Error Context**: If failure, include CA service response, policy decision, network error

**Logging Example**:

```json
{
  "event": "CERT_EXPIRING_SOON",
  "correlation_id": "req_abc123",
  "worker_id": "streaming-worker-1",
  "timestamp": "2026-01-15T14:30:00Z",
  "cert_metadata": {
    "expires_at": "2026-02-10T00:00:00Z",
    "days_remaining": 25,
    "serial": "4a:3b:2c:1d",
    "issuer": "CN=Crank Platform CA"
  }
}
```

## Success Criteria

- [ ] All security code consolidated into `src/crank/security/`
- [ ] All workers use unified imports
- [ ] Deprecation warnings in place for old locations
- [ ] No regression in security functionality
- [ ] Tests passing with new module
- [ ] Documentation updated
- [ ] **Certificate events defined and logged**
- [ ] **Metrics exported for Prometheus**
- [ ] **Policy hooks documented (implementation in Phase 2)**
- [ ] **Failure modes tested and documented**

## Blocked Issues

This consolidation **unblocks**:

- **Issue #30**: Controller extraction (needs clear CA privilege boundary)
- **Enterprise Security Proposal**: Phase 1 prerequisites (unified security config)
- **Worker Migration**: Clear pattern for external worker repos

## Related Work Required

### Secure Observability Infrastructure (Not Yet Proposed)

The certificate lifecycle events and metrics defined in this consolidation require
a **secure observability infrastructure**. Current gap:

- ✅ Certificate events defined (CERT_ISSUED, CERT_EXPIRING_SOON, etc.)
- ✅ Metrics schema specified (Prometheus format)
- ✅ Structured logging with correlation IDs
- ❌ **Missing**: Secure telemetry collection infrastructure
- ❌ **Missing**: mTLS-authenticated Prometheus endpoints
- ❌ **Missing**: Encrypted log shipping
- ❌ **Missing**: RBAC for observability data access

**Action**: Create "Secure Observability" proposal covering:
1. Zero-trust telemetry architecture (mTLS for all collection)
2. Certificate-based auth for metrics exporters
3. Encrypted log aggregation with integrity verification
4. RBAC for Grafana/log viewer access
5. Audit trail for observability system changes

**Cross-Reference**: Enterprise Security Proposal Section 8 updated with this requirement.

## References

- Issue #19: Security Configuration Scattered
- Issue #30: Phase 3 Controller Extraction
- `docs/proposals/enterprise-security.md`: Q1-Q3 2026 security roadmap
- `docs/architecture/controller-worker-model.md`: Privilege separation
