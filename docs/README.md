# Crank Platform Documentation

**Last Updated**: 2025-11-10
**Purpose**: Navigation hub for all platform documentation

## 📖 Documentation Structure

This documentation is organized into **AS-IS** (current architecture), **TO-BE** (planned features), and **HISTORICAL** (completed work). See [DOCUMENTATION_RATIONALIZATION.md](DOCUMENTATION_RATIONALIZATION.md) for complete structure and standards.

## 🎯 Critical Documents (Tier 1 - Start Here)

### Current Architecture (AS-IS)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Current system design, JEMM principles
- **[REQUIREMENTS_TRACEABILITY.md](planning/REQUIREMENTS_TRACEABILITY.md)** - Requirements → Tests mapping, micronarratives

### Future Plans (TO-BE)
- **[ENHANCEMENT_ROADMAP.md](planning/ENHANCEMENT_ROADMAP.md)** - Strategic roadmap Q1-Q4 2026

### Foundation
- **[ORGANIZATION_SUMMARY.md](../philosophy/ORGANIZATION_SUMMARY.md)** - Project vision and context

## 📂 Documentation by Category

### Planning & Requirements
- [planning/ENHANCEMENT_ROADMAP.md](planning/ENHANCEMENT_ROADMAP.md) - Strategic roadmap (TO-BE)
- [planning/REQUIREMENTS_TRACEABILITY.md](planning/REQUIREMENTS_TRACEABILITY.md) - Requirements engineering (Active)
- [planning/ENTERPRISE_READINESS_ASSESSMENT.md](planning/ENTERPRISE_READINESS_ASSESSMENT.md) - Gap analysis (2025-11-10)
- [planning/TEST_DATA_CORPUS_ROADMAP.md](planning/TEST_DATA_CORPUS_ROADMAP.md) - Test data strategy

### Architecture & Design
- [ARCHITECTURE.md](ARCHITECTURE.md) - Current system design (AS-IS)
- [architecture/MESH_INTERFACE_DESIGN.md](architecture/MESH_INTERFACE_DESIGN.md) - Service mesh patterns
- [architecture/FASTAPI_DEPENDENCY_INJECTION.md](architecture/FASTAPI_DEPENDENCY_INJECTION.md) - DI patterns

### Security
- [security/README.md](security/README.md) - Security architecture overview
- [security/DOCKER_SECURITY_DECISIONS.md](security/DOCKER_SECURITY_DECISIONS.md) - Container security + CAP design
- [security/CERTIFICATE_AUTHORITY_ARCHITECTURE.md](security/CERTIFICATE_AUTHORITY_ARCHITECTURE.md) - CA service & enterprise PKI
- [security/WORKER_CERTIFICATE_PATTERN.md](security/WORKER_CERTIFICATE_PATTERN.md) - Worker mTLS pattern
- [security/CAPABILITY_ACCESS_POLICY_ARCHITECTURE.md](security/CAPABILITY_ACCESS_POLICY_ARCHITECTURE.md) - CAP (Q2-Q4 2026)

### Operations
- [operations/DEPLOYMENT_STRATEGY.md](operations/DEPLOYMENT_STRATEGY.md) - Multi-environment deployment
- [operations/MONITORING_STRATEGY.md](operations/MONITORING_STRATEGY.md) - Observability patterns

### Development
- [development/code-quality-strategy.md](development/code-quality-strategy.md) - Three-ring type safety
- [development/GPU_SETUP_GUIDE.md](development/GPU_SETUP_GUIDE.md) - GPU environment setup

### Reports (Historical)
- [reports/MASCOT_HAPPINESS_REPORT.md](reports/MASCOT_HAPPINESS_REPORT.md) - Mascot collaboration assessment
- [reports/CODE_REVIEW_RESPONSE.md](reports/CODE_REVIEW_RESPONSE.md) - External code review analysis

## 📋 Documentation Standards

All reference documentation follows:

- **Naming**: ALL_CAPS.md for consistency
- **Status Headers**: Required on all active docs (Status, Type, Last Updated, Owner, Purpose)
- **Categories**: Clearly marked AS-IS (current), TO-BE (planned), or HISTORICAL (completed)
- **Practical Examples**: Working code samples with clear reasoning
- **Maintenance**: Future extension guidelines included

- **Measurable Results**: Before/after metrics where applicable

This documentation represents battle-tested patterns that successfully reduced type errors by 97% while maintaining full ML functionality.
