# Controller SLO + Idempotency Implementation Plan

**Status**: 🎯 Ready to Execute (Post-Phase 3)
**Blocks**: ADR-0026 acceptance
**Depends On**: Phase 3 Session 3 complete (controller `/route` endpoint operational)
**Timeline**: 2-3 days

---

## Overview

Implement SLO enforcement and idempotency manager in the controller to support enterprise deployments. This work builds on Phase 3's controller foundation and implements [ADR-0026](../decisions/0026-controller-slo-and-idempotency.md).

## Goals

- **SLO tracking**: Latency (p50/p95/p99), availability, error budget
- **CI integration**: Fail builds on SLO regression
- **Idempotency**: 1-hour deduplication window, result caching
- **Performance**: <5ms overhead on routing path
- **Observability**: Grafana/Datadog dashboard integration

## Prerequisites

✅ **Phase 3 Complete**:
- Controller service operational (`services/crank_controller.py`)
- `/route` endpoint functional
- CapabilityRegistry implemented
- OpenTelemetry instrumentation in place
- Prometheus metrics exposed

## Implementation Sessions

### Session 1: SLO Manager + YAML Schema (4 hours)

**Files to Create**:

```
src/crank/controller/
  slo_manager.py              # SLO file loader and compliance checker

state/controller/slos/
  example-capability.yml      # Example SLO file
  convert_document_to_pdf.yml # Real SLO for doc conversion
  classify_email.yml          # Real SLO for email classification

tests/unit/controller/
  test_slo_manager.py         # Unit tests
```

**What to Build**:

**SLO YAML Schema** (from ADR-0026):

```yaml
# state/controller/slos/convert_document_to_pdf.yml
capability:
  verb: convert
  name: convert_document_to_pdf
  version: "1.0"

slo:
  latency:
    p50_ms: 50
    p95_ms: 100
    p99_ms: 200
  availability:
    target: 0.999
  error_budget:
    monthly_pct: 0.1
    alerts:
      - threshold: 0.5
        channel: slack
      - threshold: 0.9
        channel: pagerduty

enforcement:
  reject_on_violation: false  # Phase 1: log only
  grace_period_days: 7

metadata:
  owner: document-team
  cost_center: engineering
  tier: production
```

**SLOManager Implementation**:

```python
import yaml
from pathlib import Path
from pydantic import BaseModel

class SLOLatency(BaseModel):
    p50_ms: int
    p95_ms: int
    p99_ms: int

class SLOAvailability(BaseModel):
    target: float  # 0.999 = 99.9%

class SLOErrorBudget(BaseModel):
    monthly_pct: float
    alerts: list[dict]

class SLODefinition(BaseModel):
    latency: SLOLatency
    availability: SLOAvailability
    error_budget: SLOErrorBudget

class SLOEnforcement(BaseModel):
    reject_on_violation: bool
    grace_period_days: int

class SLOCapability(BaseModel):
    verb: str
    name: str
    version: str

class SLOMetadata(BaseModel):
    owner: str
    cost_center: str
    tier: str

class SLOFile(BaseModel):
    capability: SLOCapability
    slo: SLODefinition
    enforcement: SLOEnforcement
    metadata: SLOMetadata

class SLOManager:
    def __init__(self, slo_dir: str = "state/controller/slos"):
        self.slo_dir = Path(slo_dir)
        self.slos: dict[str, SLOFile] = {}
        self._load_all()

    def _load_all(self):
        """Load all YAML SLO files on startup."""
        if not self.slo_dir.exists():
            logger.warning(f"SLO directory {self.slo_dir} not found")
            return

        for slo_file in self.slo_dir.glob("*.yml"):
            try:
                with open(slo_file) as f:
                    data = yaml.safe_load(f)
                    slo = SLOFile(**data)
                    key = f"{slo.capability.verb}:{slo.capability.name}"
                    self.slos[key] = slo
                    logger.info(
                        "slo_loaded",
                        capability=key,
                        p95_target=slo.slo.latency.p95_ms,
                        file=slo_file.name
                    )
            except Exception as e:
                logger.error(
                    "slo_load_failed",
                    file=slo_file.name,
                    error=str(e)
                )

    def get_slo(self, capability: str) -> SLOFile | None:
        return self.slos.get(capability)

    def check_compliance(
        self,
        capability: str,
        current_metrics: dict
    ) -> tuple[bool, list[str]]:
        """
        Check if current metrics meet SLO.
        Returns (compliant: bool, violations: list[str])
        """
        slo = self.get_slo(capability)
        if not slo:
            return True, []  # No SLO = compliant

        violations = []

        # Check p95 latency
        p95_actual = current_metrics.get("p95_ms", 0)
        if p95_actual > slo.slo.latency.p95_ms:
            violations.append(
                f"p95 latency {p95_actual}ms > target {slo.slo.latency.p95_ms}ms"
            )

        # Check availability
        avail_actual = current_metrics.get("availability", 1.0)
        if avail_actual < slo.slo.availability.target:
            violations.append(
                f"availability {avail_actual:.3f} < target {slo.slo.availability.target}"
            )

        return len(violations) == 0, violations
```

**Tests**:

```python
def test_load_slo_files():
    mgr = SLOManager("test-slos")
    assert "convert:document_to_pdf" in mgr.slos

def test_compliance_check_pass():
    mgr = SLOManager()
    compliant, violations = mgr.check_compliance(
        "convert:document_to_pdf",
        {"p95_ms": 50, "availability": 0.999}
    )
    assert compliant
    assert len(violations) == 0

def test_compliance_check_fail_latency():
    mgr = SLOManager()
    compliant, violations = mgr.check_compliance(
        "convert:document_to_pdf",
        {"p95_ms": 250, "availability": 0.999}  # Exceeds p95 target
    )
    assert not compliant
    assert "p95 latency" in violations[0]
```

**Definition of Done**:
- [ ] SLOManager loads all YAML files from `state/controller/slos/`
- [ ] Pydantic schema validates SLO files
- [ ] `check_compliance()` method works
- [ ] 3 example SLO files created
- [ ] Unit tests pass
- [ ] Documentation: SLO authoring guide

---

### Session 2: Idempotency Manager (3 hours)

**Files to Create**:

```
src/crank/controller/
  idempotency_manager.py      # In-memory cache with TTL

tests/unit/controller/
  test_idempotency_manager.py # Unit tests
```

**Implementation** (from ADR-0026):

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
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 10_000):
        self._cache: dict[str, CachedResult] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
        self._max_size = max_size

    def check_duplicate(self, idempotency_key: str) -> CachedResult | None:
        """Return cached result if exists and not expired."""
        if idempotency_key in self._cache:
            cached = self._cache[idempotency_key]
            if datetime.now() - cached.timestamp < self._ttl:
                return cached
            else:
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

    def get_stats(self) -> dict:
        """Return cache statistics."""
        return {
            "total_entries": len(self._cache),
            "max_size": self._max_size,
            "ttl_seconds": self._ttl.total_seconds(),
            "utilization_pct": (len(self._cache) / self._max_size) * 100
        }
```

**Background Cleanup Task**:

```python
# Add to controller startup
async def cleanup_loop():
    """Periodic cleanup of expired cache entries."""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        removed = idempotency_mgr.cleanup_expired()
        if removed > 0:
            logger.info("idempotency_cleanup", removed_entries=removed)

# In controller __init__
asyncio.create_task(cleanup_loop())
```

**Tests**:

```python
def test_cache_and_retrieve():
    mgr = IdempotencyManager(ttl_seconds=60)
    mgr.cache_result("key1", {"status": "ok"}, "worker-1", "convert:pdf")

    cached = mgr.check_duplicate("key1")
    assert cached is not None
    assert cached.result == {"status": "ok"}

def test_cache_expiry():
    mgr = IdempotencyManager(ttl_seconds=1)
    mgr.cache_result("key1", {"status": "ok"}, "worker-1", "convert:pdf")

    time.sleep(2)
    cached = mgr.check_duplicate("key1")
    assert cached is None  # Expired

def test_lru_eviction():
    mgr = IdempotencyManager(ttl_seconds=3600, max_size=100)

    # Fill cache to max
    for i in range(100):
        mgr.cache_result(f"key{i}", {"i": i}, "worker-1", "test")

    # Add one more, should evict oldest 10
    mgr.cache_result("key_new", {"new": True}, "worker-1", "test")

    assert len(mgr._cache) == 91  # 100 - 10 + 1
    assert mgr.check_duplicate("key0") is None  # Oldest evicted
```

**Definition of Done**:
- [ ] IdempotencyManager implemented
- [ ] TTL expiry works
- [ ] LRU eviction works
- [ ] Background cleanup task runs
- [ ] Unit tests pass
- [ ] Prometheus metrics for cache hit/miss rate

---

### Session 3: Controller Integration (4 hours)

**Files to Modify**:

```
services/crank_controller.py   # Add SLO + idempotency to /route

tests/integration/
  test_slo_enforcement.py      # Integration tests
  test_idempotency.py          # Integration tests
```

**Controller `/route` Enhancement**:

```python
class ControllerService:
    def __init__(self):
        self.slo_manager = SLOManager()
        self.idempotency_mgr = IdempotencyManager(ttl_seconds=3600)
        self.registry = CapabilityRegistry()
        self.metrics = MetricsCollector()

    @app.post("/route")
    async def route(
        self,
        verb: str,
        capability: str,
        idempotency_key: str | None = None,
        priority: str = "normal",  # low, normal, high
        request_payload: dict = {}
    ):
        capability_name = f"{verb}:{capability}"
        start_time = time.time()

        # 1. Check idempotency
        if idempotency_key:
            cached = self.idempotency_mgr.check_duplicate(idempotency_key)
            if cached:
                logger.info(
                    "idempotent_request_replayed",
                    idempotency_key=idempotency_key,
                    age_seconds=(datetime.now() - cached.timestamp).seconds
                )
                self.metrics.idempotent_hits.inc()
                return JSONResponse(
                    cached.result,
                    headers={"X-Idempotent-Replay": "true"}
                )

        # 2. Load SLO
        slo = self.slo_manager.get_slo(capability_name)

        # 3. Check current performance vs SLO
        if slo and slo.enforcement.reject_on_violation:
            current_metrics = self.metrics.get_capability_metrics(capability_name)
            compliant, violations = self.slo_manager.check_compliance(
                capability_name,
                current_metrics
            )

            if not compliant:
                logger.warning(
                    "slo_violation_detected",
                    capability=capability_name,
                    violations=violations
                )

                # Reject low-priority requests during SLO violation
                if priority == "low":
                    raise HTTPException(
                        503,
                        detail={
                            "error": "slo_violation",
                            "message": "Rejecting low-priority requests",
                            "violations": violations
                        }
                    )

        # 4. Route to worker (existing logic)
        workers = self.registry.get_workers_for_capability(capability_name)
        healthy = [w for w in workers if w.is_healthy()]

        if not healthy:
            raise HTTPException(503, detail="no_worker_available")

        worker = healthy[0]

        # 5. Execute request
        result = await self._call_worker(worker, request_payload)

        # 6. Cache result if idempotency key provided
        if idempotency_key:
            self.idempotency_mgr.cache_result(
                idempotency_key=idempotency_key,
                result=result,
                worker_id=worker.worker_id,
                capability=capability_name
            )

        # 7. Track metrics for SLO
        duration_ms = (time.time() - start_time) * 1000
        success = result.get("status") == "success"

        self.metrics.record_request(
            capability=capability_name,
            latency_ms=duration_ms,
            success=success
        )

        return result
```

**Prometheus Metrics**:

```python
from prometheus_client import Histogram, Counter, Gauge

# SLO tracking
controller_slo_latency = Histogram(
    'controller_slo_latency_seconds',
    'Request latency for SLO tracking',
    ['capability'],
    buckets=[.01, .025, .05, .1, .25, .5, 1.0, 2.5, 5.0]
)

controller_slo_requests_total = Counter(
    'controller_slo_requests_total',
    'Total requests for SLO tracking',
    ['capability', 'status']  # success, error
)

controller_slo_violations = Counter(
    'controller_slo_violations_total',
    'SLO violations detected',
    ['capability', 'metric']  # latency, availability
)

# Idempotency tracking
controller_idempotency_hits = Counter(
    'controller_idempotency_hits_total',
    'Requests served from idempotency cache',
    ['capability']
)

controller_idempotency_cache_size = Gauge(
    'controller_idempotency_cache_size',
    'Current idempotency cache size'
)
```

**Integration Tests**:

```python
@pytest.mark.asyncio
async def test_idempotency_prevents_duplicate():
    # First request
    response1 = await client.post("/route", json={
        "verb": "convert",
        "capability": "document_to_pdf",
        "idempotency_key": "test-key-123",
        "request_payload": {"doc": "test"}
    })
    assert response1.status_code == 200

    # Second request (duplicate)
    response2 = await client.post("/route", json={
        "verb": "convert",
        "capability": "document_to_pdf",
        "idempotency_key": "test-key-123",
        "request_payload": {"doc": "test"}
    })
    assert response2.status_code == 200
    assert response2.headers["X-Idempotent-Replay"] == "true"
    assert response2.json() == response1.json()

@pytest.mark.asyncio
async def test_slo_violation_rejects_low_priority():
    # Simulate SLO violation (high latency)
    # ... setup code

    response = await client.post("/route", json={
        "verb": "convert",
        "capability": "slow_capability",
        "priority": "low"
    })
    assert response.status_code == 503
    assert "slo_violation" in response.json()["error"]
```

**Definition of Done**:
- [ ] `/route` endpoint uses SLOManager and IdempotencyManager
- [ ] Idempotent requests return cached results
- [ ] SLO violations logged (reject_on_violation=false in Phase 1)
- [ ] Prometheus metrics exposed
- [ ] Integration tests pass
- [ ] Performance: <5ms overhead verified

---

### Session 4: CI Integration (2 hours)

**Files to Create**:

```
scripts/
  check_slo_compliance.py     # CI script

.github/workflows/
  slo-check.yml               # GitHub Actions workflow
```

**SLO Compliance Checker** (from ADR-0026):

```python
#!/usr/bin/env python3
"""Check if current metrics violate SLO definitions."""
import sys
from pathlib import Path
import yaml

def check_slo_compliance(slo_dir: Path, metrics_file: Path) -> bool:
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
                f"{capability}: p95 latency {p95_actual}ms > {p95_target}ms"
            )

        # Check availability
        avail_actual = cap_metrics.get("availability", 1.0)
        avail_target = slo["slo"]["availability"]["target"]
        if avail_actual < avail_target:
            violations.append(
                f"{capability}: availability {avail_actual:.3f} < {avail_target}"
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
    compliant = check_slo_compliance(
        Path("state/controller/slos"),
        Path("test-results/metrics.yml")
    )
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

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run integration tests with metrics
        run: |
          pytest tests/integration/ --metrics-output=test-results/metrics.yml

      - name: Check SLO compliance
        run: |
          python scripts/check_slo_compliance.py
```

**Pytest Plugin for Metrics Export**:

```python
# conftest.py
import pytest
import yaml

@pytest.fixture(scope="session")
def metrics_collector():
    """Collect metrics during test run."""
    return {"capabilities": {}}

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "slo: mark test to contribute to SLO metrics"
    )

def pytest_sessionfinish(session, exitstatus):
    """Export metrics at end of test session."""
    metrics_output = session.config.getoption("--metrics-output")
    if metrics_output:
        # Gather metrics from test results
        # ... implementation
        with open(metrics_output, "w") as f:
            yaml.dump(metrics, f)
```

**Definition of Done**:
- [ ] `scripts/check_slo_compliance.py` works
- [ ] GitHub Actions workflow runs on push
- [ ] Pytest metrics export plugin implemented
- [ ] CI fails on SLO violations
- [ ] Documentation: CI integration guide

---

## Success Metrics

**Functional**:
- [ ] SLO files loaded from YAML
- [ ] Idempotency prevents duplicate execution
- [ ] SLO violations logged
- [ ] CI fails on SLO regression
- [ ] <5ms overhead on routing path

**Observability**:
- [ ] Prometheus metrics for SLO tracking
- [ ] Grafana dashboard showing SLO compliance
- [ ] Idempotency hit rate visible
- [ ] Cache utilization metrics

**Enterprise Readiness**:
- [ ] Error budgets calculated
- [ ] Alert thresholds configurable
- [ ] Multi-tenant billing protected (idempotency)
- [ ] SLO authoring guide published

## Rollout Plan

**Phase 1**: Log-only mode (weeks 1-2)
- `reject_on_violation: false` in all SLO files
- Monitor for false positives
- Tune SLO targets

**Phase 2**: Enforcement for new capabilities (weeks 3-4)
- New capabilities require SLO files
- Enforcement enabled for new services only
- Legacy services remain log-only

**Phase 3**: Full enforcement (week 5+)
- All capabilities enforce SLOs
- CI gate active
- Alert on SLO violations

## Next Steps

1. Complete Phase 3 Session 3 (controller `/route` operational)
2. Execute Sessions 1-4 above
3. Create SLO files for all existing capabilities
4. Enable CI SLO check
5. Create Grafana dashboard
6. Document SLO authoring best practices
7. Update ADR-0026 status to "Accepted"

## References

- [ADR-0026](../decisions/0026-controller-slo-and-idempotency.md)
- [Enhancement Roadmap - Enterprise Readiness](../proposals/enhancement-roadmap.md#enterprise-readiness-new--high-priority)
- [Phase 3 Attack Plan](PHASE_3_ATTACK_PLAN.md) - Controller foundation
