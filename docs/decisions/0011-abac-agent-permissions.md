# ADR-0011: Attribute-Based Access Control (ABAC) for Agent Permissions

**Status**: Proposed
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Security & Governance](../planning/adr-backlog-2025-11-16.md#security--governance)

## Context and Problem Statement

Agents request capabilities (email classification, document conversion, web search) that have varying sensitivity levels and cost implications. We need to control which agents can invoke which capabilities based on attributes like user identity, agent purpose, data sensitivity, and resource cost.

## Decision Drivers

- Fine-grained control: Different agents need different permissions
- Dynamic policies: Permissions change based on context (time, location, cost)
- Auditability: Track who accessed what and why
- Least privilege: Agents get minimum necessary permissions
- Scalability: Policy model must scale to many agents/capabilities
- Future CAP integration: Aligns with Capability Access Policy architecture

## Considered Options

- **Option 1**: Attribute-Based Access Control (ABAC) - Proposed
- **Option 2**: Role-Based Access Control (RBAC)
- **Option 3**: Capability-based security tokens

## Decision Outcome

**Chosen option**: "Attribute-Based Access Control (ABAC)", because it provides the flexibility needed for dynamic agent permissions while supporting future Capability Access Policy integration.

### Positive Consequences

- Fine-grained authorization decisions
- Policy-as-code (OPA/Rego)
- Dynamic decisions based on context
- Audit trail of access decisions
- Aligns with zero-trust model
- Foundation for CAP (Q2-Q4 2026)

### Negative Consequences

- More complex than simple RBAC
- Policy authoring requires expertise
- Performance overhead per request
- Need policy management tooling
- Debugging policy failures harder

## Pros and Cons of the Options

### Option 1: Attribute-Based Access Control (ABAC)

Policies evaluate attributes of agent, capability, and context.

**Pros:**
- Maximum flexibility
- Context-aware decisions
- Policy-as-code
- Scales to complex scenarios
- Dynamic permissions

**Cons:**
- Complexity
- Policy authoring burden
- Performance overhead
- Debugging difficulty

### Option 2: Role-Based Access Control (RBAC)

Agents assigned roles, roles grant capability access.

**Pros:**
- Simple to understand
- Easy to implement
- Fast authorization checks
- Industry standard

**Cons:**
- Static role assignments
- Role explosion problem
- Can't handle context
- Not flexible enough for agents

### Option 3: Capability-Based Security Tokens

Agents hold unforgeable tokens granting capability access.

**Pros:**
- Delegation-friendly
- No central authority needed
- Fast checks (token validation)

**Cons:**
- Token management burden
- Revocation is hard
- Doesn't capture context
- Token distribution problem

## Links

- [Related to] `docs/security/CAPABILITY_ACCESS_POLICY_ARCHITECTURE.md` (Q2-Q4 2026)
- [Related to] ADR-0002 (mTLS provides agent identity for ABAC)
- [Enables] Fine-grained agent authorization

## Implementation Notes

**Policy Structure** (OPA/Rego):

```rego
package crank.authz

# Allow if agent has permission for capability
allow {
    agent_permitted(input.agent, input.capability)
    cost_within_budget(input.agent, input.capability)
    data_sensitivity_acceptable(input.agent, input.data_classification)
}

# Check if agent type permits capability
agent_permitted(agent, capability) {
    agent.type == "email-assistant"
    capability.verb == "classify_email"
}

agent_permitted(agent, capability) {
    agent.type == "document-assistant"
    capability.verb in ["convert_document", "extract_entities"]
}

# Check cost limits
cost_within_budget(agent, capability) {
    agent.cost_limit_usd >= capability.estimated_cost_usd
}

# Check data sensitivity
data_sensitivity_acceptable(agent, classification) {
    agent.clearance_level >= data_sensitivity_levels[classification]
}
```

**Authorization Request**:

```python
# Controller authorizes capability invocation
policy_input = {
    "agent": {
        "id": "agent-123",
        "type": "email-assistant",
        "user": "user@example.com",
        "cost_limit_usd": 10.0,
        "clearance_level": 2
    },
    "capability": {
        "verb": "classify_email",
        "estimated_cost_usd": 0.01,
        "resource_requirements": {"gpu": False}
    },
    "data_classification": "internal",
    "context": {
        "timestamp": "2025-11-16T10:00:00Z",
        "source": "local"
    }
}

decision = opa.evaluate("crank.authz.allow", policy_input)
if not decision:
    raise PermissionDenied("Agent not authorized for capability")
```

**Audit Log**:

```jsonl
{"ts":"2025-11-16T10:00:00Z","agent":"agent-123","capability":"classify_email","decision":"allow","reason":"agent_permitted"}
{"ts":"2025-11-16T10:05:00Z","agent":"agent-456","capability":"web_search","decision":"deny","reason":"cost_limit_exceeded"}
```

## Review History

- 2025-11-16 - Initial proposal
