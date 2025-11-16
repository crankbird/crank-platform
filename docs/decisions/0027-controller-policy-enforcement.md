# ADR-0027: Controller Policy Enforcement (CAP/OPA Integration)

**Status**: Proposed
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [Enterprise Security Proposal](../proposals/enterprise-security.md), [Mesh Access Model Evolution](../proposals/crank-mesh-access-model-evolution.md)

## Context and Problem Statement

In a zero-trust mesh, we need capability-based access control: workers should only invoke capabilities they legitimately need. A compromised worker must not be able to impersonate other services or access arbitrary capabilities. How should the controller enforce authorization before routing requests?

## Decision Drivers

- **Zero-trust security**: Never trust worker identity alone
- **Capability-based access**: Workers declare needed capabilities, controller enforces
- **Policy-as-code**: Authorization rules in version control
- **Audit trail**: Log all policy decisions
- **SPIFFE integration**: Tie capabilities to cryptographic identity
- **Flexibility**: Support complex policies (time-of-day, geo, SLO-based)

## Considered Options

- **Option 1**: OPA (Open Policy Agent) with Rego policies (chosen)
- **Option 2**: Custom authorization module in controller
- **Option 3**: Network-level firewall rules only

## Decision Outcome

**Chosen option**: "OPA with Rego policies", because it provides declarative, testable, version-controlled authorization logic. OPA is industry-standard, supports complex policies, and integrates cleanly with SPIFFE identity.

### Positive Consequences

- Declarative policy (Rego language)
- Version-controlled policies (Git)
- Policy testing framework (built into OPA)
- Audit trail (all decisions logged)
- SPIFFE identity integration
- Flexible policy evolution

### Negative Consequences

- OPA sidecar adds deployment complexity
- Learning curve for Rego language
- Performance overhead (5-10ms per policy evaluation)
- Policy authoring discipline required

## Pros and Cons of the Options

### Option 1: OPA with Rego Policies

External policy engine, policies written in Rego.

**Pros:**
- Industry standard
- Declarative policy language
- Rich testing framework
- Version control
- Audit logging
- Flexible (time, geo, SLO-based policies)
- SPIFFE integration

**Cons:**
- Deployment complexity (sidecar)
- Rego learning curve
- Performance overhead
- External dependency

### Option 2: Custom Authorization Module

Python code in controller.

**Pros:**
- No external dependency
- Familiar language (Python)
- Lower latency

**Cons:**
- No declarative policy
- Hard to test policies
- Difficult to audit
- Tightly coupled to controller
- No policy versioning
- Not reusable

### Option 3: Network-Level Firewall Only

Kubernetes NetworkPolicy or iptables.

**Pros:**
- Simple
- Fast
- Low-level enforcement

**Cons:**
- Network-centric not capability-centric
- No SPIFFE integration
- No fine-grained policies
- No audit trail
- Static rules

## Links

- [Refines] ADR-0001 (Controller/worker separation - controller is policy enforcement point)
- [Refines] ADR-0002 (mTLS foundation - identity verification before policy check)
- [Depends on] ADR-0023 (Capability Publishing - routing extended with policy check)
- [Related to] ADR-0011 (ABAC policies - OPA can enforce attribute-based access)
- [Enables] Enterprise security proposal (CAP enforcement)
- [Enables] Mesh access model evolution (SPIFFE + capability tokens)

## Implementation Notes

### Architecture

```
Request Flow:
1. Worker sends request to controller with mTLS cert
2. Controller extracts SPIFFE ID from cert
3. Controller calls OPA sidecar with (identity, action, resource)
4. OPA evaluates Rego policy, returns allow/deny
5. Controller routes (if allowed) or rejects (if denied)
6. Decision logged for audit
```

**OPA Sidecar Deployment**:

```yaml
# docker-compose.yml
services:
  controller:
    image: crank-controller:latest
    ports:
      - "9000:9000"
    environment:
      - OPA_URL=http://opa:8181

  opa:
    image: openpolicyagent/opa:latest
    ports:
      - "8181:8181"
    command:
      - "run"
      - "--server"
      - "--addr=0.0.0.0:8181"
      - "/policies"
    volumes:
      - ./policies:/policies:ro
```

### Policy Structure

**Directory Layout**:

```
policies/
  capability_access.rego       # Main CAP policy
  common.rego                  # Shared helper functions
  test_capability_access.rego  # Policy tests
  data/
    worker_manifests.json      # Worker capability declarations
    exceptions.json            # Policy exceptions
```

### Capability Access Policy (CAP)

**Main Policy** (`policies/capability_access.rego`):

```rego
package crank.capability_access

import future.keywords.if
import future.keywords.in

# Default deny
default allow := false

# Allow if worker has declared this capability in its manifest
allow if {
    # Extract requester SPIFFE ID
    spiffe_id := input.identity.spiffe_id

    # Extract requested capability
    requested_capability := sprintf("%s:%s", [input.action.verb, input.action.capability])

    # Load worker manifest
    worker := data.workers[spiffe_id]

    # Check if worker declared this capability
    requested_capability in worker.required_capabilities
}

# Allow if worker is in exception list (for migration period)
allow if {
    spiffe_id := input.identity.spiffe_id
    exception := data.exceptions[spiffe_id]
    exception.temporary_allow_all == true
    exception.expires_after > time.now_ns()
}

# Deny with reason for audit trail
deny[reason] {
    not allow
    reason := sprintf(
        "Worker %s not authorized for capability %s:%s",
        [input.identity.spiffe_id, input.action.verb, input.action.capability]
    )
}
```

### Worker Manifest Format

**Worker declares needed capabilities** (`policies/data/worker_manifests.json`):

```json
{
  "workers": {
    "spiffe://crank.local/worker/streaming": {
      "worker_id": "worker-streaming",
      "required_capabilities": [
        "stream:text_events",
        "stream:sse_events"
      ],
      "owner": "streaming-team",
      "deployed_at": "2025-11-16T10:00:00Z"
    },
    "spiffe://crank.local/worker/email-classifier": {
      "worker_id": "worker-email-classifier",
      "required_capabilities": [
        "classify:email_category",
        "classify:spam_detection",
        "convert:email_to_text"  # Needs document conversion
      ],
      "owner": "ml-team",
      "deployed_at": "2025-11-16T10:00:00Z"
    },
    "spiffe://crank.local/worker/document-conversion": {
      "worker_id": "worker-document-conversion",
      "required_capabilities": [
        "convert:document_to_pdf",
        "convert:pdf_to_text",
        "convert:html_to_pdf"
      ],
      "owner": "document-team",
      "deployed_at": "2025-11-16T10:00:00Z"
    }
  }
}
```

### Controller Integration

```python
import httpx
from typing import Optional

class PolicyEnforcer:
    def __init__(self, opa_url: str = "http://localhost:8181"):
        self.opa_url = opa_url
        self.client = httpx.AsyncClient()

    async def check_policy(
        self,
        requester_spiffe_id: str,
        verb: str,
        capability: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check OPA policy.
        Returns (allowed: bool, denial_reason: str | None)
        """
        # Build OPA input
        policy_input = {
            "input": {
                "identity": {
                    "spiffe_id": requester_spiffe_id
                },
                "action": {
                    "verb": verb,
                    "capability": capability
                },
                "context": {
                    "timestamp": datetime.now().isoformat(),
                    "source": "controller"
                }
            }
        }

        # Query OPA
        response = await self.client.post(
            f"{self.opa_url}/v1/data/crank/capability_access/allow",
            json=policy_input,
            timeout=0.1  # 100ms timeout
        )

        if response.status_code != 200:
            logger.error(
                "opa_policy_check_failed",
                status_code=response.status_code,
                error=response.text
            )
            # Fail closed: deny on policy engine error
            return False, "policy_engine_unavailable"

        result = response.json()
        allowed = result.get("result", False)

        # Get denial reason if denied
        denial_reason = None
        if not allowed:
            deny_response = await self.client.post(
                f"{self.opa_url}/v1/data/crank/capability_access/deny",
                json=policy_input
            )
            if deny_response.status_code == 200:
                reasons = deny_response.json().get("result", [])
                denial_reason = reasons[0] if reasons else "policy_denied"

        return allowed, denial_reason

# Integration into routing
@app.post("/route")
async def route(
    request: Request,
    verb: str,
    capability: str
):
    # Extract SPIFFE ID from mTLS cert
    spiffe_id = extract_spiffe_from_cert(request)

    # Check policy (CAP enforcement)
    allowed, denial_reason = await policy_enforcer.check_policy(
        requester_spiffe_id=spiffe_id,
        verb=verb,
        capability=capability
    )

    if not allowed:
        # Log denial for audit
        logger.warning(
            "capability_access_denied",
            requester=spiffe_id,
            capability=f"{verb}:{capability}",
            reason=denial_reason
        )

        # Return 403 Forbidden
        raise HTTPException(
            status_code=403,
            detail={
                "error": "capability_access_denied",
                "reason": denial_reason,
                "requester": spiffe_id,
                "capability": f"{verb}:{capability}"
            }
        )

    # Policy allows, proceed with routing
    worker = registry.route(verb, capability)
    # ... rest of routing logic
```

### SPIFFE ID Extraction

```python
from cryptography import x509
from cryptography.hazmat.backends import default_backend

def extract_spiffe_from_cert(request: Request) -> str:
    """Extract SPIFFE ID from client certificate SAN field."""
    # FastAPI provides client cert in request scope
    cert_pem = request.scope.get("transport", {}).get("peercert")

    if not cert_pem:
        raise HTTPException(401, "client_certificate_required")

    # Parse certificate
    cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())

    # Extract SAN (Subject Alternative Name)
    try:
        san_ext = cert.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        )
        # Find URI SAN (SPIFFE ID)
        for name in san_ext.value:
            if isinstance(name, x509.UniformResourceIdentifier):
                uri = name.value
                if uri.startswith("spiffe://"):
                    return uri
    except x509.ExtensionNotFound:
        pass

    raise HTTPException(401, "spiffe_id_not_found_in_certificate")
```

### Policy Testing

**OPA Test Suite** (`policies/test_capability_access.rego`):

```rego
package crank.capability_access

test_worker_allowed_declared_capability {
    allow with input as {
        "identity": {"spiffe_id": "spiffe://crank.local/worker/streaming"},
        "action": {"verb": "stream", "capability": "text_events"}
    }
    with data.workers as {
        "spiffe://crank.local/worker/streaming": {
            "required_capabilities": ["stream:text_events"]
        }
    }
}

test_worker_denied_undeclared_capability {
    not allow with input as {
        "identity": {"spiffe_id": "spiffe://crank.local/worker/streaming"},
        "action": {"verb": "convert", "capability": "document_to_pdf"}
    }
    with data.workers as {
        "spiffe://crank.local/worker/streaming": {
            "required_capabilities": ["stream:text_events"]
        }
    }
}

test_exception_allows_temporary {
    allow with input as {
        "identity": {"spiffe_id": "spiffe://crank.local/worker/legacy"},
        "action": {"verb": "any", "capability": "anything"}
    }
    with data.exceptions as {
        "spiffe://crank.local/worker/legacy": {
            "temporary_allow_all": true,
            "expires_after": 9999999999999999999
        }
    }
    with time.now_ns as 1000000000
}
```

**Run Tests**:

```bash
# Run OPA policy tests
opa test policies/ -v

# Expected output:
# PASS: 12/12
```

### CI Integration

```yaml
# .github/workflows/policy-check.yml
name: Policy Validation

on: [push, pull_request]

jobs:
  policy-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install OPA
        run: |
          curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64
          chmod +x opa

      - name: Run policy tests
        run: |
          ./opa test policies/ -v

      - name: Check policy format
        run: |
          ./opa fmt --fail policies/*.rego
```

### Audit Logging

**Structured Audit Log**:

```python
# All policy decisions logged
logger.info(
    "policy_decision",
    decision="allow",  # or "deny"
    requester_spiffe_id=spiffe_id,
    capability=f"{verb}:{capability}",
    policy_version="1.2.3",
    evaluation_time_ms=5.2,
    timestamp=datetime.now().isoformat()
)

# Denials include reason
logger.warning(
    "policy_decision",
    decision="deny",
    requester_spiffe_id=spiffe_id,
    capability=f"{verb}:{capability}",
    denial_reason=denial_reason,
    policy_version="1.2.3",
    evaluation_time_ms=3.8,
    timestamp=datetime.now().isoformat()
)
```

**Audit Dashboard** (Grafana query):

```promql
# Policy denial rate
rate(controller_policy_denials_total[5m])

# Slowest policy evaluations
histogram_quantile(0.99,
  rate(controller_policy_eval_duration_seconds_bucket[5m])
)

# Top denied capabilities
topk(10,
  sum by (capability) (
    rate(controller_policy_denials_total[1h])
  )
)
```

### Migration Strategy

**Phase 1**: Shadow mode (log only, don't enforce)

```rego
# In policy file
default enforce := false  # Shadow mode

allow {
    # ... policy logic
}

# Always allow in shadow mode, but log decision
final_decision := true if {
    not enforce
}
```

**Phase 2**: Enforcement with exceptions

```json
// exceptions.json
{
  "spiffe://crank.local/worker/legacy-service": {
    "temporary_allow_all": true,
    "expires_after": "2025-12-31T23:59:59Z",
    "reason": "Migration grace period"
  }
}
```

**Phase 3**: Full enforcement
- Remove exceptions
- Set `default enforce := true`
- Monitor denial rate

## Review History

- 2025-11-16 - Initial proposal

## Next Steps

1. Deploy OPA sidecar in Phase 3 Session 2
2. Implement SPIFFE ID extraction from mTLS certs
3. Create initial CAP policy in Rego
4. Add policy check to `/route` endpoint
5. Create worker manifest schema
6. Implement audit logging for policy decisions
7. Create migration plan (shadow → exceptions → enforcement)
8. Document policy authoring guidelines
