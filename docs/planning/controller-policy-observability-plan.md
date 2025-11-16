# Controller Policy Enforcement + Distributed Tracing Implementation Plan

**Status**: 🎯 Ready to Execute (Post-Phase 3)
**Blocks**: ADR-0027 acceptance, ADR-0024 full implementation
**Depends On**: Phase 3 Session 2 complete (controller service operational with basic tracing)
**Timeline**: 3-4 days

---

## Overview

Implement capability-based access control (CAP) using OPA and complete OpenTelemetry distributed tracing infrastructure. This work builds on Phase 3's basic tracing scaffolding and implements [ADR-0027](../decisions/0027-controller-policy-enforcement.md) plus the controller extensions in [ADR-0024](../decisions/0024-observability-strategy.md).

## Goals

- **CAP enforcement**: Workers can only invoke capabilities they declare
- **Zero-trust security**: SPIFFE identity + policy evaluation on every request
- **Distributed tracing**: W3C Trace Context propagation controller → workers
- **Audit trail**: All policy decisions logged
- **Observability backend**: Jaeger/Tempo integration for trace visualization

## Prerequisites

✅ **Phase 3 Session 2 Complete**:
- Controller service operational
- Basic OpenTelemetry instrumentation (console exporter)
- FastAPI auto-instrumentation working
- `/register`, `/heartbeat`, `/route` endpoints functional

## Implementation Sessions

### Session 1: OPA Deployment + SPIFFE Extraction (4 hours)

**Files to Create**:

```
policies/
  capability_access.rego       # Main CAP policy
  common.rego                  # Shared helper functions
  test_capability_access.rego  # Policy tests
  data/
    worker_manifests.json      # Worker capability declarations
    exceptions.json            # Temporary exceptions for migration

docker-compose.policy.yml      # OPA sidecar

src/crank/controller/
  policy_enforcer.py           # OPA client wrapper
  spiffe_utils.py              # SPIFFE ID extraction from certs

tests/unit/controller/
  test_policy_enforcer.py      # Unit tests
  test_spiffe_utils.py         # Unit tests
```

**OPA Deployment** (from ADR-0027):

```yaml
# docker-compose.policy.yml
version: '3.8'

services:
  controller:
    image: crank-controller:latest
    ports:
      - "9000:9000"
    environment:
      - OPA_URL=http://opa:8181
      - HTTPS_ONLY=true
    depends_on:
      - opa

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
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8181/health"]
      interval: 10s
      timeout: 5s
      retries: 3
```

**Main CAP Policy** (`policies/capability_access.rego`):

```rego
package crank.capability_access

import future.keywords.if
import future.keywords.in

# Default deny (zero-trust)
default allow := false

# Allow if worker has declared this capability in manifest
allow if {
    spiffe_id := input.identity.spiffe_id
    requested_capability := sprintf("%s:%s", [
        input.action.verb,
        input.action.capability
    ])

    worker := data.workers[spiffe_id]
    requested_capability in worker.required_capabilities
}

# Allow if worker has temporary exception (migration grace period)
allow if {
    spiffe_id := input.identity.spiffe_id
    exception := data.exceptions[spiffe_id]
    exception.temporary_allow_all == true
    exception.expires_after > time.now_ns()
}

# Deny with reason for audit trail
deny[reason] if {
    not allow
    reason := sprintf(
        "Worker %s not authorized for capability %s:%s",
        [
            input.identity.spiffe_id,
            input.action.verb,
            input.action.capability
        ]
    )
}
```

**Worker Manifest** (`policies/data/worker_manifests.json`):

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
        "convert:email_to_text"
      ],
      "owner": "ml-team",
      "deployed_at": "2025-11-16T10:00:00Z"
    }
  }
}
```

**SPIFFE Extraction** (`src/crank/controller/spiffe_utils.py`):

```python
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from fastapi import HTTPException, Request

def extract_spiffe_from_cert(request: Request) -> str:
    """Extract SPIFFE ID from client certificate SAN field."""
    cert_pem = request.scope.get("transport", {}).get("peercert")

    if not cert_pem:
        raise HTTPException(401, detail="client_certificate_required")

    cert = x509.load_pem_x509_certificate(
        cert_pem.encode(),
        default_backend()
    )

    try:
        san_ext = cert.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        )
        for name in san_ext.value:
            if isinstance(name, x509.UniformResourceIdentifier):
                uri = name.value
                if uri.startswith("spiffe://"):
                    return uri
    except x509.ExtensionNotFound:
        pass

    raise HTTPException(401, detail="spiffe_id_not_found_in_certificate")
```

**Policy Enforcer** (`src/crank/controller/policy_enforcer.py`):

```python
import httpx
from typing import Optional
from datetime import datetime

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
        policy_input = {
            "input": {
                "identity": {"spiffe_id": requester_spiffe_id},
                "action": {"verb": verb, "capability": capability},
                "context": {
                    "timestamp": datetime.now().isoformat(),
                    "source": "controller"
                }
            }
        }

        try:
            response = await self.client.post(
                f"{self.opa_url}/v1/data/crank/capability_access/allow",
                json=policy_input,
                timeout=0.1
            )
        except Exception as e:
            logger.error("opa_unreachable", error=str(e))
            # Fail closed: deny on policy engine error
            return False, "policy_engine_unavailable"

        if response.status_code != 200:
            return False, "policy_engine_error"

        result = response.json()
        allowed = result.get("result", False)

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
```

**Tests**:

```python
# OPA policy tests
def test_worker_allowed_declared_capability():
    # Run: opa test policies/ -v
    pass

def test_worker_denied_undeclared_capability():
    pass

def test_exception_allows_temporary():
    pass

# Python unit tests
@pytest.mark.asyncio
async def test_policy_enforcer_allows():
    enforcer = PolicyEnforcer(opa_url="http://localhost:8181")
    allowed, reason = await enforcer.check_policy(
        "spiffe://crank.local/worker/streaming",
        "stream",
        "text_events"
    )
    assert allowed
    assert reason is None

@pytest.mark.asyncio
async def test_policy_enforcer_denies():
    enforcer = PolicyEnforcer(opa_url="http://localhost:8181")
    allowed, reason = await enforcer.check_policy(
        "spiffe://crank.local/worker/streaming",
        "convert",  # Not declared in manifest
        "document_to_pdf"
    )
    assert not allowed
    assert "not authorized" in reason
```

**Definition of Done**:
- [ ] OPA sidecar runs via docker-compose
- [ ] CAP policy loads from `policies/capability_access.rego`
- [ ] Worker manifests loaded from JSON
- [ ] SPIFFE ID extraction works
- [ ] PolicyEnforcer queries OPA successfully
- [ ] OPA policy tests pass (`opa test policies/ -v`)
- [ ] Python unit tests pass
- [ ] Documentation: Policy authoring guide

---

### Session 2: Controller Policy Integration (3 hours)

**Files to Modify**:

```
services/crank_controller.py   # Add policy check to /route

tests/integration/
  test_policy_enforcement.py   # Integration tests
```

**Controller Integration**:

```python
from crank.controller.policy_enforcer import PolicyEnforcer
from crank.controller.spiffe_utils import extract_spiffe_from_cert

class ControllerService:
    def __init__(self):
        self.policy_enforcer = PolicyEnforcer(
            opa_url=os.getenv("OPA_URL", "http://localhost:8181")
        )
        self.registry = CapabilityRegistry()
        # ... other managers

    @app.post("/route")
    async def route(
        self,
        request: Request,
        verb: str,
        capability: str,
        idempotency_key: str | None = None,
        priority: str = "normal"
    ):
        # 1. Extract SPIFFE ID from mTLS cert
        spiffe_id = extract_spiffe_from_cert(request)

        # 2. Check policy (CAP enforcement)
        allowed, denial_reason = await self.policy_enforcer.check_policy(
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

            # Prometheus metric
            self.metrics.policy_denials.labels(
                capability=f"{verb}:{capability}"
            ).inc()

            raise HTTPException(
                status_code=403,
                detail={
                    "error": "capability_access_denied",
                    "reason": denial_reason,
                    "requester": spiffe_id,
                    "capability": f"{verb}:{capability}"
                }
            )

        # Policy allows, log for audit
        logger.info(
            "capability_access_allowed",
            requester=spiffe_id,
            capability=f"{verb}:{capability}"
        )

        # 3. Proceed with routing (existing logic)
        # ... idempotency check, SLO check, worker selection
```

**Prometheus Metrics**:

```python
from prometheus_client import Counter, Histogram

controller_policy_decisions = Counter(
    'controller_policy_decisions_total',
    'Policy decisions (allow/deny)',
    ['capability', 'decision']  # allow, deny
)

controller_policy_eval_duration = Histogram(
    'controller_policy_eval_duration_seconds',
    'Time to evaluate policy',
    ['capability']
)

controller_policy_denials = Counter(
    'controller_policy_denials_total',
    'Policy denials by capability',
    ['capability']
)
```

**Integration Tests**:

```python
@pytest.mark.asyncio
async def test_policy_allows_declared_capability():
    # Start controller + OPA
    response = await client.post(
        "/route",
        json={
            "verb": "stream",
            "capability": "text_events"
        },
        cert=("worker-streaming.crt", "worker-streaming.key")
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_policy_denies_undeclared_capability():
    response = await client.post(
        "/route",
        json={
            "verb": "convert",
            "capability": "document_to_pdf"
        },
        cert=("worker-streaming.crt", "worker-streaming.key")
    )
    assert response.status_code == 403
    assert "capability_access_denied" in response.json()["error"]

@pytest.mark.asyncio
async def test_policy_logs_audit_trail():
    # Make request
    await client.post("/route", ...)

    # Check structured log
    logs = capture_logs()
    assert any(
        log["event"] == "capability_access_allowed"
        for log in logs
    )
```

**Definition of Done**:
- [ ] `/route` endpoint checks policy before routing
- [ ] Allowed requests proceed normally
- [ ] Denied requests return 403 with reason
- [ ] All policy decisions logged for audit
- [ ] Prometheus metrics tracked
- [ ] Integration tests pass
- [ ] Performance: <10ms policy evaluation overhead

---

### Session 3: Jaeger/Tempo Backend Integration (4 hours)

**Files to Modify**:

```
services/crank_controller.py   # Switch from console to OTLP exporter
services/crank_*.py            # All 9 workers get OTLP exporter

docker-compose.observability.yml  # Jaeger + Tempo services

src/crank/worker_runtime/
  base_worker.py               # Add tracing setup helper
```

**Observability Stack** (extend existing `docker-compose.observability.yml`):

```yaml
version: '3.8'

services:
  # Existing: prometheus, grafana, loki

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
    environment:
      - COLLECTOR_OTLP_ENABLED=true
      - SPAN_STORAGE_TYPE=badger
      - BADGER_EPHEMERAL=false
      - BADGER_DIRECTORY_VALUE=/badger/data
      - BADGER_DIRECTORY_KEY=/badger/key
    volumes:
      - jaeger-data:/badger

  tempo:
    image: grafana/tempo:latest
    command: ["-config.file=/etc/tempo.yaml"]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml
      - tempo-data:/tmp/tempo
    ports:
      - "3200:3200"   # Tempo HTTP
      - "4317"        # OTLP gRPC (internal)

volumes:
  jaeger-data:
  tempo-data:
```

**Tempo Config** (`tempo.yaml`):

```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/traces

querier:
  frontend_worker:
    frontend_address: localhost:9095
```

**Controller OTLP Exporter**:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Setup tracer with OTLP export to Jaeger
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
    insecure=True  # Use TLS in production
)

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

# Add service name
from opentelemetry.sdk.resources import Resource

resource = Resource.create({"service.name": "crank-controller"})
trace.set_tracer_provider(TracerProvider(resource=resource))
```

**Worker Tracing Helper** (`src/crank/worker_runtime/base_worker.py`):

```python
class WorkerApplication:
    def setup_tracing(self):
        """Configure OpenTelemetry for worker."""
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter
        )
        from opentelemetry.sdk.resources import Resource

        resource = Resource.create({
            "service.name": f"crank-worker-{self.worker_id}"
        })

        trace.set_tracer_provider(TracerProvider(resource=resource))

        otlp_exporter = OTLPSpanExporter(
            endpoint=os.getenv(
                "OTEL_EXPORTER_OTLP_ENDPOINT",
                "http://localhost:4317"
            ),
            insecure=True
        )

        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(otlp_exporter)
        )

        self.tracer = trace.get_tracer(__name__)

    def run(self):
        self.setup_tracing()  # Call before starting
        # ... rest of run logic
```

**Trace Propagation** (controller → worker):

```python
from opentelemetry.propagate import inject

async def call_worker(worker: WorkerEndpoint, request: dict):
    """Call worker with trace context propagation."""
    headers = {}
    inject(headers)  # Adds traceparent, tracestate

    async with httpx.AsyncClient() as client:
        response = await client.post(
            worker.url,
            json=request,
            headers=headers,  # Propagate trace
            cert=(cert_path, key_path)
        )
    return response.json()
```

**Worker Trace Continuation**:

```python
from opentelemetry.propagate import extract

@app.post("/execute")
async def execute(request: Request, payload: dict):
    # Extract parent trace context
    context = extract(request.headers)

    with self.tracer.start_as_current_span(
        "worker_execute",
        context=context  # Child of controller span
    ) as span:
        span.set_attribute("worker_id", self.worker_id)
        result = await self.process(payload)
        return result
```

**Grafana Data Source**:

```yaml
# grafana/provisioning/datasources/tempo.yml
apiVersion: 1

datasources:
  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    jsonData:
      tracesToLogs:
        datasourceUid: loki
      tracesToMetrics:
        datasourceUid: prometheus
```

**Definition of Done**:
- [ ] Jaeger UI accessible at <http://localhost:16686>
- [ ] Controller sends spans to Jaeger
- [ ] All 9 workers send spans to Jaeger
- [ ] Trace context propagates controller → worker
- [ ] End-to-end trace visible in Jaeger UI
- [ ] Grafana shows traces linked to logs/metrics
- [ ] Documentation: Observability stack setup

---

### Session 4: Audit Logging + Migration Strategy (3 hours)

**Files to Create**:

```
policies/data/
  exceptions.json              # Migration grace period exceptions

scripts/
  generate_worker_manifest.py  # Auto-generate manifests from code

docs/operations/
  policy-migration-guide.md    # Migration playbook
  observability-guide.md       # Tracing/metrics guide
```

**Exception Management** (`policies/data/exceptions.json`):

```json
{
  "spiffe://crank.local/worker/legacy-service": {
    "temporary_allow_all": true,
    "expires_after": 1735689599000000000,
    "reason": "Migration grace period - expires 2025-12-31",
    "owner": "platform-team",
    "created_at": "2025-11-16T10:00:00Z"
  }
}
```

**Manifest Generator** (`scripts/generate_worker_manifest.py`):

```python
#!/usr/bin/env python3
"""
Generate worker manifest from worker code.
Scans worker for capability declarations.
"""
import json
import ast
from pathlib import Path

def extract_capabilities(worker_file: Path) -> list[str]:
    """Parse worker code to extract declared capabilities."""
    with open(worker_file) as f:
        tree = ast.parse(f.read())

    capabilities = []

    # Find CapabilitySchema declarations
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if getattr(node.func, 'id', None) == 'CapabilitySchema':
                # Extract verb and name
                for keyword in node.keywords:
                    if keyword.arg in ['verb', 'name']:
                        # ... extract values
                        pass

    return capabilities

def generate_manifest(worker_id: str, spiffe_id: str, worker_file: Path):
    """Generate manifest JSON."""
    capabilities = extract_capabilities(worker_file)

    manifest = {
        "worker_id": worker_id,
        "required_capabilities": capabilities,
        "owner": "auto-generated",
        "deployed_at": datetime.now().isoformat()
    }

    return {spiffe_id: manifest}

if __name__ == "__main__":
    # Scan all workers
    workers_dir = Path("services")
    manifests = {}

    for worker_file in workers_dir.glob("crank_*.py"):
        # ... generate manifest
        pass

    with open("policies/data/worker_manifests.json", "w") as f:
        json.dump({"workers": manifests}, f, indent=2)
```

**Audit Log Schema**:

```python
# All policy decisions logged with structured format
logger.info(
    "policy_decision",
    decision="allow",  # or "deny"
    requester_spiffe_id=spiffe_id,
    capability=f"{verb}:{capability}",
    policy_version="1.0.0",
    evaluation_time_ms=5.2,
    timestamp=datetime.now().isoformat(),
    trace_id=trace.get_current_span().get_span_context().trace_id
)
```

**Migration Playbook** (`docs/operations/policy-migration-guide.md`):

```markdown
# Policy Migration Guide

## Phase 1: Shadow Mode (Week 1-2)
- Deploy OPA with policies
- All workers get temporary exceptions
- Log all decisions, don't enforce
- Monitor for false positives

## Phase 2: Worker-by-Worker Migration (Week 3-6)
- Generate manifest for worker: `python scripts/generate_worker_manifest.py`
- Review manifest (verify capabilities correct)
- Remove exception for worker
- Monitor for denials (should be zero)
- Repeat for each worker

## Phase 3: Full Enforcement (Week 7+)
- Remove all exceptions
- New workers require manifest before deployment
- CI enforces manifest exists
- Alert on any policy denials
```

**Observability Guide** (`docs/operations/observability-guide.md`):

```markdown
# Observability Guide

## Accessing Traces
- Jaeger UI: http://localhost:16686
- Search by service: crank-controller, crank-worker-*
- Filter by operation: /route, /execute

## Linking Traces to Metrics
- Grafana exemplars link p95 latency → traces
- Click metric point → see trace causing slowness

## Debugging with Traces
1. Find slow request in Jaeger
2. See which worker took longest
3. Drill into worker span for details
4. Check linked logs for errors
```

**Definition of Done**:
- [ ] Exception management working
- [ ] Manifest generator script functional
- [ ] Audit logs include trace IDs
- [ ] Migration playbook documented
- [ ] Observability guide written
- [ ] All documentation reviewed

---

## Success Metrics

**Security**:
- [ ] CAP policy prevents unauthorized capability access
- [ ] SPIFFE ID extraction from all worker certs
- [ ] 100% of policy decisions logged for audit
- [ ] Zero unauthorized access in production

**Observability**:
- [ ] End-to-end traces visible in Jaeger
- [ ] Trace context propagates controller → workers
- [ ] Grafana links traces ↔ metrics ↔ logs
- [ ] <100ms trace processing latency

**Performance**:
- [ ] Policy evaluation <10ms (p95)
- [ ] Tracing overhead <5ms (p95)
- [ ] Total overhead <15ms for policy + tracing

**Operations**:
- [ ] Worker manifests auto-generated from code
- [ ] Migration playbook tested
- [ ] Exception management working
- [ ] CI enforces manifest exists for new workers

## Rollout Plan

**Week 1-2: Shadow Mode**
- Deploy OPA + Jaeger
- All workers get temporary exceptions
- Log decisions, don't enforce
- Tune policies based on logs

**Week 3-4: Initial Workers**
- Migrate hello_world (simplest)
- Migrate streaming
- Migrate document_conversion
- Verify zero denials

**Week 5-6: Remaining Workers**
- Migrate email_classifier
- Migrate semantic_search
- Migrate zettel workers (3)
- Migrate image_classifier

**Week 7+: Full Enforcement**
- Remove all exceptions
- CI enforces manifests
- Alert on denials
- ADR-0027 status → Accepted

## Next Steps

1. **Complete Phase 3 Session 2** (controller service operational)
2. **Execute Sessions 1-4** above
3. **Deploy observability stack** (Jaeger, Tempo, Grafana)
4. **Migrate workers** one by one
5. **Enable full enforcement**
6. **Update ADR-0027** status to Accepted

## References

- [ADR-0027](../decisions/0027-controller-policy-enforcement.md) - CAP/OPA policy enforcement
- [ADR-0024](../decisions/0024-observability-strategy.md) - Observability strategy + controller tracing
- [Enterprise Security Proposal](../proposals/enterprise-security.md) - CAP/OPA requirements
- [Enhancement Roadmap](../proposals/enhancement-roadmap.md) - Observability requirements
- [Mesh Access Model Evolution](../proposals/crank-mesh-access-model-evolution.md) - SPIFFE + capability tokens
- [Phase 3 Attack Plan](PHASE_3_ATTACK_PLAN.md) - Controller foundation
