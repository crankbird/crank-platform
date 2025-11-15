# Issues Directory

**Status**: Active WIP tracker  
**Purpose**: Canonical record of in-flight or recently resolved issues, including acceptance criteria, debugging notes, and links to related proposals/plans.  
**Audience**: Contributors and AI agents needing the latest state of work.

---

## How to Use This Directory

1. **One file per issue** using `issue-id-short-description.md` or a descriptive slug when the GitHub issue number is unknown.
2. **Frontmatter Block**: Start with `Title`, `Date`, `Owner`, `Status`, `Impact`, and `Related Work`.
3. **Sections to include**:
   - *Problem Statement / Symptoms*
   - *Root Cause & Analysis*
   - *Solution / Patch Summary*
   - *Verification / Tests*
   - *Follow-ups or linked planning documents*

Keep the tone factual and decision-focused—this directory is the source of truth for what was done, why, and whether it is complete.

---

## Relationship to Other Directories

- **`docs/proposals/`** captures long-lived ideas before they are staffed.
- **`docs/planning/`** decomposes a proposal into ready-to-execute work.
- **`docs/issues/`** records the actual execution and resolution narrative.
- **`docs/operations/` / `docs/development/`** inherit mature procedures or standards that emerged from an issue.

---

## Workflow Expectations

- Update the issue document whenever status changes (e.g., `In Progress → Blocked → Resolved`).
- Link specific commits or pull requests so later teams can trace the implementation.
- When opening a new GitHub issue, cross-link both directions to keep humans and agents aligned.

This keeps the WIP list intelligible and prevents historical regressions—if it is not documented here, it did not happen.
