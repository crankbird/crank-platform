# 🎭 Mascot Council Action Plan

**Review Date:** 2025-11-10
**Based On:** `mascots/MASCOT_COUNCIL_REVIEW.md`

This document prioritizes the technical debt and security issues identified by the Mascot Council review.

---

## 🚨 Priority 1: Security Violations (Wendy's Critical Findings)

### Issue 1.1: `verify=False` Anti-Pattern (CRITICAL)

**Problem:** Multiple workers disable TLS certificate verification, violating NIST SP 800-53 SC-8.

**Affected Files:**
- `services/crank_doc_converter.py:339-344` (2 instances)
- `services/crank_email_parser.py:551-555` (2 instances)
- `services/crank_image_classifier_advanced.py:592` (1 instance)

**Current Code:**
```python
def _create_client(self) -> httpx.AsyncClient:
    """Create HTTP client with certificate verification."""
    if hasattr(self.cert_store, "ca_cert") and self.cert_store.ca_cert:
        # Use CA certificate for verification
        return httpx.AsyncClient(verify=False)  # ❌ Simplified for now
    return httpx.AsyncClient(verify=False)  # ❌ Still disabled!
```

**Required Fix:**
```python
def _create_client(self) -> httpx.AsyncClient:
    """Create HTTP client with certificate verification."""
    if hasattr(self.cert_store, "ca_cert") and self.cert_store.ca_cert:
        # Use CA certificate for verification
        ca_path = self.cert_store.get_ca_cert_path()  # ✅ Get actual CA
        return httpx.AsyncClient(verify=ca_path)
    raise RuntimeError("CA certificate required for TLS verification")
```

**Action Items:**
- [ ] Fix `crank_doc_converter.py` to use CA verification
- [ ] Fix `crank_email_parser.py` to use CA verification
- [ ] Fix `crank_image_classifier_advanced.py` to use CA verification
- [ ] Add test: `test_worker_http_client_enforces_tls_verification`
- [ ] Update REQ-SEC-002 coverage in traceability matrix

**Estimated Effort:** 2-3 hours
**Risk if Deferred:** High - Man-in-the-middle attacks possible in production

---

### Issue 1.2: Health Check Security (`curl -k`)

**Problem:** Docker compose health checks disable certificate validation.

**Affected Files:**
- `docker-compose.development.yml:23-65` (multiple services)

**Current Code:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-k", "https://localhost:8100/health"]  # ❌ -k disables verification
```

**Required Fix:**
```yaml
healthcheck:
  test: ["CMD", "curl", "--cacert", "/app/certs/ca.crt", "https://localhost:8100/health"]
```

**Action Items:**
- [ ] Update all health checks to use `--cacert`
- [ ] Ensure CA cert is mounted at `/app/certs/ca.crt` in all containers
- [ ] Test health checks still work with proper verification
- [ ] Document health check certificate requirements

**Estimated Effort:** 1-2 hours
**Risk if Deferred:** Medium - Health checks work but violate security policy

---

### Issue 1.3: Missing REQ-SEC Test Coverage

**Problem:** Security requirements have 0/2 test coverage in traceability matrix.

**Required Tests:**
1. `test_controller_registration_requires_valid_certificate` (REQ-SEC-001: mTLS Authentication)
2. `test_capability_schema_rejects_malicious_input` (REQ-SEC-002: Input Validation) - **ALREADY EXISTS!**
3. `test_certificate_rotation_without_downtime` (REQ-SEC-001)
4. `test_worker_http_client_enforces_tls` (REQ-SEC-001)

**Action Items:**
- [ ] Create `tests/test_security_requirements.py`
- [ ] Add mTLS authentication tests
- [ ] Update traceability matrix to show existing REQ-SEC-002 coverage
- [ ] Add certificate rotation tests

**Estimated Effort:** 4-6 hours
**Risk if Deferred:** Low - Tests exist but aren't linked properly

---

## ⚙️ Priority 2: Anti-Pattern Elimination (Oliver's Findings)

### Issue 2.1: Literal Brace Logging (BUG)

**Problem:** Logging statements use literal braces instead of f-strings, losing diagnostic information.

**Affected Files:**
- `services/crank_doc_converter.py:158` - `"Converting {file.filename}..."`
- `services/crank_doc_converter.py:177` - `"Conversion failed: {e}"`
- `services/crank_doc_converter.py:334` - `"❌ Registration error: {e}"`

**Current Code:**
```python
logger.info("Converting {file.filename} from {input_format} to {output_format}")
# Logs: "Converting {file.filename} from {input_format} to {output_format}" (literals!)
```

**Required Fix:**
```python
logger.info(f"Converting {file.filename} from {input_format} to {output_format}")
# Logs: "Converting document.pdf from pdf to docx" (actual values!)
```

**Action Items:**
- [ ] Fix all logging statements in `crank_doc_converter.py`
- [ ] Search for same pattern in other services
- [ ] Add Ruff rule `G001` to detect f-string issues in logging
- [ ] Add pre-commit hook to catch this pattern

**Estimated Effort:** 1 hour
**Risk if Deferred:** Medium - Production logs are useless for debugging

---

### Issue 2.2: Duplicated Registration Logic (Code Smell)

**Problem:** `crank_doc_converter.py` reimplements registration models that exist in shared runtime.

**Affected Files:**
- `services/crank_doc_converter.py:31-178` - Custom `WorkerRegistration`, heartbeat
- `src/crank/worker_runtime/registration.py:24-183` - Canonical implementation

**Required Fix:**
Refactor document converter to use `WorkerApplication` + `ControllerClient`:

```python
from crank.worker_runtime.base import WorkerApplication

app = WorkerApplication(
    worker_id="crank-doc-converter",
    capabilities=[DOCUMENT_CONVERSION],
    # ... other config
)

# Business logic only - no registration/heartbeat reimplementation
@app.route("/convert", methods=["POST"])
async def convert_document(request):
    # ... conversion logic
```

**Action Items:**
- [ ] Refactor `crank_doc_converter.py` to use `WorkerApplication`
- [ ] Delete custom registration classes (200+ lines removed)
- [ ] Port route handlers to shared runtime hooks
- [ ] Apply same pattern to `crank_email_parser.py` and `crank_image_classifier_advanced.py`
- [ ] Update docs to show `WorkerApplication` as canonical pattern

**Estimated Effort:** 6-8 hours (per worker)
**Risk if Deferred:** High - Protocol changes require shotgun surgery across workers

---

## 🦙 Priority 3: Portability Issues (Kevin's Findings)

### Issue 3.1: Hardcoded Platform URLs

**Problem:** Workers default to `https://platform:8443` instead of using environment-driven discovery.

**Affected Files:**
- `services/crank_doc_converter.py:78-86`
- Similar pattern in other workers

**Current Code:**
```python
self.platform_url = platform_url or os.getenv("PLATFORM_URL", "https://platform:8443")
```

**Better Approach:**
```python
self.platform_url = os.getenv("PLATFORM_URL")
if not self.platform_url:
    raise RuntimeError("PLATFORM_URL environment variable required")
```

**Action Items:**
- [ ] Remove hardcoded fallbacks from all workers
- [ ] Update docker-compose to explicitly set `PLATFORM_URL`
- [ ] Add validation that required env vars are present
- [ ] Document required environment variables per worker

**Estimated Effort:** 2 hours
**Risk if Deferred:** Medium - Harder to deploy on Kubernetes/bare metal

---

### Issue 3.2: Docker-Only Development Scripts

**Problem:** `scripts/dev-universal.sh` assumes Docker CLI/daemon availability.

**Affected Files:**
- `scripts/dev-universal.sh:86-141`

**Required Fix:**
Add runtime detection for container orchestration:

```bash
detect_container_runtime() {
    if command -v docker &> /dev/null; then
        echo "docker"
    elif command -v podman &> /dev/null; then
        echo "podman"
    elif command -v nerdctl &> /dev/null; then
        echo "nerdctl"
    else
        echo "none"
    fi
}

CONTAINER_RUNTIME=$(detect_container_runtime)
```

**Action Items:**
- [ ] Add container runtime detection to dev scripts
- [ ] Create adapter layer for Docker/Podman/nerdctl commands
- [ ] Add smoke tests that boot via `podman compose`
- [ ] Document multi-runtime support in README

**Estimated Effort:** 4-6 hours
**Risk if Deferred:** Low - Only affects developers without Docker

---

## 🐌 Priority 4: Context & Coverage (Gary's Findings)

### Issue 4.1: Low Requirements Coverage (43%)

**Problem:** Only 15/35 requirements have tests, with entire categories untested.

**Gaps:**
- Security Requirements: 0/2 (0%) ❌
- Universal Protocol Support: 0/4 (0%) ❌
- Platform Services: 3/7 (43%) ⚠️

**Action Items:**
- [ ] Add REQ-SEC tests (see Priority 1.3)
- [ ] Add protocol support tests (HTTP/REST, WebSockets, gRPC, GraphQL)
- [ ] Fill platform services gaps (task routing, ML management, auto-scaling)
- [ ] Update traceability matrix to reflect new coverage
- [ ] Set target: 80% coverage by end of Phase 1

**Estimated Effort:** 12-16 hours (ongoing)
**Risk if Deferred:** Medium - Requirements drift from implementation

---

### Issue 4.2: Missing Architecture Decision Records

**Problem:** Major decisions (like `WorkerApplication` refactor) lack documented rationale.

**Action Items:**
- [ ] Create `docs/architecture/decisions/` directory
- [ ] Document ADR-001: Worker Runtime Standardization
- [ ] Document ADR-002: Test Corpus Infrastructure
- [ ] Document ADR-003: Requirements Traceability Pattern
- [ ] Template for future ADRs

**Estimated Effort:** 4 hours
**Risk if Deferred:** Low - But helpful for onboarding

---

## 🐩 Priority 5: Modularity (Bella's Findings)

### Issue 5.1: Missing Bella Test Suite

**Problem:** `mascots/README.md` advertises `mascots/bella/` modularity tests, but they don't exist.

**Action Items:**
- [ ] Create `mascots/bella/` directory structure
- [ ] Implement dependency graph analyzer
- [ ] Create interface contract validator
- [ ] Add separation readiness scoring tool
- [ ] Integrate into CI pipeline

**Estimated Effort:** 8-12 hours
**Risk if Deferred:** Low - Nice to have, not blocking

---

## 📊 Summary & Roadmap

### ✅ Success Stories (Already Passing Council Review)

**Refactored Workers (WorkerApplication Pattern):**
- `crank_email_classifier.py` - ✅ All mascots approve
- `crank_streaming.py` - ✅ All mascots approve

**Key Wins:**
- Zero `verify=False` instances
- Zero code duplication (registration/heartbeat in base class)
- Clean separation of concerns
- Automatic certificate management
- Environment-driven configuration
- 40-60% code reduction per worker

**Pattern Proven:** The `WorkerApplication` refactoring eliminates most council concerns automatically!

---

### Immediate Actions (This Week)

**Strategy:** Apply proven `WorkerApplication` pattern to remaining workers

1. ✅ **Refactor `crank_doc_converter.py`** (Priority 1) - 6-8 hours
   - Delete ~200 lines of duplicated infrastructure
   - Automatically fixes `verify=False` violations
   - Automatically fixes hardcoded URLs
   - Automatically fixes manual registration/heartbeat
   - Expected result: ~250-300 lines (60% reduction)

2. ✅ **Update REQ-SEC coverage in traceability matrix** (DONE) - 0 hours
   - Already completed in previous commit

3. ✅ **Fix literal brace logging** (DONE) - 0 hours
   - Already completed in previous commit

**Total: ~6-8 hours, eliminates ALL critical issues in document converter**

---

### Next Sprint (2 Weeks)

1. **Refactor `crank_email_parser.py`** - 6-8 hours
   - Apply WorkerApplication pattern
   - Fixes `verify=False` automatically
   - Completes email processing stack

2. **Refactor `crank_image_classifier_advanced.py`** - 8-10 hours
   - Apply WorkerApplication pattern (GPU variant)
   - Fixes `verify=False` automatically
   - More complex due to GPU memory management

3. **Create ADRs for architecture decisions** - 4 hours
   - ADR-001: Worker Runtime Standardization
   - ADR-002: WorkerApplication Pattern
   - ADR-003: Test Corpus Infrastructure

**Total: ~18-22 hours, achieves 100% worker standardization**

---

### Long Term (Phase 1 Completion)

1. Increase requirements coverage to 80% (Priority 4.1) - 16 hours
2. Add container runtime abstraction (Priority 3.2) - 6 hours
3. Create Bella's modularity test suite (Priority 5.1) - 12 hours

**Total: ~34 hours, achieves comprehensive quality goals**

---

## 🎯 Success Metrics

### Security (Wendy)
- [ ] Zero `verify=False` instances in production code
- [ ] 100% health checks use certificate validation
- [ ] REQ-SEC coverage: 0/2 → 4/4 (200%)

### Code Quality (Oliver)
- [ ] Zero literal brace logging statements
- [ ] Zero duplicated registration logic
- [ ] Ruff/pre-commit catches anti-patterns automatically

### Portability (Kevin)
- [ ] Zero hardcoded platform URLs
- [ ] Smoke tests pass on Docker + Podman
- [ ] Container runtime adapter in place

### Maintainability (Gary)
- [ ] Requirements coverage: 43% → 80%
- [ ] 4+ ADRs documenting key decisions
- [ ] Traceability automation in CI

### Modularity (Bella)
- [ ] All workers use `WorkerApplication` pattern
- [ ] Bella's test suite operational
- [ ] Separation readiness scores tracked

---

**Next Review:** After Priority 1 items are completed
**Council Reconvene:** 2025-11-17 (1 week)
