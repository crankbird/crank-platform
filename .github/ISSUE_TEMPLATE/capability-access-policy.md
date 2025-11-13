---
name: Capability Access Policy (CAP) Implementation
about: Platform-level authorization for capability routing
title: '[SECURITY] Implement Capability Access Policy (CAP)'
labels: security, enhancement, wendy, architecture
assignees: ''
---

## Overview

Implement platform-level authorization that restricts which services can call which capabilities, even after mTLS authentication succeeds.

**Security Property**: A compromised worker cannot impersonate other services or call capabilities outside its intended scope.

## Problem Statement

**Current State**: Any authenticated service (via mTLS) can call any capability.

**Risk**: If `email-processor` is compromised, it can call `admin-api:delete-all-data` or any other capability, even though it should only need email-related capabilities.

**Solution**: Capability Access Policy enforces caller restrictions at the platform routing layer.

## Example Policy

```yaml
capability_access:
  summarize:v2:
    allowed_callers:
      - crank-ui
      - crank-doc-converter
      - system:internal
    denied_callers:
      - image-classifier  # This worker should never summarize

  classify-image:v1:
    allowed_callers:
      - crank-ui
      - email-processor
    max_calls_per_minute: 100
```

## Security Properties

- **Blast Radius Containment**: Compromised worker can only access capabilities it legitimately needs
- **No Impersonation**: Worker cannot call capabilities outside its policy scope
- **Architecture-Level Security**: Not a check—enforced by routing fabric itself

## Implementation Phases

### Phase 1: Policy Definition (Q1 2026)
- [ ] Design YAML policy language
- [ ] Define policy governance model (who can update policies?)
- [ ] Version control policy files alongside code
- [ ] Document capability inventory and natural caller relationships

### Phase 2: Routing Enforcement (Q2 2026)
- [ ] Platform controller extracts caller identity from mTLS cert (CN/SAN)
- [ ] Check caller against policy before routing request
- [ ] Return `403 Forbidden` + audit log if denied
- [ ] Add policy enforcement metrics/observability

### Phase 3: Dynamic Policy Updates (Q3 2026)
- [ ] Support runtime policy updates without platform restart
- [ ] Policy change audit trail
- [ ] Emergency "lockdown mode" to restrict all cross-service calls
- [ ] Policy validation testing framework

### Phase 4: Advanced Features (Q4 2026)
- [ ] Rate limiting per caller+capability
- [ ] Time-based access windows
- [ ] Conditional access based on request context
- [ ] Integration with external policy engines (OPA)

## What We Did to NOT Block This

✅ Platform controller already handles capability routing → policy checks are additive
✅ mTLS provides caller identity → no protocol changes needed
✅ Capability registry is versioned → policies can reference `capability:version`
✅ Audit logging exists → policy denials auto-appear in logs
✅ Service mesh compatible → CAP can layer on Istio/Linkerd

## Open Questions

- [ ] **Policy storage**: Config files vs database vs dedicated service?
- [ ] **Policy testing**: How to validate policies before deployment?
- [ ] **Emergency overrides**: Break-glass mechanism for incidents?
- [ ] **Policy complexity**: Trade-off between expressiveness and auditability?
- [ ] **Performance**: In-memory cache vs policy service latency?

## Success Criteria

- [ ] Compromised worker cannot call unauthorized capabilities
- [ ] Policy violations appear in audit logs with caller identity
- [ ] Policy updates deploy without platform downtime
- [ ] Performance overhead < 5ms per request
- [ ] Security team can audit who-can-call-what at any time

## References

- Security Architecture: `docs/security/DOCKER_SECURITY_DECISIONS.md` Section 9
- Wendy's Security Framework: `mascots/wendy/`
- Platform Controller Routing: `src/platform/controller/`

## Why Not Now?

We're letting the current security foundation (mTLS + container hardening) settle first. CAP adds a powerful security multiplier, but we want the base layers to feel normal before introducing policy complexity.

---

**Assigned to**: @wendy 🐰
**Timeline**: Q1-Q4 2026
**Priority**: P1 (High security value, not urgent)
