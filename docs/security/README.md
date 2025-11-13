# Security Documentation

**Owner**: Wendy the Zero Security Bunny 🐰
**Last Updated**: 2025-11-10
**Purpose**: Navigation hub for Crank Platform security architecture

---

## 🎯 Current Security Strategy (AS-IS)

The Crank Platform implements **zero-trust mTLS architecture** with:

- **Centralized Certificate Authority**: Single source of truth for all certificates
- **Synchronous Certificate Loading**: Eliminates async timing issues
- **Non-root Containers**: All services run as `worker:1000`
- **HTTPS-only**: No HTTP fallbacks in production
- **Container Security**: Slim images, non-root users, minimal attack surface

## 📖 Active Documentation

### Core Architecture

**[DOCKER_SECURITY_DECISIONS.md](DOCKER_SECURITY_DECISIONS.md)** ⭐ **CRITICAL**
- **Type**: Active Design Documentation
- **Purpose**: Complete container security posture for technical review
- **Sections**: Base images, non-root execution, certificate strategy, CAP design
- **Use when**: Understanding security decisions, reviewing security posture, onboarding security reviewers

**[CERTIFICATE_AUTHORITY_ARCHITECTURE.md](CERTIFICATE_AUTHORITY_ARCHITECTURE.md)**
- **Type**: Architecture (AS-IS)
- **Purpose**: Centralized enterprise-grade certificate management
- **Sections**: CA service design, pluggable providers, enterprise integration
- **Use when**: Understanding certificate lifecycle, integrating enterprise PKI, troubleshooting mTLS

**[WORKER_CERTIFICATE_PATTERN.md](WORKER_CERTIFICATE_PATTERN.md)**
- **Type**: Implementation Pattern (AS-IS)
- **Purpose**: Synchronous certificate loading pattern for worker services
- **Sections**: Problem solved, correct vs incorrect patterns, implementation steps
- **Use when**: Implementing new worker services, debugging certificate timing issues

### Future Enhancements

**[CAPABILITY_ACCESS_POLICY_ARCHITECTURE.md](CAPABILITY_ACCESS_POLICY_ARCHITECTURE.md)**
- **Type**: Future Enhancement (Q2-Q3 2026)
- **Purpose**: Platform-level caller authorization design
- **Timeline**: Q2 2026 (design), Q3 2026 (implementation), Q4 2026 (production)
- **Use when**: Planning CAP implementation, understanding future security roadmap

## 🏛️ Security Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Capability Access Policy (CAP)                     │
│ Status: PLANNED (Q2-Q4 2026)                                │
│ Purpose: Platform-level caller authorization                │
└─────────────────────────────────────────────────────────────┘
                           ▲
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: mTLS Certificate Authentication                    │
│ Status: ACTIVE                                              │
│ Pattern: Worker Certificate Pattern                         │
│ Provider: Certificate Authority Service                     │
└─────────────────────────────────────────────────────────────┘
                           ▲
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Container Isolation                                │
│ Status: ACTIVE                                              │
│ Strategy: Non-root users (worker:1000), slim images         │
└─────────────────────────────────────────────────────────────┘
                           ▲
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Network Isolation                                  │
│ Status: ACTIVE                                              │
│ Strategy: Docker networks, HTTPS-only                       │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Implementation Patterns

### Current Worker Service Security Pattern

```python
from worker_cert_pattern import WorkerCertificatePattern, create_worker_fastapi_with_certs

def main():
    # Step 1: Initialize certificates SYNCHRONOUSLY
    cert_pattern = WorkerCertificatePattern("crank-service-name")
    cert_store = cert_pattern.initialize_certificates()

    # Step 2: Create FastAPI with pre-loaded certificates
    worker_config = create_worker_fastapi_with_certs(
        title="Service Title",
        service_name="crank-service-name",
        cert_store=cert_store
    )

    # Step 3: Start server
    cert_pattern.start_server(worker_config.app, port=8XXX)
```

**Key Principle**: Certificates loaded BEFORE FastAPI startup eliminates async timing issues.

### Certificate Authority Integration

```python
# Development: Self-signed certificates
CERTIFICATE_PROVIDER = "development"

# Production options (future):
# CERTIFICATE_PROVIDER = "azure_keyvault"
# CERTIFICATE_PROVIDER = "hashicorp_vault"
# CERTIFICATE_PROVIDER = "adcs"  # Active Directory Certificate Services
```

## 📊 Security Metrics & Results

**Worker Migration Results** (see [reports/WORKER_MIGRATION_COMPLETE.md](../reports/WORKER_MIGRATION_COMPLETE.md)):
- ✅ 6/6 workers migrated to standardized pattern
- ✅ 837 lines of code eliminated
- ✅ Zero SSL timing warnings
- ✅ 21.4% code reduction average

**Security Improvements**:
- ✅ All services run as non-root (`worker:1000`)
- ✅ All inter-service communication uses mTLS
- ✅ Centralized certificate lifecycle management
- ✅ No HTTP fallbacks in production

## 🗄️ Historical Documentation

Historical reports and superseded strategies are archived in:

**[../reports/](../reports/)** — Completed migration reports
- `WORKER_MIGRATION_COMPLETE.md` — Worker certificate migration results
- `CERTIFICATE_SOLUTION_SUMMARY.md` — Original CA service implementation summary

**[../archive/security/](../archive/security/)** — Superseded strategies
- `MTLS_RESILIENCE_STRATEGY.md` — Superseded by Worker Certificate Pattern
- `anti-fragile-mtls-strategy.md` — Duplicate of above
- `docker-security-guide.md` — Superseded by DOCKER_SECURITY_DECISIONS.md

## 🚀 Next Steps

### Immediate (Current)
- Monitor certificate expiration
- Maintain security quality gate (Trivy, gitleaks, hadolint)
- Continue using Worker Certificate Pattern for new services

### Q1 2026 (Planned)
- Implement SLOs for security operations
- Add rate limiting per capability
- Implement back-pressure handling

### Q2-Q4 2026 (Future)
- Design Capability Access Policy (CAP) architecture
- Implement CAP enforcement layer
- Deploy CAP to production with monitoring

## 🐰 Wendy's Security Principles

1. **Zero Trust**: Never trust, always verify (mTLS everywhere)
2. **Least Privilege**: Services run as non-root, minimal permissions
3. **Defense in Depth**: Multiple security layers (network, container, mTLS, CAP)
4. **Fail Secure**: Certificate failures = hard failures, no degradation
5. **Auditability**: All certificate operations logged and traceable

---

**Questions?** See [DOCKER_SECURITY_DECISIONS.md](DOCKER_SECURITY_DECISIONS.md) for comprehensive security architecture or ping Wendy 🐰 for security reviews.
