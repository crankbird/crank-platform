# ADR-0004: Prefer Local-First Agent Execution with Cloud Escalation

**Status**: Accepted
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Core Platform & Agent Architecture](../planning/adr-backlog-2025-11-16.md#core-platform--agent-architecture)

## Context and Problem Statement

AI agents can execute in various environments (local workstations, edge devices, cloud VMs). We need to decide where agent execution should occur by default and under what conditions to escalate to cloud resources. This affects latency, cost, privacy, and operational complexity.

## Decision Drivers

- Privacy: Keep sensitive data local when possible
- Cost: Cloud compute is expensive at scale
- Latency: Local execution is faster for user interactions
- Resource constraints: Not all local environments have GPU/sufficient RAM
- Developer experience: Local-first enables offline development
- Scalability: Cloud needed for burst workloads

## Considered Options

- **Option 1**: Local-first with cloud escalation (chosen)
- **Option 2**: Cloud-only execution
- **Option 3**: User-selectable per-agent

## Decision Outcome

**Chosen option**: "Local-first with cloud escalation", because it optimizes for privacy, cost, and latency while maintaining flexibility for resource-intensive workloads.

### Positive Consequences

- Data stays local by default (privacy win)
- Lower operational costs (no cloud charges for routine tasks)
- Faster response times for interactive agents
- Works offline for local-only capabilities
- Developer-friendly (develop without cloud dependencies)

### Negative Consequences

- Need robust capability detection (local vs cloud)
- Cloud escalation adds complexity to routing logic
- Resource exhaustion handling required
- Hybrid execution model harder to reason about

## Pros and Cons of the Options

### Option 1: Local-First with Cloud Escalation

Agents execute locally unless they need resources unavailable locally.

**Pros:**
- Privacy by default
- Low latency for local operations
- Cost-effective for routine workloads
- Offline capability
- Developer-friendly

**Cons:**
- Complexity in escalation logic
- Need capability discovery protocol
- Hybrid state management

### Option 2: Cloud-Only Execution

All agent execution happens in cloud infrastructure.

**Pros:**
- Simple deployment model
- Unlimited resources available
- Centralized monitoring/logging
- Consistent environment

**Cons:**
- High operational costs
- Privacy concerns (all data leaves device)
- Latency overhead
- Requires constant connectivity
- Not suitable for edge/mobile use cases

### Option 3: User-Selectable Per-Agent

Users choose execution location for each agent.

**Pros:**
- Maximum flexibility
- User controls privacy vs performance tradeoff
- Simple implementation (no auto-escalation)

**Cons:**
- Requires user to understand technical constraints
- Poor user experience (decision fatigue)
- Inconsistent behavior across agents
- Still need both local and cloud infrastructure

## Links

- [Related to] ADR-0001 (Controller/Worker model supports local execution)
- [Related to] ADR-0006 (Capability registry identifies available resources)
- [Related to] ADR-0007 (Message bus enables cloud escalation)
- [Related to] ADR-0023 (Capability publishing protocol drives placement data)

## Implementation Notes

**Escalation Triggers:**
- GPU required but not available locally
- Memory requirements exceed local capacity
- Long-running jobs (>10 minutes)
- Explicit user request for cloud execution

**Implementation:**
- Controller checks local capability registry
- If capability unavailable locally, routes to cloud mesh
- Cloud controller executes and returns results
- Transparent to agent code (routing layer handles it)

## Review History

- 2025-11-16 - Initial decision
