# Proposals Directory

**Status**: Active  
**Purpose**: Capture strategic ideas, technical specifications, and future direction before they become executable work.  
**Audience**: Anyone exploring "what could we build?" or "how should this work?"

---

## Directory Organization

This directory uses a **flat structure with naming prefixes** instead of subdirectories:

- **No prefix**: Strategic/conceptual proposals (multi-quarter vision)
- **`faas-*`**: FaaS worker technical specifications
- **`identity-*`**: Identity and security quick-win improvements

**Why flat?** Easier navigation, clearer categorization, simpler for both humans and AI agents.

---

## When to Add a Proposal

Use this directory when you have:

- **Strategic vision** not yet tied to a specific quarter or team
- **Technical specifications** for future capabilities (FaaS workers, identity improvements)
- **Architectural exploration** that needs validation before planning
- **User scenarios** captured as Gherkin features

**NOT here**:
- Executable work breakdown → `docs/planning/`
- Active issue tracking → `docs/issues/`
- Operational procedures → `docs/operations/`
- Development guides → `docs/development/`

---

## Proposal Lifecycle

```text
1. Draft          → Initial idea captured in proposals/
2. Planning       → Decomposed in docs/planning/ with dependencies
3. Execution      → Tracked in docs/issues/ or GitHub Issues
4. Codification   → Mature procedures → docs/operations/ or docs/development/
5. Archive        → Completed/superseded → docs/archive/
```

**Handoff to Planning**: When a proposal has:
- Clear business value identified
- Technical feasibility validated
- Resource requirements estimated
- Dependencies mapped

Create a planning document that breaks it into phases and references the original proposal.

---

## Document Types

### Strategic Proposals (No Prefix)

**Examples**: `crank-mesh-access-model-evolution.md`, `enhancement-roadmap.md`

Long-term vision documents that:
- Span multiple quarters
- Define architectural direction
- Frame market positioning
- Don't have immediate execution plans

**Status**: Typically remain in proposals/ indefinitely as reference

---

### Technical Specifications (`faas-*`, `identity-*`)

**Examples**: `faas-worker-specification.md`, `identity-spiffe_id.md`

Detailed technical specs that:
- Define APIs or protocols
- Specify implementation requirements
- Provide guidelines for AI agents
- Support incremental improvements

**Status**: Move to `docs/architecture/` once implemented and stable

---

### User Scenarios (`*-gherkins.feature.md`)

**Example**: `crank-gherkins.feature.md`

Behavior-driven development scenarios that:
- Describe user-facing features
- Use Gherkin syntax (Given/When/Then)
- Drive integration testing
- Inform product requirements

**Status**: Reference indefinitely, update as features evolve

---

## Naming Conventions

- **kebab-case.md** for all filenames (easier linking)
- **Descriptive names** over abbreviations
- **Clear prefixes** for categorization (`faas-`, `identity-`)
- **Avoid numbered prefixes** (1_, 2_) — use descriptive names

**Good**: `identity-spiffe_id.md`, `faas-worker-specification.md`  
**Avoid**: `1_identity.md`, `spec.md`, `new-idea-v2.md`

---

## Master Index

See **[PROPOSALS_INDEX.md](PROPOSALS_INDEX.md)** for:
- Complete catalog of all proposals
- Status and timeline for each
- Cross-references to planning/issues
- Implementation priority matrix

The index is the authoritative reference — update it when adding or archiving proposals.

---

## Contribution Guidelines

### Adding a New Proposal

1. **Choose appropriate prefix** (or none for strategic)
2. **Use descriptive filename** following kebab-case convention
3. **Include frontmatter**:

   ```yaml
   ---
   title: Proposal Title
   status: Draft | Active | Archived
   timeline: Q1 2026 | Long-term | TBD
   related_docs:
     - path/to/related.md
   ---
   ```

4. **Update PROPOSALS_INDEX.md** with entry and cross-references
5. **Link to related proposals** within document body

### Promoting to Planning

When a proposal is ready for execution planning:

1. Create `docs/planning/phase-n-<focus>.md`
2. Reference original proposal at top
3. Break into executable phases
4. Map dependencies and blockers
5. Update proposal status to "In Planning"

### Archiving a Proposal

When a proposal is completed or superseded:

1. Move to `docs/archive/proposals/<year>/`
2. Update PROPOSALS_INDEX.md status to "Archived"
3. Add pointer in original location if highly referenced
4. Document outcome (implemented, superseded, abandoned)

---

## Cross-Directory Relationships

### Proposals → Planning

**Trigger**: Proposal gains concrete business case or technical validation

**Action**: Create planning document that references proposal and breaks into phases

**Example**: `enhancement-roadmap.md` (proposal) → `docs/planning/phase-3-controller-extraction.md`

---

### Proposals → Issues

**Trigger**: Planning phase results in specific executable work

**Action**: Create issue document or GitHub issue, link back to proposal

**Example**: `enterprise-security.md` (proposal) → `docs/issues/security-config-scattered.md` (Issue #19)

---

### Proposals → Architecture

**Trigger**: Technical spec is implemented and becomes stable reference

**Action**: Move spec to `docs/architecture/`, leave pointer in proposals

**Example**: FaaS spec → `docs/architecture/faas-worker-runtime.md` (future)

---

## Quality Standards

- **Clear value proposition**: Why does this matter?
- **Concrete enough to plan**: Can we break this into phases?
- **Abstract enough to evolve**: Not over-specified too early
- **Well-connected**: Links to related proposals, planning docs, issues
- **Agent-friendly**: AI agents can understand context and relationships

---

## Maintenance

- **Quarterly**: Review all proposals, update status, archive completed
- **Per proposal**: Update when new information emerges
- **Index sync**: Keep PROPOSALS_INDEX.md current with directory state

**Goal**: Proposals directory should be the "idea vault" — everything else is execution.

---

**Questions?** See [PROPOSALS_INDEX.md](PROPOSALS_INDEX.md) for catalog or `docs/planning/README.md` for workflow handoff.
