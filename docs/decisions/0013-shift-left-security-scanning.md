# ADR-0013: Shift-Left Security Scanning in CI/CD

**Status**: Proposed
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Security & Governance](../planning/adr-backlog-2025-11-16.md#security--governance)

## Context and Problem Statement

Container images and dependencies may contain known vulnerabilities (CVEs). We need to detect security issues early in the development cycle before they reach production. Should we scan for vulnerabilities during development, CI, or production?

## Decision Drivers

- Early detection: Find issues before production
- Automation: Don't rely on manual security reviews
- Developer feedback: Quick feedback loop
- Compliance: Regulatory requirements for vulnerability management
- Cost: Fix CVEs early is cheaper than later
- Zero-trust: Verify all dependencies

## Considered Options

- **Option 1**: Shift-left security scanning in CI/CD - Proposed
- **Option 2**: Production-only scanning
- **Option 3**: Manual security audits

## Decision Outcome

**Chosen option**: "Shift-left security scanning in CI/CD", because it provides early detection, automated feedback, and prevents vulnerable code from reaching production.

### Positive Consequences

- Early vulnerability detection
- Automated security checks
- Fast developer feedback
- Prevents vulnerable deployments
- Compliance-friendly
- Builds security awareness

### Negative Consequences

- CI pipeline slowdown (scan time)
- False positives need triage
- Tool maintenance overhead
- May block deployments
- Requires security expertise

## Pros and Cons of the Options

### Option 1: Shift-Left Security Scanning

Scan every commit/PR for vulnerabilities.

**Pros:**
- Early detection
- Automated
- Fast feedback
- Prevents issues
- Developer education

**Cons:**
- CI slowdown
- False positives
- Tool overhead
- May block PRs

### Option 2: Production-Only Scanning

Scan deployed images.

**Pros:**
- Simple
- No CI impact
- Actual runtime state

**Cons:**
- Late detection
- Vulnerabilities in production
- Expensive to fix
- Compliance gaps

### Option 3: Manual Security Audits

Periodic manual reviews.

**Pros:**
- Expert analysis
- Low false positives
- Context-aware

**Cons:**
- Slow
- Expensive
- Not scalable
- Human error
- Late detection

## Links

- [Related to] ADR-0010 (Container scanning critical for containerized deployment)
- [Related to] ADR-0012 (Defense in depth with network policies)

## Implementation Notes

**CI Pipeline** (GitHub Actions):

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      # Dependency scanning
      - name: Python dependency check
        run: |
          pip install safety
          safety check

      # Container scanning
      - name: Build image
        run: docker build -t ${{ github.sha }} .

      - name: Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ github.sha }}
          severity: 'CRITICAL,HIGH'
          exit-code: 1

      # Secret scanning
      - name: Gitleaks
        uses: gitleaks/gitleaks-action@v2

      # SAST
      - name: Bandit Python security linter
        run: |
          pip install bandit
          bandit -r src/ services/
```

**Tools**:
- **Trivy**: Container image scanning
- **Safety**: Python dependency CVEs
- **Gitleaks**: Secret detection
- **Bandit**: Python SAST
- **Dependabot**: Automated dependency updates

**Policy**:
- CRITICAL: Block merge
- HIGH: Block merge (can override with justification)
- MEDIUM: Warning only
- LOW: Informational

## Review History

- 2025-11-16 - Initial proposal
