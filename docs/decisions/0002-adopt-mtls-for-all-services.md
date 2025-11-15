# ADR-0002: Adopt mTLS for All Services

**Status**: Accepted
**Date**: 2025-11-15
**Deciders**: Platform Team
**Technical Story**: Security Consolidation (Issue #19)

## Context and Problem Statement

Workers communicate over HTTP with the platform and each other. We need to ensure authenticity, confidentiality, and integrity of all service-to-service communication. What security model should we adopt?

## Decision Drivers

- Zero-trust security model for distributed workers
- Need to authenticate both clients and servers
- Certificate-based identity aligns with SPIFFE/SPIRE future direction
- Automatic certificate management reduces operator burden
- Must work in both containerized and native deployments

## Considered Options

- **Option 1**: Mutual TLS (mTLS) with internal Certificate Authority
- **Option 2**: API keys/bearer tokens
- **Option 3**: Service mesh with automatic mTLS (Istio)

## Decision Outcome

**Chosen option**: "Mutual TLS with internal Certificate Authority", because it provides strong cryptographic identity, works across deployment models, and establishes foundation for SPIFFE adoption.

### Positive Consequences

- Cryptographic identity for all workers
- Certificate Authority service provides central trust anchor
- Automatic certificate bootstrap (workers request CSR signing on startup)
- Works in containers, native, and hybrid deployments
- Foundation for future SPIFFE/SPIRE migration
- Eliminates API key management burden

### Negative Consequences

- Requires Certificate Authority to be available for worker startup
- Certificate rotation needs to be implemented (future work)
- More complex than simple API keys
- PKI infrastructure to maintain

## Pros and Cons of the Options

### Option 1: Mutual TLS with Internal CA

Internal CA signs worker certificates. All connections require valid certs.

**Pros:**
- Strong cryptographic identity
- Industry standard security model
- Works across all deployment types
- Automatic certificate bootstrap
- Foundation for SPIFFE
- No secret distribution problem

**Cons:**
- CA becomes critical service
- Need to implement certificate lifecycle
- More complex than API keys
- Certificate path detection across environments

### Option 2: API Keys/Bearer Tokens

Workers authenticate with long-lived API keys.

**Pros:**
- Simple to implement
- Easy to understand
- No PKI infrastructure
- Fast authentication

**Cons:**
- Secret distribution problem
- Revocation is difficult
- No mutual authentication (server doesn't prove identity)
- Key rotation is manual burden
- Not aligned with zero-trust model
- Doesn't scale to distributed mesh

### Option 3: Service Mesh with Automatic mTLS

Istio/Linkerd handles mTLS automatically.

**Pros:**
- Industry standard solution
- Automatic certificate management
- Rich policy framework
- Observability built-in

**Cons:**
- Requires full containerization (blocks hybrid deployment)
- Heavy infrastructure overhead for small deployments
- Complex to configure correctly
- Vendor lock-in risk
- Overkill for current scale

## Links

- [Supersedes] Scattered security patterns in legacy workers
- [Related to] ADR-0001 (Controller/Worker model)
- [Refined by] ADR-0003 (Security module consolidation)
- [Related to] [docs/security/CERTIFICATE_AUTHORITY_ARCHITECTURE.md]
- [Related to] [docs/security/WORKER_CERTIFICATE_PATTERN.md]

## Implementation Notes

Implemented via unified `src/crank/security/` module:
- `certificate_authority.py` - CA service (port 9090)
- `certificate_manager.py` - Worker certificate bootstrap
- `ssl_config.py` - Automatic SSL context creation
- `paths.py` - Environment-aware path detection

All workers use `WorkerApplication.run()` for automatic HTTPS+mTLS setup.

**Reference Implementation**: `services/crank_hello_world.py` (3-line main function)

## Review History

- 2025-11-15 - Initial decision during Issue #19 (Security Consolidation)
- 2025-11-15 - Implemented and validated across all 9 workers
