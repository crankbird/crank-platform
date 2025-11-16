---
id: agent-orientation-master
title: "Agent Reorientation Protocol"
created: 2025-11-16
updated: 2025-11-16
type: meta-coordination
purpose: Enable naïve or freshly-pruned agents to quickly reorient using authoritative docs
schema: v1.0
---

# Agent Reorientation Protocol

## Purpose

This document exists to help AI coding agents (Agent13/Codex, Agent14/Sonnet, GitHub Copilot, future agents) **quickly rebuild context** after:

- Context window pruning
- Session termination
- Handoff between agents
- Major refactoring that changes mental models

**Core Principle**: Don't guess. Follow the graph.

---

## Document Universe: Mental Model

The Crank-Platform documentation forms a **directed graph** with explicit relationships:

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        UPSTREAM (Strategic)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐         ┌──────────────────┐                 │
│  │  Brand Science  │────────>│  Personas (UPN)  │                 │
│  │  Philosophy     │         │  Stakeholders    │                 │
│  └────────┬────────┘         └────────┬─────────┘                 │
│           │                           │                            │
│           └───────────┬───────────────┘                            │
│                       v                                            │
│           ┌───────────────────────┐                                │
│           │     Proposals         │                                │
│           │  (What could we do?)  │                                │
│           └───────────┬───────────┘                                │
│                       │ informs                                    │
├───────────────────────┼────────────────────────────────────────────┤
│                       v                                            │
│           ┌───────────────────────┐                                │
│           │        ADRs           │ <──── YOU ARE HERE             │
│           │  (What we decided)    │       (Start here for arch)   │
│           └───────────┬───────────┘                                │
│                       │ constrains                                 │
│           ┌───────────┴───────────┐                                │
│           v                       v                                │
│  ┌────────────────┐      ┌────────────────┐                       │
│  │   Planning     │      │  Agent Config  │                       │
│  │  (How to do)   │      │ (How agents    │                       │
│  └───────┬────────┘      │  should work)  │                       │
│          │               └────────────────┘                        │
├──────────┼──────────────────────────────────────────────────────  │
│          v                                                         │
│  ┌──────────────────────┐                                         │
│  │  Gherkin Features    │ <──── YOU ARE HERE (Start here for BDD) │
│  │  (How it behaves)    │                                         │
│  └──────────┬───────────┘                                         │
│             │ validates                                            │
├─────────────┼──────────────────────────────────────────────────── │
│             v                                                      │
│  ┌──────────────────────┐         ┌──────────────────┐           │
│  │   Implementation     │────────>│  Operations      │           │
│  │   (Code in src/)     │         │  (Runbooks)      │           │
│  └──────────────────────┘         └──────────────────┘           │
│                                                                    │
│                       DOWNSTREAM (Execution)                       │
└────────────────────────────────────────────────────────────────────┘
```

**Navigation Rule**: Start from your role (Architecture vs Behavior), follow explicit `adr_refs`, `feature_refs`, `knowledge_refs` links.

---

## Document Types & Relationships

### 1. Brand Science & Philosophy (`docs/knowledge/`)

**Purpose**: Strategic worldview, cognitive frameworks, market positioning

**Key Files**:
- `philosophy/governed-service-fabric-agentic-economy.md` - Core platform philosophy
- `brand-science/unified-persona-and-narrative-upn-a-framework-for-continuity.md` - UPN framework
- `brand-science/brand-to-demand-cognitive-continuum.md` - Market positioning

**Relationships**:
- **Informs** → Proposals (strategic direction)
- **Shapes** → Personas (stakeholder archetypes)
- **Constrains** → ADRs (architectural philosophy)

**Agent Use**: Read when understanding **why** a decision aligns with platform worldview (e.g., local-first, situated intelligence).

---

### 2. Personas (`docs/knowledge/personas/`)

**Purpose**: Stakeholder archetypes who already think in situated intelligence paradigm

**Format**: Zettel with YAML front-matter

**Key Personas**:
- `zk20251112-002_upn-systems-architect.md` - Distributed systems thinkers
- `zk20251112-003_upn-field-decision-maker.md` - Context-aware operators
- `zk20251112-010_upn-distributed-researcher.md` - Decentralized analysts

**Relationships**:
- **Informed by** → Brand Science
- **Referenced in** → Proposals, ADRs, Gherkin features
- **Validates** → User stories and behavioral specs

**Agent Use**: Read when understanding **who** benefits from a feature or decision.

---

### 3. Proposals (`docs/proposals/`)

**Purpose**: Upstream thinking before commitment - "We might do X for reason Y"

**Types**:
- Strategic proposals (no prefix) - Long-term vision
- Technical specs (`faas-*`, `identity-*`) - Detailed specifications
- Gherkin scenarios (`*-gherkins.feature.md`) - User scenarios

**Metadata** (front-matter):

```yaml
proposal_id: P-2025-11-faas-worker-spec
status: Active | Draft | Archived | Implemented
related_adrs: [0008, 0009, 0010]
related_features: [F-WORKER-SANDBOXING]
personas: [zk20251112-002]
```

**Relationships**:
- **Derived from** → Brand Science, Personas
- **Leads to** → ADRs (when decided)
- **References** → Planning docs

**Agent Use**: Read when a recent ADR references a proposal for historical context.

---

### 4. ADRs (`docs/decisions/`)

**Purpose**: Committed architectural decisions - "We decided X, here's why, here are consequences"

**Format**: Sequential numbered markdown (0001-NNNN-title.md)

**Metadata** (in `## Links` section):

```markdown
### Architecture References
- [Related to] ADR-0001
- [Refined by] ADR-0003

### Upstream Context
- [Derived from] P-2025-11-faas-worker-spec
- [Informed by] docs/knowledge/personas/zk20251112-002

### Behavioral Specifications
- [Validated by] F-CAPABILITY-ROUTING

### Agent Guidance
- [Constrains] .vscode/AGENT_CONTEXT.md#worker-development
```

**Relationships**:
- **Informed by** → Proposals, Brand Science, Personas
- **Constrains** → Planning, Implementation
- **Validated by** → Gherkin features
- **Guides** → Agent behavior

**Agent Use**: **Start here** when working on architecture. ADRs are the authoritative source of truth for "what we decided."

---

### 5. Planning (`docs/planning/`)

**Purpose**: Implementation breakdown - "How to execute the decision in phases"

**Key Files**:
- `phase-3-controller-extraction.md` - Current focus (Issue #30)
- `test-data-corpus.md` - Testing strategy

**Relationships**:
- **Derived from** → ADRs
- **References** → Issues (GitHub or `docs/issues/`)
- **Decomposed into** → Tasks, milestones

**Agent Use**: Read when understanding **what to build next** or **current project phase**.

---

### 6. Gherkin Features (`tests/bdd/features/`)

**Purpose**: Behavioral specifications - "Here's how X should behave for persona Y in context Z"

**Format**: Gherkin syntax with metadata header

**Metadata** (comment block):

```gherkin
# feature_id: F-CAPABILITY-ROUTING
# adr_refs: [0001, 0006, 0023]
# personas: [zk20251112-002]
# proposals: [P-2025-11-faas-worker-spec]
```

**Relationships**:
- **Constrained by** → ADRs (architecture limits behavior)
- **Informed by** → Personas (who is the user?)
- **Validates** → Implementation (BDD testing)

**Agent Use**: **Start here** when working on behavior/testing. Features describe expected outcomes.

---

### 7. Agent Instructions (`.vscode/`, `.github/`)

**Purpose**: Operational rules for AI agents working in this codebase

**Key Files**:
- `.vscode/AGENT_CONTEXT.md` - Comprehensive rules for all agents
- `.github/copilot-instructions.md` - GitHub Copilot specific

**Metadata** (header):

```yaml
agent_id: agent-platform-dev
authoritative_refs:
  adrs: [0001, 0002, 0003, ...]
  features: [F-CAPABILITY-ROUTING, ...]
  proposals: [P-2025-11-faas-worker-spec]
```

**Relationships**:
- **Constrained by** → ADRs (follow architectural decisions)
- **Informed by** → Gherkin features (understand expected behavior)
- **References** → This document (reorientation protocol)

**Agent Use**: **Start here** on session start. Agent config tells you your scope and authoritative refs.

---

## Reorientation Checklists

### Scenario A: Working on Architecture/Refactoring

**Context Lost**: You don't remember the current refactor phase or architectural constraints.

**Reorientation Protocol**:

1. ✅ **Read your agent config**: `.vscode/AGENT_CONTEXT.md`
   - Identifies current phase (e.g., "Phase 3 Ready - Controller extraction")
   - Lists authoritative ADRs

2. ✅ **Read relevant ADRs** (from agent config `adr_refs`):
   - Start with recent ADRs (0020+)
   - Follow backward through `[Related to]` links
   - Understand **what was decided** and **why**

3. ✅ **Check planning docs**:
   - `docs/planning/phase-3-controller-extraction.md` (current focus)
   - Understand **current phase** and **blockers**

4. ✅ **Verify with features**:
   - Check `tests/bdd/features/` for behavioral expectations
   - Ensure changes align with specified behavior

5. ✅ **Review anti-patterns**:
   - `.vscode/AGENT_CONTEXT.md#anti-patterns` section
   - Avoid deprecated patterns

**Example**:

```text
Agent: "I need to add a new worker capability."

1. Read .vscode/AGENT_CONTEXT.md
   → Phase 2 complete, use WorkerApplication pattern
   → ADRs: 0001 (controller/worker), 0009 (CPU/GPU), 0022 (agent-assisted)

2. Read ADR-0001
   → Workers are untrusted, controller is privileged
   → Capabilities drive routing

3. Read ADR-0009
   → Separate CPU and GPU workers
   → Determine if new capability needs GPU

4. Check tests/bdd/features/capability_routing.feature
   → Understand capability manifest format
   → Verify routing behavior expectations

5. Implement following WorkerApplication pattern
```

---

### Scenario B: Working on Behavior/Testing

**Context Lost**: You don't remember what behavior is expected or which personas matter.

**Reorientation Protocol**:

1. ✅ **Identify relevant feature**: `tests/bdd/features/*.feature`
   - Find feature closest to your work (e.g., `capability_routing.feature`)

2. ✅ **Read feature metadata** (header comments):
   - `adr_refs` → Which architectural decisions constrain this?
   - `personas` → Who is this for?
   - `proposals` → What was the original idea?

3. ✅ **Read referenced ADRs**:
   - Understand **architectural constraints**
   - Verify behavior aligns with decisions

4. ✅ **Read referenced personas**:
   - Understand **user mental model**
   - Validate scenarios match persona needs

5. ✅ **Check Brand Science** (if referenced):
   - Understand **strategic context**
   - Verify behavior aligns with platform philosophy

**Example**:

```text
Agent: "I need to write tests for capability routing."

1. Read tests/bdd/features/capability_routing.feature
   → Feature: Capability-driven routing
   → adr_refs: [0001, 0006, 0023]
   → personas: [zk20251112-002_upn-systems-architect]

2. Read ADR-0001 (Controller/Worker)
   → Controller routes based on capabilities
   → Workers advertise capabilities via manifest

3. Read ADR-0006 (Capability Registry)
   → Registry stores capability → worker mapping
   → Heartbeat keeps registry fresh

4. Read persona zk20251112-002
   → Systems architect who thinks "data gravity is real"
   → Expects intelligent routing, not random assignment

5. Write tests validating:
   - Exact capability match routing
   - Constraint satisfaction (gpu=true)
   - No route when capability unavailable
```

---

### Scenario C: Handoff Between Agents

**Context Lost**: Agent13 (Codex) started work, Agent14 (Sonnet) needs to continue.

**Reorientation Protocol**:

1. ✅ **Read handoff zettel** (if exists):
   - Check `docs/knowledge/zettels/` for recent context
   - Look for zettel from previous agent

2. ✅ **Read your agent config**: `.vscode/AGENT_CONTEXT.md`
   - Understand scope and constraints

3. ✅ **Check recent commits**:
   - `git log --oneline -10`
   - Look for ADR/Issue references in commit messages

4. ✅ **Follow ADR trail**:
   - Find most recent ADR mentioned in commits
   - Read ADR and follow `[Related to]` links

5. ✅ **Verify planning status**:
   - Check `docs/planning/` for current phase
   - Understand what's in-progress vs done

**Example**:

```text
Agent14 (Sonnet): "Agent13 was refactoring workers. What's the current state?"

1. Check docs/knowledge/zettels/agent13/
   → No recent zettel (context lost)

2. Read .vscode/AGENT_CONTEXT.md
   → Phase 2 complete: Base worker image + hybrid deployment
   → Phase 3 ready: Controller extraction

3. Check git log
   → "feat: consolidate security module (ADR-0003, Issue #19)"
   → "docs: create ADR backlog (ADR-0004 through ADR-0025)"

4. Read ADR-0003
   → Security module consolidated
   → All workers use WorkerApplication.run()
   → 675 lines deprecated code removed

5. Read docs/planning/phase-3-controller-extraction.md
   → Phase 3 not started yet
   → Foundation ready (capability schema, worker runtime)

6. Continue: Phase 3 is next logical step
```

---

## Quick Reference: Where to Start

| If you need to... | Start here |
|-------------------|------------|
| **Understand overall architecture** | `.vscode/AGENT_CONTEXT.md` → ADR-0001 → Follow `[Related to]` links |
| **Know what to build next** | `docs/planning/phase-3-controller-extraction.md` |
| **Understand why a decision was made** | `docs/decisions/README.md` → Find ADR → Read `## Context` |
| **Write behavioral tests** | `tests/bdd/features/` → Read feature → Follow `adr_refs` |
| **Understand user needs** | Feature `personas` ref → `docs/knowledge/personas/` |
| **Understand strategic context** | `docs/knowledge/brand-science/` or `philosophy/` |
| **Avoid deprecated patterns** | `.vscode/AGENT_CONTEXT.md#anti-patterns` |
| **Add new capability** | ADR-0001, ADR-0006, ADR-0023 → `tests/bdd/features/capability_routing.feature` |
| **Work with security** | ADR-0002, ADR-0003 → `tests/bdd/features/security_trust_mtls.feature` |
| **Deploy workers** | ADR-0010, ADR-0021 → `tests/bdd/features/deployment_models.feature` |

---

## Metadata Schema Reference

### ADR Links Section

```markdown
## Links

### Architecture References
- [Related to] ADR-NNNN (description)
- [Refined by] ADR-NNNN
- [Supersedes] ADR-NNNN

### Upstream Context
- [Derived from] P-YYYY-MM-proposal-id
- [Informed by] docs/knowledge/path/to/file.md

### Behavioral Specifications
- [Validated by] F-FEATURE-ID (tests/bdd/features/file.feature)

### Agent Guidance
- [Constrains] .vscode/AGENT_CONTEXT.md#section
```

### Proposal Front-Matter

```yaml
---
proposal_id: P-YYYY-MM-short-name
status: Active | Draft | Archived | Implemented
timeline: Q1 2026 | Long-term | TBD
related_adrs: [NNNN, NNNN]
related_features: [F-FEATURE-ID]
personas: [zk-id]
knowledge_refs:
  - docs/knowledge/path/to/file.md
---
```

### Gherkin Feature Header

```gherkin
# language: en
# feature_id: F-UPPERCASE-NAME
# adr_refs: [NNNN, NNNN]
# personas: [zk-id]
# proposals: [P-YYYY-MM-id]
# knowledge_refs: [path/to/file.md]

@tags @here
Feature: Title
```

### Agent Config Header

```yaml
---
agent_id: agent-name
scope: Description
authoritative_refs:
  adrs: [NNNN, NNNN, ...]
  features: [F-FEATURE-ID, ...]
  proposals: [P-YYYY-MM-id]
  knowledge:
    - docs/knowledge/path/to/file.md
reorientation_protocol: docs/knowledge/agent-orientation.md
---
```

---

## Maintenance Conventions

**When creating new ADR**:
1. Add `## Links` section with all relationships
2. Update related ADRs with back-references
3. Update features with new `adr_refs` if behavior changes

**When creating new proposal**:
1. Add front-matter with `proposal_id`
2. Update `docs/proposals/PROPOSALS_INDEX.md`
3. Reference related personas

**When creating new feature**:
1. Add header comments with metadata
2. Reference constraining ADRs
3. Reference relevant personas

**When updating agent config**:
1. Add new ADRs to `authoritative_refs`
2. Update scope if role changes
3. Keep anti-patterns current

---

## Philosophy

**Why this system?**

1. **Naïve agents can self-orient**: No human needed to explain context
2. **Explicit beats implicit**: Links are visible, not guessed
3. **Bounded maintenance**: Update only what changes, graph propagates context
4. **Lightweight**: Metadata is minimal, not burdensome
5. **Agent-friendly**: Clear navigation, no ambiguity

**What this is NOT**:

- ❌ A comprehensive knowledge graph (too heavy)
- ❌ A replacement for human judgment (augments, not replaces)
- ❌ A one-time migration (evolves incrementally)

**What this IS**:

- ✅ Explicit relationships between strategic thinking and implementation
- ✅ Fast reorientation after context loss
- ✅ Sustainable pattern that scales with project complexity

---

## Meta

**This document**:
- **Is** the authoritative reorientation guide
- **Should be** referenced in all agent configs
- **Will evolve** as the graph grows
- **Replaces** implicit "ask a human" patterns

**Last Updated**: 2025-11-16
**Maintained by**: Platform Team
**Referenced by**: `.vscode/AGENT_CONTEXT.md`, `.github/copilot-instructions.md`
