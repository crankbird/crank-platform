# Issue Burn-Down Sprint Plan

**Type**: Active Plan
**Status**: 🚀 Ready to Execute
**Temporal Context**: Current Work (Nov 2025 - Q1 2026)
**Total Issues**: 24 open issues
**Estimated Duration**: 4-5 sprints (~23 days core work)
**Last Updated**: November 14, 2025

---

## 📊 Overview

Systematic plan to burn down 24 open GitHub issues across 6 priority tiers, organized into focused sprints for maximum efficiency.

## 🎯 Priority Tiers

### 🔴 Tier 1: Critical Blockers (4 issues)
**Impact**: Security risks, blocks other work
**Issues**: #19, #32, #13, #18

### 🟡 Tier 2: Architecture Refactor (2 issues)
**Impact**: Core architectural shift
**Issues**: #30, #31

### 🟢 Tier 3: Test Corpus (4 issues)
**Impact**: Quality foundation
**Issues**: #33, #34, #35, #36

### 🔵 Tier 4: Developer Experience (4 issues)
**Impact**: Developer enablement
**Issues**: #17, #21, #23, #11

### 🟠 Tier 5: Technical Debt (6 issues)
**Impact**: Code quality, maintainability
**Issues**: #15, #16, #14, #22, #20, #24

### ⚪ Tier 6: Future Work (4 issues)
**Impact**: Deferred roadmap items
**Issues**: #25, #26, #12

---

## 🏃 Sprint Execution Plan

### **Sprint 1: Foundation** (5 days)

**Goal**: Clean repo, secure foundation, test infrastructure ready

**Issues**:
- **#13 - Python .gitignore** (30 min) - Gary 🐌
  - Add standard Python ignore patterns
  - Remove tracked artifacts
  - Verify clean working directory

- **#19 - Security Configuration Scattered** (2-3 days) - Wendy 🐰
  - **CRITICAL BLOCKER**: Blocks enterprise security Phase 1
  - Create single authoritative security module
  - Consolidate certificate management
  - Establish clear security boundaries

- **#32 - Test Data Structure** (1 day) - Gary 🐌
  - **FOUNDATION**: Unblocks issues #33-36
  - Create `tests/data/` directory structure
  - Add `tests/data/README.md` with licensing
  - Create `tests/utils/data_loader.py` utility

- **#18 - Fix MeshReceipt Duplicates** (2-4 hours) - Oliver 🦅
  - Remove duplicate MeshReceipt definitions
  - Fix broken field access in receipt generation
  - Add regression tests

**Success Criteria**:
- ✅ `git status` shows clean working directory
- ✅ Security audit passes (single source of truth)
- ✅ Test data infrastructure functional
- ✅ MeshReceipt tests passing

---

### **Sprint 2: Core Refactor** (6 days)

**Goal**: Controller/worker architecture complete and validated

**Issues**:
- **#30 - Phase 3: Controller Extraction** (3-5 days) - Multi-mascot
  - **MAJOR REFACTOR**: Core architectural shift
  - **Dependencies**: #19 resolved, Phases 0-2 complete ✅
  - Rename platform → controller files
  - Implement capability registry endpoints
  - Update workers for controller discovery
  - Create controller mocks for testing

- **#31 - Phase 4: Integration Tests** (1-2 days) - Multi-mascot
  - **Dependencies**: #30 complete
  - Multi-worker capability routing tests
  - Contract tests (schema compliance)
  - CI pipeline updates
  - Documentation updates
  - Cleanup old code

**Success Criteria**:
- ✅ Controller exposes capability registry endpoints
- ✅ Workers discover controller via ENV
- ✅ Integration test suite passing
- ✅ CI validates all workers
- ✅ Documentation complete

---

### **Sprint 3: Quality & Testing** (4 days)

**Goal**: Robust test coverage, clear test strategy

**Issues**:
- **#33 - JSON Schema Test Suite** (1 day) - High Priority
  - **Dependencies**: #32
  - Vendor JSON Schema Test Suite subset
  - Parametrize capability schema tests
  - Cover ≥50 edge cases

- **#34 - Adversarial Text Corpus** (1 day) - High Priority (Security)
  - **Dependencies**: #32
  - Pull OWASP FuzzDB payloads
  - Add to `tests/data/worker-runtime/adversarial-payloads/`
  - Parametrize worker runtime tests
  - Validate ≥20 adversarial inputs rejected

- **#35 - Certificate Fixtures** (1 day) - Medium Priority
  - **Dependencies**: #32
  - Create `tests/data/certs/regenerate.sh`
  - Add corrupted cert variants (≥5 scenarios)
  - Refactor CertificateManager tests to use fixtures

- **#36 - Test Corpus Governance** (2-4 hours) - Medium Priority
  - **Dependencies**: #32-35 complete
  - Add worker-specific corpus checklist
  - Define success metrics (≥80% coverage, ≥10 edge cases)
  - Create GitHub Project 'Test Corpus Initiative'
  - Update PR template with corpus requirement

**Success Criteria**:
- ✅ Capability schema: ≥50 validation edge cases
- ✅ Worker runtime: ≥20 adversarial tests passing
- ✅ Certificate tests fully deterministic
- ✅ Test corpus governance established

---

### **Sprint 4: Developer Experience** (3 days)

**Goal**: Excellent developer onboarding

**Issues**:
- **#15 - Fix Service Docs** (1-2 hours) - Kevin 🦙
  - Update `services/README.md` with correct file names
  - Fix `services/docker-compose.yml` references
  - Verify one-command deployment works

- **#16 - Centralize Docker Compose** (2-4 hours) - Kevin 🦙
  - Fix `services/docker-compose.yml` to reference existing Dockerfiles
  - Document compose file hierarchy
  - Create deployment decision tree

- **#17 - Consolidate Hello World Tests** (2-4 hours) - Oliver 🦅 + Gary 🐌
  - Document test purposes clearly (unit vs integration vs smoke)
  - Preserve different test types with clear documentation
  - Create test selection guide

- **#21 - Unified Test Runner** (1-2 days) - Gary 🐌
  - **Dependencies**: #17
  - Create `run_platform_tests.py` orchestrator
  - Implement service startup/teardown coordination
  - Generate consolidated test reports
  - CI/CD integration

- **#23 - Mascot Assignment Matrix** (2-4 hours) - Gary 🐌
  - Create mascot assignment decision matrix
  - Document collaboration patterns
  - Add AI agent guidance for issue triage

- **#11 - Hello World Worker Template** (1 day) - Bella 🐩
  - **Dependencies**: #30 complete (uses new worker patterns)
  - Create minimal worker template
  - Add customization guide
  - Include Dockerfile and tests

**Success Criteria**:
- ✅ New developer can deploy platform in one command
- ✅ Clear test suite documentation
- ✅ Unified test runner working
- ✅ Mascot assignment guidance clear
- ✅ Worker template enables <1 hour new worker creation

---

### **Sprint 5: Technical Debt** (5 days) - *Optional/Iterative*

**Goal**: Clean architecture, maintainable imports

**Issues**:
- **#14 - Refactor to src/ Layout** (2-3 days) - Bella 🐩 + Oliver 🦅
  - **Dependencies**: After #30 (don't disrupt refactor)
  - Create proper Python package hierarchy under `src/`
  - Move platform core and services to modules
  - Update imports and tests
  - Migration script for Docker builds

- **#22 - Fragile Import Paths** (1-2 days) - Oliver 🦅 + Bella 🐩
  - **Dependencies**: After #14
  - Audit all Python import statements
  - Create import compatibility layer
  - Add import validation tests
  - Document new import conventions

**Success Criteria**:
- ✅ Proper package structure under `src/`
- ✅ Zero circular imports
- ✅ Import validation tests in CI
- ✅ Migration guide documented

---

### **Future Sprints: GPU + Infrastructure**

**GPU Support** (5-7 days when prioritized):
- **#20 - UniversalGPUManager Integration** (1-2 days) - Kevin 🦙
  - Replace CUDA-only code with UniversalGPUManager
  - Test on M4 Mac Mini (MPS) and NVIDIA (CUDA)
  - Performance benchmarks

- **#24 - GPU Classifier CUDA-Only** (2-3 days) - Kevin 🦙 + Oliver 🦅
  - **Dependencies**: #20
  - Merge GPU classifier features into universal service
  - Document macOS native execution
  - Archive legacy CUDA-only service

- **#25 - Container GPU Strategy** (deferred)
  - **Dependencies**: #20, #24
  - **When**: After Apple/WSL GPU passthrough available

**Infrastructure** (when justified):
- **#26 - Extract to crank-infrastructure** (deferred)
  - **When**: Multi-repo need or ≥3 platform variants

**Cloud Deployment**:
- **#12 - Azure Deployment** (8-10 days)
  - **Dependencies**: After #30-31 complete
  - **When**: Validate new controller/worker architecture in cloud

---

## 📈 Success Metrics by Sprint

| Sprint | Key Metrics |
|--------|-------------|
| Sprint 1 | Security audit passes, test infrastructure working, clean git status |
| Sprint 2 | Controller extraction complete, integration tests green, CI passing |
| Sprint 3 | ≥80% test coverage, ≥20 adversarial tests, corpus governance active |
| Sprint 4 | New developer onboarding <1 hour, unified test runner operational |
| Sprint 5 | Zero circular imports, clean package structure, import validation in CI |

---

## 🎯 Execution Strategy

### **Immediate Next Actions** (Start Today)

1. **#13 - Python .gitignore** (30 min warm-up)
   - Quick win to build momentum
   - Clean up tracked artifacts

2. **#19 - Security Consolidation** (critical path)
   - Blocks enterprise security Phase 1
   - Blocks controller extraction (#30)
   - Highest priority blocker

### **Parallel Work Opportunities**

- **Documentation tasks** (#15, #16, #17, #23) can be done in parallel with development
- **Test corpus issues** (#33-36) can be parallelized after #32 foundation
- **GPU work** (#20, #24) can proceed independently of main refactor path

### **Critical Path**

```
#19 (Security) → #30 (Controller) → #31 (Integration) → Production Ready
      ↓
   #32 (Test Data) → #33-36 (Corpus) → Quality Validated
```

---

## 🚀 Getting Started

**To begin Sprint 1**:

```bash
# Start with quick win
git checkout -b fix/issue-13-python-gitignore

# Then tackle critical blocker
git checkout -b fix/issue-19-security-consolidation

# Foundation for test corpus
git checkout -b feat/issue-32-test-data-structure
```

**Branch naming convention**:
- `fix/issue-{N}-{short-description}` for bugs
- `feat/issue-{N}-{short-description}` for features
- `refactor/issue-{N}-{short-description}` for refactors
- `docs/issue-{N}-{short-description}` for documentation

---
**Estimated Total Burn-Down**: ~23 days core work (Sprints 1-4), excluding GPU/Infrastructure deferred to future sprints.
**Target Completion**: End of Q1 2026 (with controller refactor + test corpus complete by end of 2025).
