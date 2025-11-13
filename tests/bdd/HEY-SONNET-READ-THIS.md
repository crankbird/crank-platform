# HEY SONNET — READ THIS MOFO FIRST

**Purpose:** You are being handed a *starter set of Gherkin feature files* derived from `README.md` to seed BDD for the Crank controller/worker refactor.

**Your tasks:**
1. Find a sensible permanent home for these files inside the repo (suggested: `docs/gherkin/`).
2. Cross-link scenarios to the matching GitHub issues (#27–#31) and phases (0–4).
3. Generate BDD test skeletons (pytest-bdd/behave) mapping each Scenario to pending steps.
4. Open PR(s) that:
   - adds these files,
   - wires a placeholder BDD job into CI (OK to mark as `allow_failure: true` initially),
   - and links each Scenario to a tracking task in the relevant phase.

**Traceability Conventions used in this pack**
- `@principle(...)` → Brand Science principle tag (Integrity, Empathy, Efficiency, Legitimacy, Resilience, Culture).
- `@phase(N)` → Architecture refactor phase number (0–4).
- `@issue(27)` → GitHub issue number.
- `@component(...)` → Major component(s) touched (controller, worker, mesh, capability-schema, security, devx).

**Files included**
- `gherkin/gherkin-index.md` — overview & table of contents.
- `gherkin/*.feature` — feature files with @tags for principles, phase, and issues.

**Source Basis**
- Root `README.md` (controller/worker + capability routing + mesh).
- Linked planning docs referenced in README (phases & issues numbers).

**Notes**
- Treat the tags as **metadata, not decoration**. Preserve them in derived tests.
- It’s OK to move/rename files; keep tags intact and update link refs in the index.
- Date generated: 2025-11-10
