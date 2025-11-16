# ADR Backlog – 2025-11-16

**Purpose**: Preserve the retrospective ADR backlog that triggered the November 2025 documentation push so every decision can reference a specific context document.  
**Source**: Governance request to formalise historical architectural decisions across Crank-Platform, Agent13/Agent14, Docforge, and Brand-Science tooling.

---

## Core Platform & Agent Architecture

- Prefer Local-First Agent Execution with Cloud Escalation
- Represent Agent and Platform State as File-Backed JSONL/YAML
- Introduce Verb/Capability Registry as the Integration Layer
- Standardise on Python as Primary Worker Runtime
- Separate CPU and GPU Workers with a Common Interface
- Use Containers as the Primary Deployment Unit
- Use Message-Bus–Backed Asynchronous Orchestration (technology TBD)

## Security & Governance

- Attribute-Based Access Control (ABAC) for Agent Permissions
- Default-Deny Network Egress for Agents and Workers
- Shift-Left Security Scanning in CI/CD (Trivy, CVE checks, etc.)
- Standardise Secrets Management Across Environments

## Documentation, Knowledge & Repo Structure

- Use ADRs as the Canonical Record of Architectural Decisions
- Consolidate Projects into a Mono-Repo for Crankbird
- Use Zettelkasten Notes with YAML Front-Matter as the Primary Knowledge System
- Use Docforge + Pandoc as the Semantic Document Rendering Layer
- Standardise Documentation Layout (proposals → decisions → planning → architecture → archive)

## Developer Experience & CI/CD

- Use Git-Based CI Pipelines as the Single Source of Automation
- Standardise Local Dev Environments (Mac + WSL + Containers)
- Adopt Agent-Assisted Development as a First-Class Workflow

## Platform Services / Extensions

- Define Capability Publishing Protocol for Workers and Agents
- Establish Observability Strategy (Logs, Metrics, Traces)
- Use Plugin-Based Extension Model for Agents (Agent13/14)
