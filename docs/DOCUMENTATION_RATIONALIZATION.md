# Documentation Rationalization Plan

**Date**: 2025-11-10
**Status**: Active Cleanup Plan
**Priority**: CRITICAL — Foundation for BDD/Micronarrative Development
**Owner**: Platform Team

---

## Problem Statement

Our documentation has grown organically with inconsistent:
- **Naming conventions**: ALL_CAPS vs kebab-case vs underscore_case
- **Status tracking**: No clear "active" vs "deprecated" vs "historical"
- **Location logic**: Architecture vs Planning vs Development unclear
- **Duplication**: Multiple documents covering similar topics
- **Micronarrative sources**: BDD scenarios scattered, hard to extract

**Impact**: Can't confidently develop micronarratives and Gherkin tests because we don't know what's current architecture vs future plans vs superseded decisions.

---

## Current State Audit

### docs/ (Root Level) — 28 files

#### ✅ KEEP (Core References)
| File | Status | Purpose | Action |
|------|--------|---------|--------|
| `README.md` | Active | Documentation index | Update with new structure |
| `ARCHITECTURE.md` | Active | Current architecture | Keep, mark as "AS-IS" |
| `VISION.md` | Active | Product vision & economics | Keep, timeless |
| `PLATFORM_SERVICES.md` | Active | Service descriptions | Keep |

#### 🔄 CONSOLIDATE/RELOCATE
| File | Status | Issue | Action |
|------|--------|-------|--------|
| `ARCHITECTURAL_MENAGERIE_GUIDE.md` | Active | Should be in architecture/ | Move |
| `MASCOT_HAPPINESS_REPORT.md` | Historical | Report, not reference | Move to docs/reports/ |
| `MTLS_RESILIENCE_STRATEGY.md` | Superseded | See security/DOCKER_SECURITY_DECISIONS.md | Archive or merge |
| `anti-fragile-mtls-strategy.md` | Superseded | Same as above ^ | Merge into one mTLS doc |
| `certificate-authority-architecture.md` | Active | Should be in security/ | Move |
| `certificate-solution-summary.md` | Historical | Report | Move to reports/ |
| `container-strategy.md` | Superseded | See DOCKER_SECURITY_DECISIONS.md | Archive |

#### ⚠️ EVALUATE (Environment/Setup Docs)
| File | Status | Purpose | Action |
|------|--------|---------|--------|
| `current-environment-baseline.md` | Historical | Snapshot doc | Move to reports/ |
| `gpu-setup-reality-check.md` | Active | GPU setup guide | Keep or move to development/ |
| `universal-gpu-environment.md` | Active | GPU env strategy | Merge with above? |
| `uv-conda-hybrid-strategy.md` | Active | Package manager strategy | Keep or move to development/ |
| `mac-mini-development-strategy.md` | Active | Dev environment | Move to development/ |
| `WSL2-GPU-CUDA-COMPATIBILITY.md` | Active | Windows dev | Move to development/ |
| `windows-agent-instructions.md` | Active | Windows setup | Move to development/ |

#### 📊 REPORTS (Should be in reports/)
| File | Current Location | Action |
|------|------------------|--------|
| `CODE_REVIEW_RESPONSE.md` | docs/ | Move to reports/ |
| `azure-vm-test-results.md` | docs/ | Move to reports/ |
| `bleeding-edge-assessment.md` | docs/ | Move to reports/ |
| `email-classifier-cleanup-results.md` | docs/ | Move to reports/ |
| `error-suppression-strategy.md` | docs/ | Evaluate - strategy or report? |
| `ml-development-guide.md` | docs/ | Move to development/ |
| `pylance-ml-configuration.md` | docs/ | Move to development/ |

---

### docs/planning/ — 8 files ✅ MOSTLY GOOD

| File | Status | Purpose | Naming | Action |
|------|--------|---------|--------|--------|
| `REQUIREMENTS_TRACEABILITY.md` | Active | **CRITICAL** — Maps requirements → tests | ALL_CAPS | **KEEP** |
| `ENHANCEMENT_ROADMAP.md` | Active | **CRITICAL** — Future plans | ALL_CAPS | **KEEP** |
| `ENTERPRISE_READINESS_ASSESSMENT.md` | Active | **NEW** — Gap analysis | ALL_CAPS | **KEEP** |
| `CONTROLLER_WORKER_REFACTOR_PLAN.md` | Completed | Historical plan (Phase 2 done) | ALL_CAPS | Mark "COMPLETED" |
| `PHASE_2_README.md` | Active | Phase 2 implementation guide | ALL_CAPS | **KEEP** |
| `REPOSITORY_ORGANIZATION.md` | Active | Repo structure | ALL_CAPS | **KEEP** |
| `test-data-corpus-roadmap.md` | Active (Draft) | Test data strategy | kebab-case | Rename to ALL_CAPS |
| `crank-taxonomy-and-deployment.md` | ? | Taxonomy | kebab-case | Review + rename |

**Standardization**: Rename all to `ALL_CAPS.md` for planning docs.

---

### docs/architecture/ — 7 files

| File | Status | Purpose | Naming | Action |
|------|--------|---------|--------|--------|
| `mesh-interface-design.md` | Active | **CRITICAL** — Mesh interface spec | kebab-case | Rename `MESH_INTERFACE_DESIGN.md` |
| `WORKER_ARCHETYPE_PATTERNS.md` | Active | Worker design patterns | ALL_CAPS | **KEEP** |
| `WORKER_SEPARATION_STRATEGY.md` | Completed? | Worker refactor plan | ALL_CAPS | Mark status |
| `LEGACY_INTEGRATION.md` | Active | Legacy protocol adapters | ALL_CAPS | **KEEP** |
| `MODULARITY_ANALYSIS.md` | Active | JEMM analysis | ALL_CAPS | **KEEP** |
| `ENHANCED_MASCOT_FRAMEWORK.md` | Active | Mascot council design | ALL_CAPS | **KEEP** |
| `fastapi-dependency-injection.md` | Active | FastAPI DI strategy | kebab-case | Rename `FASTAPI_DEPENDENCY_INJECTION.md` |

**Standardization**: Rename kebab-case to `ALL_CAPS.md`.

---

### docs/security/ — 5 files ✅ GOOD

| File | Status | Purpose | Naming | Action |
|------|--------|---------|--------|--------|
| `DOCKER_SECURITY_DECISIONS.md` | Active | **CRITICAL** — Container security | ALL_CAPS | **KEEP** |
| `CAPABILITY_ACCESS_POLICY_ARCHITECTURE.md` | Active | **CRITICAL** — CAP design | ALL_CAPS | **KEEP** |
| `WORKER_CERTIFICATE_PATTERN.md` | Active | mTLS certificate pattern | ALL_CAPS | **KEEP** |
| `WORKER_MIGRATION_COMPLETE.md` | Completed | Historical report | ALL_CAPS | Move to reports/ |
| `docker-security-guide.md` | ? | Duplicate of above? | kebab-case | Review/merge |

**Action**: Check if `docker-security-guide.md` duplicates `DOCKER_SECURITY_DECISIONS.md`.

---

### docs/operations/ — 4 files ✅ GOOD

| File | Status | Purpose | Naming | Action |
|------|--------|---------|--------|--------|
| `AZURE_DEPLOYMENT.md` | Active | Azure deployment guide | ALL_CAPS | **KEEP** |
| `GITOPS_WORKFLOW.md` | Active | GitOps practices | ALL_CAPS | **KEEP** |
| `PORT_CONFIGURATION_STRATEGY.md` | Active | Port management | ALL_CAPS | **KEEP** |
| `PORT_CONFLICTS_RESOLVED.md` | Completed | Historical report | ALL_CAPS | Move to reports/ |

---

### docs/development/ — 10 files

| File | Status | Purpose | Naming | Action |
|------|--------|---------|--------|--------|
| `code-quality-strategy.md` | Active | **CRITICAL** — Type safety | kebab-case | Rename `CODE_QUALITY_STRATEGY.md` |
| `testing-strategy.md` | Active | Test strategy | kebab-case | Rename `TESTING_STRATEGY.md` |
| `crank-mesh-migration-guide.md` | Active | Migration guide | kebab-case | Rename `MIGRATION_MESH_INTERFACE.md` |
| `LINTING_AND_TYPE_CHECKING.md` | Active | Linting guide | ALL_CAPS | **KEEP** |
| `AI_ASSISTANT_ONBOARDING.md` | Active | AI assistant guide | ALL_CAPS | **KEEP** |
| `NEW_MACHINE_SETUP.md` | Active | Dev setup | ALL_CAPS | **KEEP** |
| `ONBOARDING_SUMMARY.md` | ? | Duplicate of above? | ALL_CAPS | Review/merge |
| `DOCKER_CONFIGS.md` | Active | Docker dev guide | ALL_CAPS | **KEEP** |
| `testing-implementation-summary.md` | Historical | Report | kebab-case | Move to reports/ |
| `host-environment-requirements.md` | Active | Host requirements | kebab-case | Rename |
| `universal-gpu-dependencies.md` | Active | GPU dependencies | kebab-case | Rename |

**Standardization**: Rename all to `ALL_CAPS.md`.

---

## Proposed Structure (After Cleanup)

### docs/ (Root — 4 Core Docs Only)
```
README.md                          # Master index
ARCHITECTURE.md                    # Current system design (AS-IS)
VISION.md                          # Product vision & philosophy
PLATFORM_SERVICES.md               # Service catalog
```

### docs/planning/ (Strategic Plans)
```
REQUIREMENTS_TRACEABILITY.md       # ⭐ CRITICAL — Req → Test mapping
ENHANCEMENT_ROADMAP.md             # ⭐ CRITICAL — Future plans (TO-BE)
ENTERPRISE_READINESS_ASSESSMENT.md # Gap analysis
PHASE_2_README.md                  # Phase 2 implementation guide
REPOSITORY_ORGANIZATION.md         # Repo structure
TEST_DATA_CORPUS_ROADMAP.md        # Test data strategy (renamed)
CONTROLLER_WORKER_REFACTOR.md      # Historical (mark COMPLETED)
TAXONOMY_AND_DEPLOYMENT.md         # Taxonomy (renamed)
```

### docs/architecture/ (Design Decisions — AS-IS)
```
MESH_INTERFACE_DESIGN.md           # ⭐ CRITICAL — Mesh spec (renamed)
WORKER_ARCHETYPE_PATTERNS.md       # Worker patterns
LEGACY_INTEGRATION.md              # Legacy protocol support
MODULARITY_ANALYSIS.md             # JEMM analysis
ENHANCED_MASCOT_FRAMEWORK.md       # Mascot council
FASTAPI_DEPENDENCY_INJECTION.md    # DI strategy (renamed)
ARCHITECTURAL_MENAGERIE_GUIDE.md   # Moved from root
WORKER_SEPARATION_STRATEGY.md      # Mark status COMPLETED?
```

### docs/security/ (Security Architecture)
```
DOCKER_SECURITY_DECISIONS.md       # ⭐ CRITICAL — Container security
CAPABILITY_ACCESS_POLICY_ARCHITECTURE.md  # ⭐ CAP design
WORKER_CERTIFICATE_PATTERN.md      # mTLS pattern
CERTIFICATE_AUTHORITY.md           # Moved from root (renamed)
MTLS_STRATEGY.md                   # Consolidated mTLS docs
```

### docs/operations/ (Ops & Deployment)
```
AZURE_DEPLOYMENT.md
GITOPS_WORKFLOW.md
PORT_CONFIGURATION_STRATEGY.md
```

### docs/development/ (Dev Guides)
```
CODE_QUALITY_STRATEGY.md           # ⭐ CRITICAL — Type safety
TESTING_STRATEGY.md                # ⭐ CRITICAL — Test approach
LINTING_AND_TYPE_CHECKING.md
AI_ASSISTANT_ONBOARDING.md
NEW_MACHINE_SETUP.md
DOCKER_CONFIGS.md
MIGRATION_MESH_INTERFACE.md        # Renamed
HOST_ENVIRONMENT_REQUIREMENTS.md   # Renamed
GPU_SETUP_GUIDE.md                 # Consolidated GPU docs
PACKAGE_MANAGER_STRATEGY.md        # uv/conda/pip strategy
WINDOWS_DEVELOPMENT.md             # Windows + WSL2 guide
MAC_DEVELOPMENT.md                 # macOS dev guide
```

### docs/reports/ (Historical Reports & Snapshots)
```
CODE_REVIEW_RESPONSE.md
AZURE_VM_TEST_RESULTS.md
BLEEDING_EDGE_ASSESSMENT.md
EMAIL_CLASSIFIER_CLEANUP.md
CURRENT_ENVIRONMENT_BASELINE.md
CERTIFICATE_SOLUTION_SUMMARY.md
MASCOT_HAPPINESS_REPORT.md
WORKER_MIGRATION_COMPLETE.md
PORT_CONFLICTS_RESOLVED.md
TESTING_IMPLEMENTATION_SUMMARY.md
```

---

## Naming Convention (Going Forward)

### ALL_CAPS.md
Use for:
- Strategic plans (planning/)
- Architecture decisions (architecture/)
- Security designs (security/)
- Operations guides (operations/)
- Development guides (development/)

### kebab-case.md
**DEPRECATED** — Convert all to ALL_CAPS.md

### Rationale
- ALL_CAPS clearly signals "this is reference documentation"
- Consistent across all folders
- Easy to spot in file listings
- No mixed case confusion

---

## Document Status Headers (REQUIRED)

Every document must have a header:

```markdown
# Document Title

**Status**: [Active | Draft | Completed | Deprecated | Superseded]
**Type**: [Architecture | Plan | Guide | Report]
**Last Updated**: YYYY-MM-DD
**Owner**: [Team/Person]
**Supersedes**: [filename.md] (if applicable)
**Superseded By**: [filename.md] (if applicable)

---
```

### Status Definitions

- **Active**: Current reference, in use
- **Draft**: Work in progress
- **Completed**: Finished work (e.g., migration complete)
- **Deprecated**: No longer recommended, kept for history
- **Superseded**: Replaced by newer document

---

## Critical Documents for BDD/Micronarrative Development

### Tier 1: Must Read First ⭐
1. `docs/planning/REQUIREMENTS_TRACEABILITY.md` — Maps user requirements → system requirements → tests
2. `docs/ARCHITECTURE.md` — Current system (AS-IS)
3. `docs/planning/ENHANCEMENT_ROADMAP.md` — Future plans (TO-BE)
4. `docs/architecture/MESH_INTERFACE_DESIGN.md` — Core interface contract

### Tier 2: Architecture Context
5. `docs/architecture/WORKER_ARCHETYPE_PATTERNS.md` — How workers should work
6. `docs/security/DOCKER_SECURITY_DECISIONS.md` — Security requirements
7. `docs/development/CODE_QUALITY_STRATEGY.md` — Type safety & testing patterns
8. `docs/development/TESTING_STRATEGY.md` — Test philosophy

### Tier 3: Specific Domains
9. `docs/architecture/LEGACY_INTEGRATION.md` — Protocol support
10. `docs/security/CAPABILITY_ACCESS_POLICY_ARCHITECTURE.md` — Future CAP design
11. `docs/planning/ENTERPRISE_READINESS_ASSESSMENT.md` — Enterprise gaps

---

## Micronarrative Extraction Strategy

### Current Micronarratives (Found)
- **MN-DOC-001**: Document conversion (sync/async/progress)
- **MN-GOV-001**: Audit trail with PII redaction
- **MN-OPS-001**: Zero-downtime capability rollout

### Where to Find More

**Source Documents**:
1. `REQUIREMENTS_TRACEABILITY.md` — Existing micronarratives
2. `ENHANCEMENT_ROADMAP.md` — Future capabilities → derive scenarios
3. `ENTERPRISE_READINESS_ASSESSMENT.md` — Enterprise scenarios
4. `WORKER_ARCHETYPE_PATTERNS.md` — Worker behavior scenarios
5. `CAPABILITY_ACCESS_POLICY_ARCHITECTURE.md` — Security scenarios

**Extraction Pattern**:
```gherkin
# For each capability/feature in roadmap:
Feature: <Capability Name>
  Scenario: <User goal>
    Given <precondition>
    When <action>
    Then <outcome>
    And <measurable result>
```

**Examples to Extract**:
- Back-pressure scenarios (from Enterprise Assessment)
- Idempotency scenarios (from Enterprise Assessment)
- CAP enforcement scenarios (from CAP Architecture)
- Multi-region failover (from Roadmap)
- Rate limiting (from Enterprise Assessment)

---

## Action Plan (Phased)

### Phase 1: Critical Cleanup (IMMEDIATE — 2 hours)

**Goal**: Make it clear what's current vs future vs historical.

1. **Add status headers** to all planning/ and architecture/ docs
2. **Rename** kebab-case files to ALL_CAPS in planning/ and architecture/
3. **Move** completed reports to docs/reports/
4. **Update** docs/README.md with new structure

**Files to Update** (Priority Order):
- ✅ `docs/planning/REQUIREMENTS_TRACEABILITY.md` — Add header
- ✅ `docs/planning/ENHANCEMENT_ROADMAP.md` — Add header
- ✅ `docs/ARCHITECTURE.md` — Add "AS-IS" header
- ✅ `docs/architecture/mesh-interface-design.md` → `MESH_INTERFACE_DESIGN.md`
- ✅ `docs/planning/test-data-corpus-roadmap.md` → `TEST_DATA_CORPUS_ROADMAP.md`
- ✅ Move `MASCOT_HAPPINESS_REPORT.md` → `reports/`
- ✅ Move `CODE_REVIEW_RESPONSE.md` → `reports/`

### Phase 2: Consolidation (NEXT — 4 hours)

**Goal**: Eliminate duplication and clarify locations.

1. **Consolidate** mTLS docs into one `security/MTLS_STRATEGY.md`
2. **Consolidate** GPU setup docs into `development/GPU_SETUP_GUIDE.md`
3. **Review** and merge/archive:
   - `ONBOARDING_SUMMARY.md` vs `NEW_MACHINE_SETUP.md`
   - `docker-security-guide.md` vs `DOCKER_SECURITY_DECISIONS.md`
4. **Move** environment setup docs from root to development/

### Phase 3: Micronarrative Extraction (AFTER Phase 1 — 8 hours)

**Goal**: Extract all implicit scenarios into explicit Gherkin.

1. **Review** `REQUIREMENTS_TRACEABILITY.md` — ensure all micronarratives are documented
2. **Extract** scenarios from `ENHANCEMENT_ROADMAP.md` Q1-Q2 items
3. **Create** `docs/planning/MICRONARRATIVE_CATALOG.md` — Master list
4. **Generate** Gherkin features for each micronarrative
5. **Map** to test files in `tests/e2e/`

---

## Success Criteria

After cleanup, you should be able to:

1. **Answer**: "What's our current architecture?" → Read `ARCHITECTURE.md`
2. **Answer**: "What are we building next?" → Read `ENHANCEMENT_ROADMAP.md`
3. **Answer**: "What tests do we need?" → Read `REQUIREMENTS_TRACEABILITY.md`
4. **Answer**: "What scenarios exist?" → Read `MICRONARRATIVE_CATALOG.md` (new)
5. **Answer**: "Is this doc current?" → Check status header
6. **Find**: Any document by logical location (planning/architecture/security/etc.)
7. **Know**: Which docs are historical vs active

---

## Next Steps

1. **Review this plan** with team
2. **Execute Phase 1** (2 hours) — Critical cleanup
3. **Generate** `MICRONARRATIVE_CATALOG.md` from Phase 3 work
4. **Create** GitHub issue for Phase 2 consolidation
5. **Schedule** weekly doc review to prevent drift

---

**Prepared by**: Documentation Rationalization Task Force
**Priority**: CRITICAL — Blocks effective BDD development
**Timeline**: Phase 1 immediate, Phase 2 this week, Phase 3 ongoing
