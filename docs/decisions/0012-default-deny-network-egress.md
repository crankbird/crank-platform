# ADR-0012: Default-Deny Network Egress for Agents and Workers

**Status**: Proposed
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Security & Governance](../planning/adr-backlog-2025-11-16.md#security--governance)

## Context and Problem Statement

Agents and workers process sensitive data (emails, documents, user information). We need to prevent unauthorized data exfiltration and ensure that network access is explicit and auditable. Should network egress be allowed by default or denied by default?

## Decision Drivers

- Data protection: Prevent accidental or malicious exfiltration
- Zero-trust: Explicit permission for all network access
- Auditability: Track all external network calls
- Least privilege: Workers get minimum network access
- Debugging: Need to allow controlled exceptions
- Compliance: GDPR, HIPAA require data protection

## Considered Options

- **Option 1**: Default-deny network egress - Proposed
- **Option 2**: Allow-all with monitoring
- **Option 3**: Domain allowlist per worker

## Decision Outcome

**Chosen option**: "Default-deny network egress", because it provides the strongest data protection while supporting explicit exceptions for legitimate use cases.

### Positive Consequences

- Strong data exfiltration protection
- Forces explicit network permission design
- Complete audit trail of external calls
- Compliance-friendly (GDPR, HIPAA)
- Catches bugs (unexpected network calls)
- Aligns with zero-trust model

### Negative Consequences

- More complex worker development
- Need proxy for allowed domains
- Debugging can be harder
- Legitimate network calls must be declared
- Requires egress proxy infrastructure

## Pros and Cons of the Options

### Option 1: Default-Deny Network Egress

Block all outbound network by default, explicit allowlist.

**Pros:**
- Maximum data protection
- Explicit network permissions
- Complete audit trail
- Zero-trust alignment
- Compliance-friendly

**Cons:**
- Development friction
- Proxy infrastructure needed
- Debugging complexity
- Allowlist maintenance

### Option 2: Allow-All with Monitoring

Allow all network, log and monitor.

**Pros:**
- Simple to implement
- No development friction
- Easy debugging
- Maximum flexibility

**Cons:**
- Data exfiltration risk
- Reactive not proactive
- Monitoring overhead
- Compliance issues

### Option 3: Domain Allowlist Per Worker

Each worker declares allowed domains.

**Pros:**
- Balanced approach
- Explicit permissions
- Some flexibility

**Cons:**
- Still allows data exfiltration (to allowed domains)
- Allowlist can grow large
- Hard to audit which worker called what

## Links

- [Related to] ADR-0002 (mTLS controls service-to-service communication)
- [Related to] ADR-0011 (ABAC can grant network permissions)
- [Enables] Zero-trust security model

## Implementation Notes

**Container Network Policy**:

```dockerfile
# Default: no external network access
FROM python:3.11-slim

# Only internal mesh access via proxy
ENV HTTP_PROXY=http://egress-proxy:8080
ENV HTTPS_PROXY=http://egress-proxy:8080
ENV NO_PROXY=localhost,127.0.0.1,.local

# Worker code doesn't need to know about restrictions
```

**Docker Compose**:

```yaml
services:
  email-classifier:
    image: crank-email-classifier
    networks:
      - crank-internal  # No bridge to external network
    environment:
      - HTTP_PROXY=http://egress-proxy:8080

  egress-proxy:
    image: squid
    networks:
      - crank-internal
      - external  # Only proxy can reach internet
    volumes:
      - ./egress-policy.conf:/etc/squid/squid.conf:ro
```

**Egress Policy** (`egress-policy.conf`):

```
# Default: deny all
http_access deny all

# Allow specific workers to specific domains
acl email_classifier src 172.20.0.5
acl spam_db dstdomain api.spamhaus.org
http_access allow email_classifier spam_db

# Audit all allowed requests
access_log /var/log/squid/access.log combined
```

**Worker Declaration**:

```yaml
# Worker capability manifest
worker_id: email-classifier-01
capabilities:
  - verb: classify_email
network_requirements:
  egress:
    - domain: api.spamhaus.org
      purpose: "Spam database lookup"
      justification: "Required for spam classification accuracy"
```

**Runtime Enforcement**:
- Kubernetes NetworkPolicy (production)
- Docker user-defined networks (local)
- iptables rules (native execution)

**Exceptions** (require approval):
- Model download (Hugging Face, PyTorch Hub)
- API calls (legitimate external APIs)
- Telemetry (optional, explicit opt-in)

## Review History

- 2025-11-16 - Initial proposal
