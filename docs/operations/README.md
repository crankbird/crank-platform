# Operations Directory

**Status**: Active, needs cleanup pass  
**Purpose**: Runbooks and patterns that keep the Crank Platform deployed, observable, and recoverable across environments.  
**Audience**: Operators, platform engineers, and AI agents executing day-2 tasks.

---

## Scope

Place a document here if it answers “How do we keep the platform healthy in production-like environments?”

- Deployment strategy across local → staging → production
- GitOps workflows and automation
- Monitoring/alerting/observability patterns
- Environment-specific configuration (ports, certificates, secrets distribution)
- Incident response guides and remediation checklists

Avoid storing speculative ideas or code-level design here—those belong in `docs/proposals/` or `docs/architecture/`. If a procedure is specific to developer workstations, prefer `docs/development/`.

---

## Current Contents

| File | Intent | Status |
|------|--------|--------|
| `GITOPS_WORKFLOW.md` | Repository-driven operations | Active |
| `PORT_CONFIGURATION_STRATEGY.md` | Canonical port map | Active |
| `PORT_CONFLICTS_RESOLVED.md` | Historical tracking of port clashes | Should merge with above |
| `AZURE_DEPLOYMENT.md` | Azure-specific deployment guide | Needs modernization |

**Next cleanup**: Merge the two port documents and either rename AZURE_DEPLOYMENT.md to be provider-neutral or clarify it's Azure-specific in a multi-cloud context.

---

## Naming & Capitalization Rules

- **Meta/runbook files**: `ALL_CAPS.md` (e.g., `DEPLOYMENT_STRATEGY.md`)
- **Environment-specific supplements**: `provider-topic.md` (lowercase), clearly marked as `Draft` until validated
- Prefix incident write-ups with the date: `2025-11-15-docker-permission-outage.md`

`README.md` files may use Title Case, but all operational standards should follow ALL_CAPS for fast scanning.

---

## Maintenance Checklist

- Verify every runbook quarterly; include `Last Reviewed` metadata.
- Link to supporting scripts or Terraform manifests rather than embedding long code blocks.
- When operational knowledge becomes automated (e.g., Terraform module, CI/CD pipeline), leave a short summary that points to the source of truth.

Keeping this directory curated prevents the drift that originally caused the “random capitalization” sprawl.
