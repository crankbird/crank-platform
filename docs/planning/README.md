# Planning Directory

**Status**: Active  
**Purpose**: Bridge between raw ideas in `docs/proposals/` and executable work captured in `docs/issues/`.  
**Audience**: Humans + AI agents doing research, decomposition, or sequencing work for the platform backlog.

---

## When to Add a Planning Doc

Use this directory when you need to answer **“what has to be true before this issue can move?”** Typical cases:

- Background research or competitive analysis needed to unblock an issue (e.g. `test-data-corpus.md`)
- Decomposition notes that describe phased execution (e.g. `phase-3-controller-extraction.md`)
- Sprint playbooks and burn-down strategies (`issue-burn-down-sprints.md`)
- Agent-facing instructions that accelerate ongoing work but are not yet canonical standards

If a document is purely speculative or multi-quarter in scope, keep it in `docs/proposals/` until a concrete backlog item emerges. Once a plan is executed or superseded, archive it to `docs/archive/`.

---

## Document Types & Naming

| Type | Description | Naming Guidance |
|------|-------------|-----------------|
| **Background Brief** | Context, landscape studies, capability inventory | `topic-or-area.md` |
| **Execution Plan** | Step-by-step strategy for a specific issue or refactor phase | `phase-n-<focus>.md` |
| **Agent Instructions** | Temporary guardrails for AI/human collaborators | `agent-<topic>.md` |
| **Sprint/Burn-down** | How we retire a slice of the WIP | `issue-<id>-<short-name>.md` |

Favor kebab-case for ease of linking. Only promote a document to ALL_CAPS when it becomes a long-lived reference (then consider moving it to `docs/architecture/` or `docs/development/`).

---

## Workflow Handoff

1. **Proposal Captures the Idea** → high-level intent documented in `docs/proposals/`.
2. **Planning Adds Shape** → break intent into phases, dependencies, and data we need.
3. **Issue Captures Execution** → create/refresh `docs/issues/<topic>.md` with acceptance criteria and final state.
4. **Operations/Development Codify** → once stable, lift procedures or standards into `docs/operations/` or `docs/development/`.

This loop keeps the WIP list lean: planning files should either graduate (issue created), be archived (no longer relevant), or be superseded by updated plans.

---

## Maintaining the Directory

- Revisit documents at the start of each burn-down sprint; mark stale sections with `> NOTE: Needs refresh`.
- Link out to the specific proposal or issue at the top of every file to make lineage obvious.
- When pulling in outside research, summarize in-line and reference the original zettel or knowledge node so future agents can trace provenance.

**Goal**: Anyone landing here should know *why* the work matters, *what proof is needed*, and *how to turn it into executable issues* within a few minutes.
