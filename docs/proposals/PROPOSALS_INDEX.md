# Crank Platform Proposals Index

**Purpose**: Directory of strategic proposals, specifications, and future direction documents
**Last Updated**: November 16, 2025

---

## 📚 Strategic Proposals

### 1. [Repository Split Strategy](repository-split-strategy.md)
**Status**: Draft | **Timeline**: Q1 2026

Proposes separating `crank-platform` (application) from `crank-infrastructure` (DevOps) for:
- Clear separation of concerns (developers vs DevOps teams)
- Multi-cloud deployment support (Azure, AWS, GCP, Kubernetes)
- Infrastructure as code (Terraform, Ansible)
- Cross-platform compatibility (macOS, Linux, WSL2)

**Dependencies**: Issue #19 (security consolidation) ✅ COMPLETE

---

### 2. [Access Model Evolution](crank-mesh-access-model-evolution.md)
**Status**: Conceptual Framework | **Timeline**: Long-term vision

Outlines evolution from traditional access control to capability-based security:
- **Current**: RBAC/ABAC models (insufficient for distributed systems)
- **Next**: Capability-Based Security (CBS) with unforgeable tokens
- **Future**: Object-Capability (OCap) model for pure capability security

**Key Points**:
- SPIFFE identity alignment for industry standards
- Capabilities as first-class authorization objects
- Workers become capability-bearing actors
- Foundation for machine-to-machine economy

**Connection to Issue #19**: Certificate-based identity enables capability tokens

---

### 3. [Job Scheduling to Capability Markets](from-job-scheduling-to-capability-markets.md)
**Status**: Conceptual Framework | **Timeline**: Q1-Q2 2026 (early experiments)

Vision for moving beyond classical job scheduling to economic capability markets:
- Workers self-benchmark performance (p95/p99 latency, throughput, cost)
- Workers publish SLO-based "bids" for capabilities
- Budget entitlements become capability tokens
- Controller matches requests to best worker under constraints
- Emergent market dynamics without blockchain complexity

**Technical Foundation**:
- Worker heartbeat protocol can carry SLO metadata
- Certificate-based trust enables verifiable performance claims
- Budget tokens use same security as capability tokens

**Connection to Issue #19**: Secure identity required for trusted self-benchmarking

---

### 4. [Enhancement Roadmap](enhancement-roadmap.md)
**Status**: Active Roadmap | **Timeline**: Q1 2026 → Q4 2026+

Phased enterprise readiness plan with clear metrics:

**Short Term (Q1 2026)**:
- SLO files per capability with CI regression checks
- Idempotency manager (1-hour deduplication window)
- Back-pressure controls (queue depth, load shedding)
- Rate limiting (per-tenant quotas)

**Medium Term (Q2-Q3 2026)**:
- OpenTelemetry distributed tracing
- Chaos engineering platform (Loki 🦙)
- Multi-node controller (peer-to-peer in single region)
- OPA policy engine integration

**Long Term (Q4 2026+)**:
- Cross-region deployment (multi-region mesh)
- Global capability market
- Autonomous economic negotiation
- Carbon tracking and green routing

**Dependency Resolution**: Issue #19 marked as ✅ COMPLETE

---

### 5. [Enterprise Security & Certification](enterprise-security.md)
**Status**: Ready to Execute | **Timeline**: Q1 2026 start → Q4 2026 certification

SOC 2, ISO 27001, GDPR/HIPAA compliance program:

**Phase 1 (Q1 2026)** - ✅ **UNBLOCKED**:
- Capability Access Policy (CAP) framework
- OPA policy engine with policy-as-code
- Distroless production images
- Automated certificate renewal (foundation exists via `crank.security`)

**Phase 2 (Q2 2026)**:
- Falco runtime monitoring
- Immutable audit trails with PII redaction
- SOC 2 readiness audit

**Phase 3 (Q3-Q4 2026)**:
- Multi-tenancy isolation
- Cross-region federation
- ISO 27001 / SOC 2 Type II certifications

**Critical Milestone**: Prerequisite blocker (Issue #19) ✅ RESOLVED (Nov 15, 2025)

---

### 6. [Gherkin Feature Specifications](crank-gherkins.feature.md)
**Status**: User Story Collection | **Timeline**: Ongoing reference

User-facing features for GPT + Crank integration:
- Execute agent-generated code locally via Crank
- Document processing pipelines with GPT guidance
- Multi-step workflows orchestrated by AI agents
- Natural language to capability execution

**Security Requirements**: Worker isolation, certificate-based API trust ✅ (Issue #19)

---

## 🔧 Technical Specifications

### FaaS Worker Specifications (`crank-specs/`)

#### [FaaS Worker v0](crank-specs/faas-worker-v0.md)
Minimal Python-only FaaS worker for Crank-Mesh:
- Python 3.11 sandbox execution
- Environment profile support
- CPU/GPU variant handling
- Time/output limits enforcement

**Job Schema**:

```json
{
  "job_id": "1234",
  "runtime": "python",
  "env_profile": "python-core",
  "constraints": {
    "accelerator": "cpu",
    "timeout_sec": 10,
    "max_output_bytes": 1048576
  },
  "code": "print(42)",
  "args": {"foo": "bar"}
}
```

**Safety Rules**:
- No network access
- Output size limits
- Timeout enforcement
- CPU/GPU selection via constraints

---

#### [Environment Profiles](crank-specs/env-profiles.md)
Python execution environment specifications:

**python-core**:
- Python 3.11 + stdlib
- `requests`, `pydantic`
- No subprocess access
- CPU-only

**python-docs**:
- `python-core` base
- `pandoc` installed
- `markdown`, `beautifulsoup4`

**python-ml**:
- Python + `numpy` + `torch`
- CPU or GPU build (determined at startup)
- ML inference and heavy compute

**Agent Guidance**:
- No `pip install` allowed
- Only use tools explicitly listed in profile

---

#### [CPU vs GPU Worker](crank-specs/cpu-gpu-split.md)
Same codebase, different deployment capabilities:

**CPU Worker Capability**:

```json
{
  "name": "python.run.ml",
  "env_profile": "python-ml",
  "accelerator": "cpu"
}
```

**GPU Worker Capability**:

```json
{
  "name": "python.run.ml",
  "env_profile": "python-ml",
  "accelerator": "gpu",
  "gpu_model": "RTX 1060"
}
```

**Job Constraints**:

```json
"constraints": { "accelerator": "gpu" }
```

**Connection to Architecture**: Aligns with Phase 0 capability schema work (Issue #27)

---

#### [Agent Instructions](crank-specs/agent-instructions.md)
Guidelines for AI agents generating Crank execution code:

**Rules**:
- Always generate Python 3.11
- Choose appropriate env profile
- Specify accelerator needs in constraints
- No `pip install` allowed
- Only assume tools listed in env profile

---

## 🔐 Identity & Security Quick Wins (`identity-easy-wins/`)

Collection of 10 incremental improvements for Crankbird identity system:

### 1. [SPIFFE ID Alignment](identity-easy-wins/1_spiffe_id.md)
Adopt SPIFFE-style identity URIs for industry compatibility

**Connection**: Aligns with Access Model Evolution proposal

---

### 2. [JWT Signing](identity-easy-wins/2_jwt_tokens.md)
Add cert-server JWT issuance for capability tokens

**Connection**: Enables capability markets and budget tokens

---

### 3. [Trust Bundle Endpoint](identity-easy-wins/3_trust_bundle.md)
Expose `/trust-bundle` endpoint for certificate distribution

**Connection**: Foundation for federated mesh trust

---

### 4. [Role Assumption](identity-easy-wins/4_role_assumption.md)
STS-like temporary role capability tokens

**Connection**: Enables fine-grained delegation in capability markets

---

### 5. [NIST 800-207 Mapping](identity-easy-wins/5_nist_doc.md)
Document Zero Trust Architecture (ZTA) alignment

**Connection**: Required for enterprise certification (SOC 2, ISO 27001)

---

### 6. [Certificate Metadata](identity-easy-wins/6_cert_metadata.md)
Add workload-type OID to certificates for capability binding

**Connection**: Strengthens capability verification in markets

---

### 7. [Attestation Vocabulary](identity-easy-wins/7_attestation_vocab.md)
Rename endpoints to use attestation semantics

**Connection**: SPIFFE/SPIRE compatibility, industry standards

---

### 8. [Workload Instance ID](identity-easy-wins/8_instance_id.md)
Add UUIDv7 instance IDs for worker tracking

**Connection**: Enables performance tracking for SLO bidding

---

### 9. [Node Attestation](identity-easy-wins/9_node_attestation.md)
Lightweight node attestation via certificate thumbprints

**Connection**: Multi-node controller trust (Phase 3 work)

---

### 10. [Trust Domain Spec](identity-easy-wins/10_trust_domain_spec.md)
Define Crankbird trust domain specification

**Connection**: Foundation for cross-organization federation

---

## 🔗 Cross-References

### Security Foundation → Proposals
- **Issue #19** (Security Consolidation) ✅ COMPLETE → Unblocks:
  - Enterprise Security & Certification (Phase 1 ready)
  - Capability Markets (verifiable identity foundation)
  - Repository Split (stable security to extract)
  - Identity Easy Wins (certificate infrastructure exists)

### Capability Schema → FaaS Specs
- **Phase 0** (Issue #27) capability schema → Validates:
  - FaaS worker capability declarations
  - Environment profile specifications
  - CPU/GPU constraint model

### Worker Runtime → Identity
- **Phase 0** (Issue #27) worker runtime → Integrates:
  - SPIFFE-aligned identity URIs
  - Certificate-based capability tokens
  - Trust bundle distribution

---

## 📋 Implementation Priority Matrix

| Proposal                    | Priority   | Blockers                       | Timeline          |
|-----------------------------|------------|--------------------------------|-------------------|
| Enterprise Security Phase 1 | **HIGH**   | ✅ None (Issue #19 complete)   | Q1 2026           |
| SLO Files + Benchmarking    | **HIGH**   | None                           | Q1 2026           |
| SPIFFE Identity Alignment   | **MEDIUM** | Issue #19 complete ✅          | Q1 2026           |
| FaaS Worker v0              | **MEDIUM** | Capability schema (Phase 0 ✅) | Q1-Q2 2026        |
| Multi-Node Controller       | **MEDIUM** | Identity work                  | Q2 2026           |
| Capability Markets          | **MEDIUM** | SLO files, benchmarking        | Q2-Q3 2026        |
| Repository Split            | **LOW**    | Stable platform (ready)        | Q1 2026 (optional)|
| Cross-Region Mesh           | **LOW**    | Multi-node controller          | Q4 2026+          |

---

## 📚 Related Documentation

- **Recent Work Integration**: `docs/RECENT_WORK_INTEGRATION.md` - Connects Issue #19 to proposals
- **Worker Security Pattern**: `docs/development/WORKER_SECURITY_PATTERN.md` - Implementation guide
- **Agent Instructions**: `.github/copilot-instructions.md` - AI agent guidance
- **Architecture**: `docs/architecture/controller-worker-model.md` - Core architecture
- **Roadmap**: `docs/planning/phase-3-controller-extraction.md` - Current work

---

*This index is maintained as proposals are added. Last significant update: Integration of Issue #19 completion (Nov 16, 2025)*
