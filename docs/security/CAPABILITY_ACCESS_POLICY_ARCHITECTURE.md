# Capability Access Policy (CAP) — Architecture Note

**Status**: Future Enhancement (Q2-Q3 2026)  
**Owner**: Wendy 🐰  
**Purpose**: Document why CAP isn't implemented now and how current architecture won't block it

---

## What CAP Solves

**Problem**: A compromised worker with valid mTLS credentials can currently call ANY capability.

**Solution**: Platform-level policy enforcement that restricts which services can call which capabilities.

```yaml
# Example policy
capability_access:
  summarize:v2:
    allowed_callers:
      - crank-ui
      - crank-doc-converter
      - system:internal
    denied_callers:
      - image-classifier  # Should never need summarization
```

**Security Property**: Even if `email-processor` is fully compromised, it cannot:
- Call `admin-api:delete-all-data`
- Impersonate `crank-ui` to exfiltrate data
- Access capabilities outside its legitimate job function

This transforms security from "checks" into **architecture**.

---

## Why We're NOT Implementing This Today

**Current Priority**: Let the security foundation settle and feel normal.

**What needs to mature first**:
1. Platform controller routing must be stable and battle-tested
2. We need real-world usage data to inform policy granularity
3. mTLS authentication should become "boring" before we add policy complexity
4. Policy language and governance model require careful design

**Philosophy**: Security should feel normal, not heavy. Add multipliers incrementally.

---

## What We Did to NOT Block This Later

The current architecture is **CAP-ready** with zero breaking changes needed:

| Design Decision | Why It Enables CAP |
|----------------|-------------------|
| **Platform controller does routing** | Policy checks are additive to routing logic |
| **mTLS provides caller identity** | CN/SAN already identifies the calling service |
| **Capability registry is versioned** | Policies can reference `capability:version` |
| **Audit logging exists** | Policy denials auto-appear in existing logs |
| **Service mesh compatible** | CAP can layer on Istio/Linkerd if adopted |

**No protocol changes. No database migrations. No service disruptions.**

CAP is a platform controller feature that turns on when the policies are ready.

---

## Implementation Timeline

### Q4 2025: Observation & Documentation
- Document capability inventory (which capabilities exist)
- Map natural caller relationships (who legitimately calls what)
- Identify blast radius for each capability

### Q1 2026: Policy Design
- Design YAML policy language
- Define policy governance (who updates policies, approval process)
- Create policy validation and testing framework
- Version control policies alongside code

### Q2 2026: Platform Integration
- Platform controller extracts caller identity from mTLS cert
- Check caller against policy before routing
- Return `403 Forbidden` + audit log if denied
- Metrics and observability for policy enforcement

### Q3 2026: Production Rollout
- Deploy in audit-only mode (log violations, don't block)
- Tune policies based on real traffic patterns
- Enable enforcement mode for production workloads
- Emergency "lockdown mode" for incident response

### Q4 2026: Advanced Features
- Rate limiting per caller+capability
- Time-based access windows
- Conditional policies based on request context
- Integration with external policy engines (OPA)

---

## Reference Architecture

```text
┌─────────────────────────────────────────────────────────┐
│ Platform Controller (with CAP)                          │
│                                                         │
│  1. Receive request: email-processor → summarize:v2    │
│  2. Extract caller: CN=email-processor (from mTLS)     │
│  3. Check policy: allowed_callers includes caller?     │
│  4. ✅ Route request   OR   ❌ Return 403 + audit      │
└─────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
         ✅ ALLOWED                  ❌ DENIED
    (continues to worker)      (logged, rejected)
```

---

## Success Criteria

Before declaring CAP "done", we must demonstrate:

- [ ] Compromised worker cannot call unauthorized capabilities
- [ ] Policy violations appear in audit logs with full context
- [ ] Policy updates deploy without platform downtime
- [ ] Performance overhead < 5ms per request
- [ ] Security team can audit "who can call what" at any time
- [ ] Emergency lockdown can restrict all cross-service calls in < 60 seconds

---

## Where to Learn More

- **Full Design**: `docs/security/DOCKER_SECURITY_DECISIONS.md` Section 9
- **Issue Template**: `.github/ISSUE_TEMPLATE/capability-access-policy.md`
- **Roadmap**: `docs/planning/ENHANCEMENT_ROADMAP.md` Q2-Q3 2026
- **Wendy's Security Framework**: `mascots/wendy/`

---

## For Future Implementers

When you're ready to build CAP, you'll need:

1. **Policy parser**: YAML → in-memory policy tree
2. **Caller extractor**: mTLS cert → service identity
3. **Policy matcher**: (caller, capability, version) → allowed/denied
4. **Audit integration**: Log all policy decisions with context
5. **Metrics**: Policy checks per second, denial rate, latency
6. **Testing**: Policy validation framework + chaos engineering

The platform controller already has hooks for all of these. CAP is an additive feature.

---

**Remember**: This is a security **multiplier**, not a prerequisite. The current foundation (mTLS + container hardening + CVE scanning) is already production-ready for many workloads. CAP is for when you need defense against insider threats and compromised workers.

Let the foundation feel normal first. Then add the multiplier when it's time.

— Wendy 🐰
