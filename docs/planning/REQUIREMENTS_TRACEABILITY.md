# Requirements Traceability Matrix

> **Purpose**: Link tests to requirements, enabling bidirectional traceability and requirements coverage analysis.

## Overview

This document maps test cases to system requirements defined in `REQUIREMENTS.md`. Each requirement should have at least one test validating its implementation.

## Stakeholder (User) Requirements via Micronarratives

> **Why**: Our current matrix focuses on internal/system requirements. This section adds **stakeholder-facing user requirements** expressed as short **micronarratives** (story-like scenarios) and traces them to system capabilities and executable tests. The goal is to ensure we test what real users/agents actually need, not just whether functions return sane values.

### Format

- **Micronarrative (MN-ID)**: One-sentence story (Actor • Context • Intent • Outcome • Value)
- **User Requirement (UR-ID)**: Verifiable statement derived from the micronarrative
- **Acceptance Criteria**: Gherkin-style scenarios that become end-to-end tests
- **Trace Links**: UR → System Requirement(s) (REQ-*) → Test(s)

### Template

| Field | Content |
|------|---------|
| **Micronarrative** | *As an {Actor} in {Context}, I want {Intent} so that {Value}.* |
| **User Requirement** | *The system shall …* (quantified where possible) |
| **Acceptance Criteria** | Gherkin `Given/When/Then` scenarios |
| **Trace Links** | UR-→ REQ-… → Test(s) |

### Initial Micronarratives (Draft)

#### MN-OPS-001 — Zero-Downtime Capability Rollout

- **Micronarrative**: *As a platform operator during business hours, I want to roll out a new capability without dropping requests so that customers experience zero downtime.*
- **User Requirement (UR-OPS-001)**: The platform shall support **seamless capability activation** with **no 5xx spikes** and **<1% request retries** during rollout windows ≤ **5 minutes**.
- **Acceptance Criteria**:

  ```gherkin
  Feature: Zero-downtime rollout
    Scenario: Activate new capability without dropping requests
      Given an idle registered worker for capability "summarize:v2"
      And production traffic flowing through the controller
      When the operator activates route "summarize:v2" with weight 10%
      Then the observed 5xx rate over 5 minutes is 0
      And the retry rate is < 1%
      And p95 latency increases by < 20%
  ```

- **Trace Links**: UR-OPS-001 → REQ-PLAT-Load Balancing, REQ-PLAT-Request Routing, REQ-SEC-001 (mTLS) → *Pending Tests*: `tests/e2e/test_rollout_zerodowntime.py::TestWeightedRouting` (to be added)

#### MN-CUST-001 — Bounded-Latency Job Completion

- **Micronarrative**: *As a customer agent submitting a document for conversion, I want a result within a predictable time so that I can provide a synchronous UX.*
- **User Requirement (UR-CUST-001)**: For inputs ≤ **20MB**, the system shall return results within **3s p95 / 10s p99**, or **emit progress + callback** within **1s**.
- **Acceptance Criteria**:

  ```gherkin
  Feature: Bounded-latency conversion
    Scenario: Small document returns synchronously
      Given a 5MB PDF input
      When I POST to /api/convert?target=docx
      Then the response status is 200 within 3 seconds (p95)
      And the payload includes a downloadable artifact
    Scenario: Large document falls back to async with progress
      Given a 50MB PDF input
      When I POST to /api/convert?target=docx
      Then I receive 202 Accepted within 1 second
      And a progress endpoint emits events at least every 2 seconds
  ```

- **Trace Links**: UR-CUST-001 → REQ-PLAT-Connection Pooling, REQ-QA-Timeout Handling → *Pending Tests*: `tests/e2e/test_conversion_latency.py` (to be added)

#### MN-GOV-001 — Auditability with Redaction

- **Micronarrative**: *As a governance auditor during quarterly review, I need to trace who invoked which capability with what parameters, without exposing secrets, so that we meet compliance obligations.*
- **User Requirement (UR-GOV-001)**: The platform shall produce **immutable audit events** for every request, including **caller, capability, decision, latency, status**, with **configurable PII redaction** and **export to JSONL**.
- **Acceptance Criteria**:

  ```gherkin
  Feature: Auditable request trail
    Scenario: Redacted audit log on success
      Given redaction rules hide fields ["token", "email"]
      When an agent calls capability "summarize:v2" with a token and email
      Then the audit record omits those fields
      And includes request_id, caller_id, capability, status, latency_ms
      And the record is written to audit-YYYYMMDD.jsonl
  ```

- **Trace Links**: UR-GOV-001 → REQ-SEC-Audit Trail → *Pending Tests*: `tests/e2e/test_audit_redaction.py`

### User Requirements Coverage (New)

| User Requirement | E2E Test(s) | Status |
|------------------|-------------|--------|
| UR-OPS-001 | `test_rollout_zerodowntime.py::TestWeightedRouting` | *Pending* |
| UR-CUST-001 | `test_conversion_latency.py` | *Pending* |
| UR-GOV-001 | `test_audit_redaction.py` | *Pending* |

> Add more micronarratives as they emerge (operators, customer agents, governance, SREs, billing, privacy). Each UR must trace down to one or more REQ-* rows and executable tests.

## Traceability Format

Tests use structured docstrings with explicit requirement links:

```python
def test_example(self) -> None:
    """
    Test brief description.

    REQUIREMENT: Section - Specific requirement
    VALIDATES: What aspect of the requirement is validated
    """
```

## Coverage Matrix

### 🔐 Security Requirements

| Requirement | Test(s) | Coverage | Notes |
|------------|---------|----------|-------|
| **mTLS Authentication (REQ-SEC-001)** | *Pending* | 0% | Need controller↔worker mTLS handshake tests |
| **Input Validation (REQ-SEC-002)** | `TestCapabilitySchemaCorpus.test_adversarial_capability_handling[2 cases]` | ✅ 100% | SQL injection, XSS, command injection, Unicode exploits validated |
| Multi-tier Auth | *Pending* | 0% | Need tests for API keys, JWT, RBAC |
| Audit Trail | *Pending* | 0% | Need request logging tests |

### 🏭 Worker Service Requirements

#### Worker Container Pattern

| Sub-Requirement | Test(s) | Coverage | Notes |
|-----------------|---------|----------|-------|
| **Stateless Design** | *Pending* | 0% | Need tests for worker state isolation |
| **Platform Registration** | `test_registration_exchange_from_corpus` | ✅ 100% | Validates registration protocol |
| **Health Reporting** | `TestHealthCheckManager.*` | ✅ 100% | Full health check test suite (6 tests) |
| **Graceful Shutdown** | `test_http_client_cleanup_on_close`, `TestShutdownHandler.*` | ✅ 100% | Shutdown handler + HTTP cleanup (7 tests) |
| **Resource Efficiency** | `test_http_client_lazy_initialization` | ✅ 100% | Lazy client initialization |

### 📊 Platform Services Requirements

#### Service Mesh Capabilities

| Sub-Requirement | Test(s) | Coverage | Notes |
|-----------------|---------|----------|-------|
| **Worker Registration** | `TestControllerClient.test_registration_success`, `test_registration_exchange_from_corpus` | ✅ 100% | Registration flow validated |
| **Health Checking** | `TestHealthCheckManager.*` | ✅ 100% | Health status, uptime, custom details |
| **Load Balancing** | *Pending* | 0% | Need controller routing tests |
| **Circuit Breakers** | *Pending* | 0% | Need fault tolerance tests |
| **Request Routing** | *Pending* | 0% | Need capability-based routing tests |

#### Performance Optimization

| Sub-Requirement | Test(s) | Coverage | Notes |
|-----------------|---------|----------|-------|
| **Connection Pooling** | `test_http_client_reuse_across_requests` | ✅ 100% | Validates HTTP client reuse |
| **Resource Cleanup** | `test_http_client_cleanup_on_close` | ✅ 100% | Validates proper cleanup |

### 🔧 Capability Schema Requirements

| Sub-Requirement | Test(s) | Coverage | Notes |
|-----------------|---------|----------|-------|
| **Schema Validation** | `test_capability_schema.py` (24 tests) | ✅ 100% | Full capability validation suite |
| **Standard Capabilities** | `test_standard_capabilities` | ✅ 100% | Validates 6 built-in capabilities |
| **Custom Capabilities** | *Pending* | 0% | Need tests for custom capability registration |

### 🌐 Universal Protocol Support

| Requirement | Test(s) | Coverage | Notes |
|------------|---------|----------|-------|
| **REST API** | *Pending* | 0% | Need REST adapter tests |
| **MCP (Model Context Protocol)** | *Pending* | 0% | Need MCP adapter tests |
| **gRPC** | *Pending* | 0% | Need gRPC adapter tests |
| **Protocol Adapter Architecture** | *Pending* | 0% | Need adapter interface tests |

### 📋 Quality Assurance Requirements

| Requirement | Test(s) | Coverage | Notes |
|------------|---------|----------|-------|
| **Error Handling** | `test_shutdown_scenarios_from_corpus[error.json]` | ⚠️ 20% | Shutdown errors covered, need more |
| **Input Validation** | `test_certificate_bundle_rejects_invalid[2 cases]` | ⚠️ 20% | Certificate validation covered, need schema validation |
| **Timeout Handling** | `test_shutdown_scenarios_from_corpus[timeout.json]` | ⚠️ 20% | Shutdown timeouts covered, need request timeouts |

## Beauty Pass Requirements (Commit 824bb96)

These tests validate specific code quality improvements from the beauty pass:

| Improvement | Test(s) | Coverage |
|------------|---------|----------|
| **ShutdownTask metadata** | `test_shutdown_task_metadata`, `test_shutdown_scenarios_from_corpus[2 scenarios]` | ✅ 100% |
| **CertificateBundle validation** | `test_certificate_bundle_validation`, `test_certificate_bundle_rejects_invalid[2 cases]`, `test_certificate_bundle_to_uvicorn_config` | ✅ 100% |
| **Lazy httpx.AsyncClient** | `test_http_client_lazy_initialization` | ✅ 100% |
| **Connection pooling** | `test_http_client_reuse_across_requests` | ✅ 100% |
| **Resource cleanup** | `test_http_client_cleanup_on_close` | ✅ 100% |
| **Decomposed `__init__`** | *Pending* | 0% |

## Coverage Summary

### Overall Statistics

- **Total Requirements**: 35 identified
- **Requirements with Tests**: 16 (46%)
- **Fully Covered**: 13 (37%)
- **Partially Covered**: 3 (9%)
- **Not Covered**: 19 (54%)

### By Category

- **Worker Container Pattern**: 5/5 (100%) ✅
- **Platform Services**: 3/7 (43%) ⚠️
- **Security Requirements**: 1/2 (50%) ⚠️  ← **Updated: REQ-SEC-002 now validated**
- **Universal Protocol Support**: 0/4 (0%) ❌
- **Quality Assurance**: 3/3 (100%) ⚠️ (partial coverage)

### Writing Good Micronarratives (Quick Guide)

1. **Actor** (who) • **Context** (when/where) • **Intent** (what) • **Outcome** (then) • **Value** (why)
2. Convert the story to a **verifiable User Requirement (UR-ID)** with measurable thresholds.
3. Express **Acceptance Criteria** in Gherkin for automation.
4. **Trace** UR → REQ-* → Test(s). If any link is missing, the work isn’t done.

## How to Use This Matrix

### For Developers

1. **Before implementing**: Check matrix to see if requirement has tests
2. **After implementing**: Update matrix with new tests
3. **When refactoring**: Ensure all linked tests still pass

### For Test Writers

1. **Add `REQUIREMENT:` tag** to test docstring referencing REQUIREMENTS.md section
2. **Add `VALIDATES:` tag** describing what specific aspect is tested
3. **Update this matrix** when adding new requirement-linked tests

### For Requirements Analysis

**Generate coverage report**:

```bash
# Extract REQUIREMENT tags from tests
grep -r "REQUIREMENT:" tests/ | wc -l

# Find requirements without tests
# (Manual process - compare REQUIREMENTS.md sections to matrix)
```

**Infer requirements from tests**:

- Parse `REQUIREMENT:` tags from all test files
- Group by requirement category
- Identify coverage gaps

## Future Enhancements

### Automated Traceability

Create a tool to:

1. **Parse test files** for `REQUIREMENT:` and `VALIDATES:` tags
2. **Parse REQUIREMENTS.md** for all stated requirements
3. **Generate coverage report** showing:
   - Requirements without tests
   - Tests without requirement links
   - Coverage percentage by category
4. **Validate on CI** that new requirements have tests

### Requirements-Driven Testing

```python
# Example: Generate test stubs from requirements
@requirement("Worker Container Pattern - Graceful Shutdown")
@validates("Workers handle SIGTERM within 30 seconds")
def test_worker_graceful_shutdown_timeout():
    # Test implementation
    pass
```

### Bidirectional Inference

Given tests, we should be able to reconstruct:

1. **Functional requirements** - What the system must do
2. **Quality attributes** - Performance, reliability, security
3. **Constraints** - Technology choices, protocols
4. **Success criteria** - Measurable outcomes

---

**Related Documents**:

- Requirements: `REQUIREMENTS.md`
- Stakeholder/User Requirements (Micronarratives): `STAKEHOLDER_REQUIREMENTS.md` (optional dedicated doc; this file remains the trace hub)
- Test Suite: `tests/test_worker_runtime.py`, `tests/test_capability_schema.py`
- Test Corpus: `tests/data/README.md`
- Development Philosophy: `.vscode/AGENT_CONTEXT.md`
