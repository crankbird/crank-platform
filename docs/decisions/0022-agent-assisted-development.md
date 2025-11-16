# ADR-0022: Agent-Assisted Development as First-Class Workflow

**Status**: Accepted
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Developer Experience & CI/CD](../planning/adr-backlog-2025-11-16.md#developer-experience--ci-cd)

## Context and Problem Statement

AI coding agents (Agent13/Codex, Agent14/Sonnet) are used extensively in Crank Platform development for code generation, refactoring, documentation, and problem-solving. These agents need context about architecture, conventions, and ongoing work. How should we integrate AI agents into the development workflow?

## Decision Drivers

- Agent effectiveness: Provide good context
- Workflow integration: Agents as team members
- Knowledge persistence: Context survives sessions
- Convention enforcement: Agents follow standards
- Collaboration: Human-agent teamwork
- Quality: Agent output meets standards

## Considered Options

- **Option 1**: First-class agent workflow (instructions, context, mascots) - Accepted
- **Option 2**: Ad-hoc agent usage (no formal integration)
- **Option 3**: Agents for specific tasks only

## Decision Outcome

**Chosen option**: "First-class agent workflow", because treating AI agents as team members with proper context, instructions, and knowledge management significantly improves code quality, architectural consistency, and development velocity.

### Positive Consequences

- Agents produce better code with context
- Architectural decisions documented and followed
- Conventions enforced through instructions
- Knowledge persists across sessions
- Specialized testing (mascot framework)
- Human-agent collaboration patterns

### Negative Consequences

- Requires maintaining agent context documents
- Instruction files need updates
- Agent limitations need workarounds
- Quality still needs human review

## Pros and Cons of the Options

### Option 1: First-Class Agent Workflow

Formal integration with instructions, context, mascots.

**Pros:**
- Better agent output
- Context preservation
- Convention enforcement
- Specialized testing
- Knowledge persistence
- Collaboration patterns

**Cons:**
- Maintenance overhead
- Instruction updates needed
- Agent limitations
- Human review required

### Option 2: Ad-Hoc Agent Usage

Use agents without formal integration.

**Pros:**
- No overhead
- Flexible usage
- Quick answers

**Cons:**
- Inconsistent output
- No context preservation
- Conventions ignored
- Knowledge lost
- Quality issues

### Option 3: Agents for Specific Tasks Only

Limit agents to narrow use cases.

**Pros:**
- Controlled usage
- Clear boundaries
- Easy validation

**Cons:**
- Limited value
- Missed opportunities
- Still need instructions
- Fragmented knowledge

## Links

- [Related to] ADR-0015 (Use ADRs)
- [Related to] ADR-0017 (Zettelkasten knowledge system)
- [Implements] `.github/copilot-instructions.md`
- [Implements] `.vscode/AGENT_CONTEXT.md`
- [Implements] `mascots/` testing framework
- [Related to] Existing agents (Agent13/Codex, Agent14/Sonnet)

## Implementation Notes

**Agent Context Documents**:

```
.vscode/
  AGENT_CONTEXT.md              # Comprehensive rules and patterns

.github/
  copilot-instructions.md       # GitHub Copilot instructions

docs/
  architecture/                 # Canonical architecture
  decisions/                    # ADRs (architectural context)
  development/                  # Development guides

mascots/                        # Specialized testing personas
  wendy/                        # Security testing (rabbit)
  kevin/                        # Portability testing (llama)
```

**AGENT_CONTEXT.md Structure**:

```markdown
# Agent Context

## Architecture Overview
[Current phase, refactor status, key decisions]

## Core Patterns
[Worker development, security, type safety]

## Anti-Patterns
[What to avoid, why]

## File Locations
[Where to find key components]

## Troubleshooting
[Common issues and solutions]
```

**.github/copilot-instructions.md** (Platform-Specific):

```markdown
# Crank Platform - AI Coding Agent Instructions

## Essential Reading
- Primary agent context: `.vscode/AGENT_CONTEXT.md`
- Architecture roadmap: `docs/planning/phase-3-controller-extraction.md`

## Architecture: Controller/Worker Model (Active Refactor)
[Current phase, migration status]

## Development Patterns
[Package structure, worker development, type safety]

## Testing Framework
[Mascot-driven testing, standard testing]

## Deployment Patterns
[Environment commands, worker management]
```

**Mascot Testing Framework**:

Specialized AI personas for different testing concerns:

```python
# mascots/wendy/persona.yaml
name: Wendy the Security Rabbit
emoji: 🐰
focus: Security and zero-trust testing
expertise:
  - mTLS verification
  - Certificate validation
  - Attack surface analysis
  - Zero-trust principles
testing_approach: |
  Assume compromise, verify all trust boundaries,
  check certificate chains, validate encryption
```

```bash
# Run Wendy security tests
python scripts/run_mascot_tests.py --mascot wendy --target src/

# Run Kevin portability tests
python scripts/run_mascot_tests.py --mascot kevin --target services/

# Full council review
python scripts/run_mascot_tests.py --council --target .
```

**Agent Workflow Integration**:

1. **Context Loading**:

   ```bash
   # Before starting work
   cat .vscode/AGENT_CONTEXT.md
   cat docs/decisions/0001-use-controller-worker-model.md
   ```

2. **Following Patterns**:

   ```python
   # Agent reads AGENT_CONTEXT.md, follows worker pattern
   from crank.worker_runtime import WorkerApplication

   class MyWorker(WorkerApplication):
       def __init__(self):
           super().__init__(https_port=8500)

       # Agent knows to use this pattern from context
   ```

3. **Creating Documentation**:

   ```markdown
   <!-- Agent uses ADR template from docs/decisions/0000-template.md -->
   # ADR-NNNN: Decision Title

   **Status**: Proposed
   **Date**: 2025-11-16
   ...
   ```

4. **Testing**:

   ```bash
   # Agent suggests mascot testing for security changes
   python scripts/run_mascot_tests.py --mascot wendy --target src/crank/security/
   ```

**Knowledge Persistence** (Zettelkasten Integration):

```python
# Agent creates zettels to preserve knowledge
from crank.zettel import ZettelManager

zettel = ZettelManager(agent_id="agent14-sonnet")

# After solving problem
zettel.create_zettel(
    title="Controller Routing Algorithm",
    content="""
    ## Problem
    Need to route requests to capabilities.

    ## Solution
    Use capability registry with verb matching...
    """,
    tags=["routing", "controller", "capabilities"],
    related=["20251115-capability-schema"]
)
```

**Agent Collaboration Pattern**:

```
Human: "Refactor streaming worker to use WorkerApplication"

Agent14 (Sonnet):
1. Reads .vscode/AGENT_CONTEXT.md (sees worker pattern)
2. Reads services/crank_hello_world.py (reference implementation)
3. Checks docs/decisions/0002-enforce-mtls-everywhere.md (security requirement)
4. Refactors worker following pattern
5. Suggests: "Run mascot tests: wendy (security) + kevin (portability)"
6. Creates zettel: "20251116-streaming-refactor.md"
