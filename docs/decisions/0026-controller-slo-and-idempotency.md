# ADR-0026: Controller-Level SLO Enforcement and Idempotency Manager

**Status**: Proposed
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [Enhancement Roadmap - Enterprise Readiness](../proposals/enhancement-roadmap.md#enterprise-readiness-new--high-priority)

## Context and Problem Statement

Enterprise deployments require Service Level Objectives (SLOs) with error budgets and request idempotency to prevent double-billing on retries. The controller is the natural enforcement point for both. How should we implement SLO tracking and request deduplication at the controller layer?

## Decision Drivers

- **SLO enforcement**: Latency (p50/p95/p99), availability, error budget tracking
- **CI integration**: Fail builds on SLO regression
- **Idempotency**: Prevent duplicate execution on retry (1-hour dedup window)
- **Performance**: Minimal overhead on routing path (<5ms)
- **Observability**: Dashboard integration (Grafana/Datadog)
- **Billing protection**: No double-charges for retried requests

## Considered Options

- **Option 1**: Controller-owned YAML SLO files + in-memory idempotency cache (chosen)
- **Option 2**: Worker-level SLO enforcement + external cache (Redis)
- **Option 3**: No formal SLOs, best-effort only

## Decision Outcome

**Chosen option**: "Controller-owned YAML SLO files + in-memory idempotency cache", because the controller sees all routing decisions and can enforce SLOs uniformly. In-memory cache is fast enough for 1-hour TTL and avoids external dependencies.

### Positive Consequences

- Single enforcement point (controller)
- Version-controlled SLO definitions (Git)
- CI can validate SLO compliance
- Fast idempotency checks (in-memory hash map)
- No external cache dependency
- Prevents double-billing

### Negative Consequences

- SLO files must be kept in sync with capabilities
- In-memory cache lost on controller restart (acceptable for 1-hour TTL)
- SLO violations discovered at runtime, not deployment time
- Cache memory footprint (mitigated by TTL + LRU eviction)

## Pros and Cons of the Options

### Option 1: Controller-Owned YAML SLO Files + In-Memory Cache

Controller enforces SLO targets defined in YAML, maintains idempotency cache.

**Pros:**
- Central enforcement point
- Version-controlled SLO definitions
- Fast cache access (in-memory)
- No external dependencies
- CI integration straightforward
- Dashboard-friendly (Prometheus metrics)

**Cons:**
- SLO sync with capabilities
- Cache lost on restart
- Memory footprint
- Requires SLO authoring discipline

### Option 2: Worker-Level SLO Enforcement + External Cache (Redis)

Each worker tracks own SLOs, Redis for deduplication.

**Pros:**
- Distributed enforcement
- Persistent cache (Redis)
- Workers own SLOs

**Cons:**
- No global view (controller blind)
- Redis dependency
- Complex coordination
- Harder to enforce uniformly
- Higher latency (network cache)

### Option 3: No Formal SLOs

Best-effort monitoring only.

**Pros:**
- Simple
- No overhead

**Cons:**
- No error budgets
- No regression detection
- No idempotency guarantees
- Not enterprise-ready

## Links

- [Refines] ADR-0023 (Capability Publishing Protocol - routing extended with SLO awareness)
- [Depends on] ADR-0024 (Observability - metrics for SLO tracking)
- [Related to] Enhancement Roadmap (enterprise readiness requirements)
- [Enables] Multi-tenant billing (idempotency prevents double-charges)

## Implementation Notes

### SLO File Format

**Location**: `state/controller/slos/{capability-name}.yml`

**Schema**:

```yaml
# state/controller/slos/convert_document_to_pdf.yml
capability:
  verb: convert
  name: convert_document_to_pdf
  version: "1.0"

slo:
  latency:
    p50_ms: 50      # 50th percentile target
    p95_ms: 100     # 95th percentile target
    p99_ms: 200     # 99th percentile target
  availability:
    target: 0.999   # 99.9% uptime
  error_budget:
    monthly_pct: 0.1  # 0.1% error budget per month
    alerts:
      - threshold: 0.5  # Alert at 50% budget consumed
        channel: slack
      - threshold: 0.9  # Page at 90% budget consumed
        channel: pagerduty

enforcement:
  reject_on_violation: false  # Log only or reject requests
  grace_period_days: 7        # Allow violations for N days (new capabilities)

metadata:
  owner: document-team
  cost_center: engineering
  tier: production  # production, staging, development
```

### Idempotency Manager

**Data Structure**:

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib

@dataclass
class CachedResult:
    idempotency_key: str
    result: dict
    timestamp: datetime
    worker_id: str
    capability: str

class IdempotencyManager:
    def __init__(self, ttl_seconds: int = 3600):
        self._cache: dict[str, CachedResult] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
        self._max_size = 10_000  # LRU eviction above this

    def check_duplicate(self, idempotency_key: str) -> CachedResult | None:
        """Return cached result if exists and not expired."""
        if idempotency_key in self._cache:
            cached = self._cache[idempotency_key]
            if datetime.now() - cached.timestamp < self._ttl:
                return cached
            else:
                # Expired, remove
                del self._cache[idempotency_key]
        return None

    def cache_result(
        self,
        idempotency_key: str,
        result: dict,
        worker_id: str,
        capability: str
    ) -> None:
        """Store result for future duplicate detection."""
        # LRU eviction if cache too large
        if len(self._cache) >= self._max_size:
            # Remove oldest 10%
            sorted_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k].timestamp
            )
            for key in sorted_keys[:self._max_size // 10]:
                del self._cache[key]

        self._cache[idempotency_key] = CachedResult(
            idempotency_key=idempotency_key,
            result=result,
            timestamp=datetime.now(),
            worker_id=worker_id,
            capability=capability
        )

    def cleanup_expired(self) -> int:
        """Remove expired entries, return count removed."""
        now = datetime.now()
        expired = [
            key for key, cached in self._cache.items()
            if now - cached.timestamp >= self._ttl
        ]
        for key in expired:
            del self._cache[key]
        return len(expired)
```

### Controller Integration

**Routing with SLO + Idempotency**:

```python
class ControllerService:
    def __init__(self):
        self.slo_manager = SLOManager(slo_dir="state/controller/slos")
        self.idempotency_mgr = IdempotencyManager(ttl_seconds=3600)
        self.registry = CapabilityRegistry()

    @app.post("/route")
    async def route(
        self,
        verb: str,
        capability: str,
        idempotency_key: str | None = None,
        request_payload: dict = {}
    ):
        capability_name = f"{verb}:{capability}"

        # 1. Check idempotency (if key provided)
        if idempotency_key:
            cached = self.idempotency_mgr.check_duplicate(idempotency_key)
            if cached:
                logger.info(
                    "idempotent_request_replayed",
                    idempotency_key=idempotency_key,
                    original_worker=cached.worker_id,
                    age_seconds=(datetime.now() - cached.timestamp).seconds
                )
                return JSONResponse(
                    cached.result,
                    headers={"X-Idempotent-Replay": "true"}
                )

        # 2. Load SLO (if exists)
        slo = self.slo_manager.get_slo(capability_name)

        # 3. Find workers
        workers = self.registry.get_workers_for_capability(capability_name)
        healthy = [w for w in workers if w.is_healthy()]

        # 4. SLO-aware filtering (if SLO defined)
        if slo and slo.enforcement.reject_on_violation:
            # Check current performance vs SLO
            current_p95 = self.metrics.get_latency_p95(capability_name)
            if current_p95 > slo.latency.p95_ms:
                # Over SLO, reject low-priority requests
                if request_payload.get("priority", "normal") == "low":
                    raise HTTPException(
                        503,
                        detail="SLO violation: rejecting low-priority requests"
                    )

        # 5. Route to worker (same as before)
        if not healthy:
            raise HTTPException(503, detail="no_worker_available")

        worker = healthy[0]  # Simple: first available

        # 6. Execute request (simplified, actual impl calls worker)
        result = await self._call_worker(worker, request_payload)

        # 7. Cache result if idempotency key provided
        if idempotency_key:
            self.idempotency_mgr.cache_result(
                idempotency_key=idempotency_key,
                result=result,
                worker_id=worker.worker_id,
                capability=capability_name
            )

        # 8. Track metrics for SLO
        if slo:
            self.metrics.record_request(
                capability=capability_name,
                latency_ms=result.get("duration_ms", 0),
                success=result.get("status") == "success"
            )

        return result
```

### SLO Manager

```python
import yaml
from pathlib import Path

class SLOManager:
    def __init__(self, slo_dir: str):
        self.slo_dir = Path(slo_dir)
        self.slos: dict[str, SLODefinition] = {}
        self._load_all()

    def _load_all(self):
        """Load all YAML SLO files on startup."""
        if not self.slo_dir.exists():
            logger.warning(f"SLO directory {self.slo_dir} does not exist")
            return

        for slo_file in self.slo_dir.glob("*.yml"):
            with open(slo_file) as f:
                data = yaml.safe_load(f)
                slo = SLODefinition(**data)
                capability_name = f"{slo.capability.verb}:{slo.capability.name}"
                self.slos[capability_name] = slo
                logger.info(
                    "slo_loaded",
                    capability=capability_name,
                    p95_target=slo.slo.latency.p95_ms
                )

    def get_slo(self, capability_name: str) -> SLODefinition | None:
        return self.slos.get(capability_name)

    def check_compliance(self, capability_name: str, metrics: dict) -> bool:
        """Check if current metrics meet SLO."""
        slo = self.get_slo(capability_name)
        if not slo:
            return True  # No SLO defined = compliant

        # Check latency
        if metrics.get("p95_ms", 0) > slo.slo.latency.p95_ms:
            return False

        # Check availability
        if metrics.get("availability", 1.0) < slo.slo.availability.target:
            return False

        return True
```

### CI Integration

**SLO Regression Check** (`scripts/check_slo_compliance.py`):

```python
#!/usr/bin/env python3
"""
Check if current metrics violate SLO definitions.
Exit 1 if any SLO violated, 0 otherwise.
"""
import sys
from pathlib import Path
import yaml

def check_slo_compliance(slo_dir: Path, metrics_file: Path) -> bool:
    """Return True if all SLOs met."""
    with open(metrics_file) as f:
        metrics = yaml.safe_load(f)

    violations = []

    for slo_file in slo_dir.glob("*.yml"):
        with open(slo_file) as f:
            slo = yaml.safe_load(f)

        capability = f"{slo['capability']['verb']}:{slo['capability']['name']}"
        cap_metrics = metrics.get(capability, {})

        # Check p95 latency
        p95_actual = cap_metrics.get("p95_ms", 0)
        p95_target = slo["slo"]["latency"]["p95_ms"]
        if p95_actual > p95_target:
            violations.append(
                f"{capability}: p95 latency {p95_actual}ms > target {p95_target}ms"
            )

        # Check availability
        avail_actual = cap_metrics.get("availability", 1.0)
        avail_target = slo["slo"]["availability"]["target"]
        if avail_actual < avail_target:
            violations.append(
                f"{capability}: availability {avail_actual} < target {avail_target}"
            )

    if violations:
        print("❌ SLO violations detected:")
        for v in violations:
            print(f"  - {v}")
        return False
    else:
        print("✅ All SLOs met")
        return True

if __name__ == "__main__":
    slo_dir = Path("state/controller/slos")
    metrics_file = Path("test-results/metrics.yml")

    if not metrics_file.exists():
        print(f"⚠️  Metrics file {metrics_file} not found, skipping SLO check")
        sys.exit(0)

    compliant = check_slo_compliance(slo_dir, metrics_file)
    sys.exit(0 if compliant else 1)
```

**GitHub Actions Workflow**:

```yaml
# .github/workflows/slo-check.yml
name: SLO Compliance Check

on: [push, pull_request]

jobs:
  slo-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run integration tests with metrics
        run: |
          pytest --metrics-output=test-results/metrics.yml

      - name: Check SLO compliance
        run: |
          python scripts/check_slo_compliance.py
```

### Prometheus Metrics for SLO Tracking

```python
from prometheus_client import Histogram, Counter, Gauge

# Latency histogram for SLO tracking
controller_routing_duration = Histogram(
    'controller_routing_duration_seconds',
    'Time to route request to worker',
    ['capability', 'worker_id'],
    buckets=[.001, .005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0]
)

# Request success/failure for availability SLO
controller_requests_total = Counter(
    'controller_requests_total',
    'Total requests routed',
    ['capability', 'status']  # status: success, error, rejected
)

# Error budget tracking
controller_error_budget_remaining = Gauge(
    'controller_error_budget_remaining_pct',
    'Remaining error budget percentage',
    ['capability']
)

# Idempotency hits
controller_idempotent_requests = Counter(
    'controller_idempotent_requests_total',
    'Requests served from idempotency cache',
    ['capability']
)
```

### Grafana Dashboard Queries

```promql
# SLO Latency (p95)
histogram_quantile(0.95,
  rate(controller_routing_duration_seconds_bucket[5m])
)

# Availability (success rate)
sum(rate(controller_requests_total{status="success"}[5m])) /
sum(rate(controller_requests_total[5m]))

# Error budget burn rate
rate(controller_requests_total{status="error"}[1h]) /
rate(controller_requests_total[1h])

# Idempotency hit rate
rate(controller_idempotent_requests_total[5m]) /
rate(controller_requests_total[5m])
```

## Review History

- 2025-11-16 - Initial proposal

## Next Steps

1. Implement `SLOManager` and `IdempotencyManager` in Phase 3 Session 3
2. Create example SLO YAML files for existing capabilities
3. Add CI check to validate SLO compliance
4. Integrate Prometheus metrics for SLO tracking
5. Create Grafana dashboard for SLO monitoring
6. Document SLO authoring guidelines for capability owners
