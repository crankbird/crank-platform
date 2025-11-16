# Capability Metadata Upgrade Plan (FaaS Extensions)

**Status**: 🎯 Ready to Execute (Post-Phase 3)
**Blocks**: None (incremental rollout safe)
**Depends On**: Phase 3 Session 1 complete (extended CapabilitySchema deployed)
**Timeline**: 1-2 days

---

## Overview

Roll out extended capability metadata (FaaS runtime info, SLO constraints, identity fields, economic routing) to all 9 production workers and 1 reference worker. This implements the Phase 3 future-proof schema from [ADR-0006](../decisions/0006-verb-capability-registry.md) with backward compatibility.

## Goals

- **FaaS metadata**: `runtime`, `env_profile`, `constraints` fields populated
- **SLO awareness**: `slo` field declares worker SLO requirements
- **Identity integration**: `spiffe_id`, `required_capabilities` support CAP
- **Economic routing**: `cost_tokens`, `slo_bid` support smart routing
- **Multi-controller**: `controller_affinity` hints for worker placement
- **Backward compatible**: All fields optional, existing workers unaffected

## Prerequisites

✅ **Phase 3 Session 1 Complete**:
- Extended `CapabilitySchema` API deployed
- Controller accepts optional fields
- 12 new fields available but unused

## Extended Schema Recap

From [ADR-0006](../decisions/0006-verb-capability-registry.md) and [Phase 3 Session 1](PHASE_3_ATTACK_PLAN.md#session-1-extended-capability-schema-2-hours):

```python
@dataclass
class CapabilitySchema:
    """Extended capability metadata (Phase 3)."""
    # Core fields (unchanged)
    verb: str
    name: str
    version: str
    worker_id: str
    url: str
    load_score: float

    # FaaS metadata (NEW - optional)
    runtime: str | None = None           # "python3.11", "node20", "dotnet8"
    env_profile: str | None = None       # "cpu-optimized", "gpu-required", "memory-intensive"
    constraints: dict | None = None      # {"min_memory_mb": 2048, "gpu_count": 1, "disk_type": "ssd"}

    # SLO constraints (NEW - optional)
    slo: dict | None = None              # {"latency_p95_ms": 200, "availability_pct": 99.9}

    # Identity + CAP (NEW - optional)
    spiffe_id: str | None = None         # "spiffe://crank.local/worker/streaming"
    required_capabilities: list[str] | None = None  # Capabilities this worker calls

    # Economic routing (NEW - optional)
    cost_tokens: float | None = None     # Cost per invocation (arbitrary units)
    slo_bid: float | None = None         # Priority bid for SLO compliance

    # Multi-controller (NEW - optional)
    controller_affinity: list[str] | None = None  # ["controller-gpu-1", "controller-gpu-2"]
```

## Worker Upgrade Roadmap

| Worker | Priority | FaaS Fields | SLO | Identity | Economic | Multi-Controller | Session |
|--------|----------|-------------|-----|----------|----------|------------------|---------|
| `crank_hello_world` (reference) | P0 | ✅ | ✅ | ✅ | ✅ | ✅ | 1 |
| `crank_streaming` | P1 | ✅ | ✅ | ✅ | - | - | 2 |
| `crank_document_conversion` | P1 | ✅ | ✅ | - | - | - | 2 |
| `crank_email_classifier` | P2 | ✅ | ✅ | ✅ | - | - | 3 |
| `crank_semantic_search` | P2 | ✅ | - | - | - | - | 3 |
| `crank_zettel_*` (3 workers) | P3 | ✅ | - | - | - | - | 4 |
| `crank_image_classifier` | P3 | ✅ | ✅ | - | ✅ | ✅ | 4 |

**Priority Legend**:
- **P0**: Reference implementation (all fields)
- **P1**: High-traffic workers (FaaS + SLO)
- **P2**: ML/specialized workers (FaaS + SLO + CAP)
- **P3**: Lower-traffic/experimental (FaaS only)

## Implementation Sessions

### Session 1: Reference Worker (hello_world) - ALL Fields (3 hours)

**Goal**: Implement complete extended schema as reference for other workers.

**Files to Modify**:

```
services/crank_hello_world.py
tests/integration/test_capability_metadata.py
docs/examples/capability-metadata-reference.md
```

**Complete Implementation**:

```python
from crank.capabilities import CapabilitySchema

class HelloWorldWorker(WorkerApplication):
    def __init__(self, https_port: int = 8500):
        super().__init__(https_port=https_port)
        self.worker_id = "worker-hello-world"

        # FaaS metadata
        runtime = "python3.11"
        env_profile = "cpu-optimized"
        constraints = {
            "min_memory_mb": 512,
            "max_memory_mb": 1024,
            "cpu_shares": 1024,
            "disk_type": "any"
        }

        # SLO constraints
        slo = {
            "latency_p50_ms": 50,
            "latency_p95_ms": 100,
            "latency_p99_ms": 200,
            "availability_pct": 99.5,
            "error_budget_pct": 0.5
        }

        # Identity (CAP)
        spiffe_id = "spiffe://crank.local/worker/hello-world"
        required_capabilities = []  # Calls no other capabilities

        # Economic routing
        cost_tokens = 0.1  # Very cheap (reference worker)
        slo_bid = 1.0      # Normal priority

        # Multi-controller
        controller_affinity = ["controller-primary"]  # Prefer main controller

        self.capabilities = [
            CapabilitySchema(
                verb="greet",
                name="hello_world",
                version="1.0.0",
                worker_id=self.worker_id,
                url=f"https://localhost:{self.https_port}",
                load_score=0.1,
                # Extended fields
                runtime=runtime,
                env_profile=env_profile,
                constraints=constraints,
                slo=slo,
                spiffe_id=spiffe_id,
                required_capabilities=required_capabilities,
                cost_tokens=cost_tokens,
                slo_bid=slo_bid,
                controller_affinity=controller_affinity
            )
        ]
```

**Integration Test**:

```python
@pytest.mark.asyncio
async def test_hello_world_extended_metadata():
    """Verify all extended fields present and valid."""
    worker = HelloWorldWorker(https_port=8500)
    capability = worker.capabilities[0]

    # FaaS metadata
    assert capability.runtime == "python3.11"
    assert capability.env_profile == "cpu-optimized"
    assert capability.constraints["min_memory_mb"] == 512

    # SLO
    assert capability.slo["latency_p95_ms"] == 100
    assert capability.slo["availability_pct"] == 99.5

    # Identity
    assert capability.spiffe_id == "spiffe://crank.local/worker/hello-world"
    assert capability.required_capabilities == []

    # Economic
    assert capability.cost_tokens == 0.1
    assert capability.slo_bid == 1.0

    # Multi-controller
    assert "controller-primary" in capability.controller_affinity

@pytest.mark.asyncio
async def test_controller_accepts_extended_metadata():
    """Verify controller registry stores extended fields."""
    # Register hello_world with extended metadata
    response = await client.post("/register", json=capability.to_dict())
    assert response.status_code == 200

    # Retrieve from /capabilities endpoint
    response = await client.get("/capabilities")
    caps = response.json()["capabilities"]

    hello_cap = next(c for c in caps if c["name"] == "hello_world")
    assert hello_cap["runtime"] == "python3.11"
    assert hello_cap["slo"]["latency_p95_ms"] == 100
```

**Reference Documentation** (`docs/examples/capability-metadata-reference.md`):

```markdown
# Capability Metadata Reference

Complete example from `crank_hello_world.py` showing all extended fields.

## FaaS Metadata
- `runtime`: Python/Node/dotnet version for container selection
- `env_profile`: Resource optimization hint
- `constraints`: Hard requirements (memory, CPU, disk)

## SLO Constraints
- Latency targets: p50, p95, p99
- Availability target
- Error budget

## Identity (CAP)
- `spiffe_id`: Worker identity for policy enforcement
- `required_capabilities`: Other capabilities this worker calls

## Economic Routing
- `cost_tokens`: Cost per invocation
- `slo_bid`: Priority for SLO compliance

## Multi-Controller
- `controller_affinity`: Preferred controller nodes

See `services/crank_hello_world.py` for complete implementation.
```

**Definition of Done**:
- [ ] Hello world has all 12 extended fields
- [ ] Integration test validates all fields
- [ ] Controller stores extended metadata
- [ ] Reference documentation complete
- [ ] Code review approved

---

### Session 2: High-Traffic Workers (streaming, document_conversion) - FaaS + SLO (3 hours)

**Goal**: Add FaaS metadata and SLO constraints to workers with significant traffic.

**Files to Modify**:

```
services/crank_streaming.py
services/crank_document_conversion.py
```

**Streaming Worker**:

```python
class StreamingWorker(WorkerApplication):
    def __init__(self, https_port: int = 8501):
        super().__init__(https_port=https_port)
        self.worker_id = "worker-streaming"

        # FaaS metadata
        runtime = "python3.11"
        env_profile = "cpu-optimized"  # SSE streaming is CPU-light
        constraints = {
            "min_memory_mb": 1024,
            "max_memory_mb": 2048,
            "cpu_shares": 2048,
            "network_bandwidth_mbps": 100  # Streaming needs bandwidth
        }

        # SLO constraints
        slo = {
            "latency_p50_ms": 100,   # Streaming setup
            "latency_p95_ms": 250,
            "latency_p99_ms": 500,
            "availability_pct": 99.9,  # High availability for SSE
            "error_budget_pct": 0.1
        }

        # Identity (will add in Session 3 when CAP deployed)
        spiffe_id = "spiffe://crank.local/worker/streaming"
        required_capabilities = ["convert:text_to_stream"]  # Calls converter

        self.capabilities = [
            CapabilitySchema(
                verb="stream",
                name="text_events",
                version="1.0.0",
                worker_id=self.worker_id,
                url=f"https://localhost:{self.https_port}",
                load_score=0.3,
                runtime=runtime,
                env_profile=env_profile,
                constraints=constraints,
                slo=slo,
                spiffe_id=spiffe_id,
                required_capabilities=required_capabilities
            ),
            # ... sse_events capability with same metadata
        ]
```

**Document Conversion Worker**:

```python
class DocumentConversionWorker(WorkerApplication):
    def __init__(self, https_port: int = 8502):
        super().__init__(https_port=https_port)
        self.worker_id = "worker-document-conversion"

        # FaaS metadata
        runtime = "python3.11"
        env_profile = "memory-intensive"  # PDF/DOCX parsing memory-heavy
        constraints = {
            "min_memory_mb": 2048,
            "max_memory_mb": 4096,
            "cpu_shares": 2048,
            "disk_type": "ssd",  # Temp file storage
            "tmp_storage_mb": 1024
        }

        # SLO constraints
        slo = {
            "latency_p50_ms": 500,   # Conversion is slower
            "latency_p95_ms": 2000,
            "latency_p99_ms": 5000,
            "availability_pct": 99.5,
            "error_budget_pct": 0.5
        }

        self.capabilities = [
            CapabilitySchema(
                verb="convert",
                name="pdf_to_text",
                version="1.0.0",
                worker_id=self.worker_id,
                url=f"https://localhost:{self.https_port}",
                load_score=0.5,
                runtime=runtime,
                env_profile=env_profile,
                constraints=constraints,
                slo=slo
            ),
            # ... other conversion capabilities
        ]
```

**Validation Script** (`scripts/validate_worker_metadata.py`):

```python
#!/usr/bin/env python3
"""Validate worker capability metadata completeness."""
import sys
from pathlib import Path
from importlib import import_module

def validate_worker(worker_module):
    """Check worker has required metadata fields."""
    worker_class = getattr(worker_module, f"{worker_module.__name__.split('_')[-1].title()}Worker")
    worker = worker_class()

    issues = []
    for cap in worker.capabilities:
        # Check FaaS metadata
        if not cap.runtime:
            issues.append(f"{cap.name}: missing runtime")
        if not cap.env_profile:
            issues.append(f"{cap.name}: missing env_profile")
        if not cap.constraints:
            issues.append(f"{cap.name}: missing constraints")

        # Check SLO (P1/P2 workers only)
        if worker.priority in ["P1", "P2"] and not cap.slo:
            issues.append(f"{cap.name}: missing SLO (required for {worker.priority})")

    return issues

if __name__ == "__main__":
    workers_dir = Path("services")
    all_issues = []

    for worker_file in workers_dir.glob("crank_*.py"):
        # ... validate each worker
        pass

    if all_issues:
        print("Metadata validation failed:")
        for issue in all_issues:
            print(f"  - {issue}")
        sys.exit(1)

    print("All workers have complete metadata ✅")
```

**Definition of Done**:
- [ ] Streaming has FaaS + SLO metadata
- [ ] Document conversion has FaaS + SLO metadata
- [ ] Validation script passes
- [ ] Load testing confirms SLOs realistic
- [ ] Documentation updated

---

### Session 3: ML Workers (email_classifier, semantic_search) - FaaS + SLO + CAP (4 hours)

**Goal**: Add full metadata to ML workers, including CAP identity for policy enforcement.

**Files to Modify**:

```
services/crank_email_classifier.py
services/crank_semantic_search.py
```

**Email Classifier**:

```python
class EmailClassifierWorker(WorkerApplication):
    def __init__(self, https_port: int = 8503):
        super().__init__(https_port=https_port)
        self.worker_id = "worker-email-classifier"

        # FaaS metadata
        runtime = "python3.11"
        env_profile = "cpu-optimized"  # CPU inference (no GPU)
        constraints = {
            "min_memory_mb": 2048,  # Model loaded in memory
            "max_memory_mb": 4096,
            "cpu_shares": 4096,     # More CPU for inference
            "model_storage_mb": 500
        }

        # SLO constraints
        slo = {
            "latency_p50_ms": 200,
            "latency_p95_ms": 500,
            "latency_p99_ms": 1000,
            "availability_pct": 99.9,  # Critical for email routing
            "error_budget_pct": 0.1
        }

        # Identity (CAP) - IMPORTANT for policy enforcement
        spiffe_id = "spiffe://crank.local/worker/email-classifier"
        required_capabilities = [
            "convert:email_to_text",  # Calls converter for preprocessing
            "classify:spam_detection" # Calls spam detector
        ]

        self.capabilities = [
            CapabilitySchema(
                verb="classify",
                name="email_category",
                version="2.0.0",
                worker_id=self.worker_id,
                url=f"https://localhost:{self.https_port}",
                load_score=0.6,
                runtime=runtime,
                env_profile=env_profile,
                constraints=constraints,
                slo=slo,
                spiffe_id=spiffe_id,
                required_capabilities=required_capabilities
            )
        ]
```

**Semantic Search**:

```python
class SemanticSearchWorker(WorkerApplication):
    def __init__(self, https_port: int = 8504):
        super().__init__(https_port=https_port)
        self.worker_id = "worker-semantic-search"

        # FaaS metadata
        runtime = "python3.11"
        env_profile = "memory-intensive"  # Vector database in memory
        constraints = {
            "min_memory_mb": 4096,  # Large embedding index
            "max_memory_mb": 8192,
            "cpu_shares": 4096,
            "vector_index_mb": 2048
        }

        # SLO constraints (less strict - search can be slow)
        slo = {
            "latency_p50_ms": 500,
            "latency_p95_ms": 2000,
            "latency_p99_ms": 5000,
            "availability_pct": 99.0,
            "error_budget_pct": 1.0
        }

        self.capabilities = [
            CapabilitySchema(
                verb="search",
                name="semantic_documents",
                version="1.0.0",
                worker_id=self.worker_id,
                url=f"https://localhost:{self.https_port}",
                load_score=0.7,
                runtime=runtime,
                env_profile=env_profile,
                constraints=constraints,
                slo=slo
            )
        ]
```

**Policy Integration** (ready for [controller-policy-observability-plan.md](controller-policy-observability-plan.md) Session 1):

```python
# Worker manifest auto-generated from required_capabilities field
# policies/data/worker_manifests.json
{
  "workers": {
    "spiffe://crank.local/worker/email-classifier": {
      "worker_id": "worker-email-classifier",
      "required_capabilities": [
        "convert:email_to_text",
        "classify:spam_detection"
      ],
      "owner": "ml-team",
      "deployed_at": "2025-11-16T10:00:00Z"
    }
  }
}
```

**Definition of Done**:
- [ ] Email classifier has FaaS + SLO + CAP metadata
- [ ] Semantic search has FaaS + SLO metadata
- [ ] Worker manifests auto-generated
- [ ] CAP fields ready for policy enforcement (OPA not yet deployed)
- [ ] Documentation updated

---

### Session 4: Zettel + Image Workers (zettel_*, image_classifier) - FaaS Baseline (3 hours)

**Goal**: Add baseline FaaS metadata to remaining workers.

**Files to Modify**:

```
services/crank_zettel_storage.py
services/crank_zettel_retrieval.py
services/crank_zettel_link_analysis.py
services/crank_image_classifier.py
```

**Zettel Workers** (all similar):

```python
class ZettelStorageWorker(WorkerApplication):
    def __init__(self, https_port: int = 8505):
        super().__init__(https_port=https_port)
        self.worker_id = "worker-zettel-storage"

        # FaaS metadata (minimal - experimental workers)
        runtime = "python3.11"
        env_profile = "cpu-optimized"
        constraints = {
            "min_memory_mb": 1024,
            "max_memory_mb": 2048,
            "cpu_shares": 1024,
            "disk_type": "ssd",      # Persistent storage
            "disk_storage_gb": 10
        }

        self.capabilities = [
            CapabilitySchema(
                verb="store",
                name="zettel",
                version="1.0.0",
                worker_id=self.worker_id,
                url=f"https://localhost:{self.https_port}",
                load_score=0.2,
                runtime=runtime,
                env_profile=env_profile,
                constraints=constraints
            )
        ]
```

**Image Classifier** (GPU worker - full metadata):

```python
class ImageClassifierWorker(WorkerApplication):
    def __init__(self, https_port: int = 8508):
        super().__init__(https_port=https_port)
        self.worker_id = "worker-image-classifier"

        # FaaS metadata (GPU-specific)
        runtime = "python3.11"
        env_profile = "gpu-required"  # CRITICAL: GPU needed
        constraints = {
            "min_memory_mb": 4096,
            "max_memory_mb": 16384,
            "cpu_shares": 8192,
            "gpu_count": 1,            # CRITICAL: GPU requirement
            "gpu_memory_mb": 8192,
            "gpu_type": "nvidia"       # Or "apple-metal" on macOS
        }

        # SLO constraints (GPU inference is fast)
        slo = {
            "latency_p50_ms": 100,
            "latency_p95_ms": 300,
            "latency_p99_ms": 1000,
            "availability_pct": 99.5,
            "error_budget_pct": 0.5
        }

        # Economic routing (GPU is expensive)
        cost_tokens = 10.0  # 100x more expensive than CPU workers
        slo_bid = 5.0       # Higher priority for GPU utilization

        # Multi-controller (GPU node affinity)
        controller_affinity = [
            "controller-gpu-1",
            "controller-gpu-2"
        ]

        self.capabilities = [
            CapabilitySchema(
                verb="classify",
                name="image_objects",
                version="1.0.0",
                worker_id=self.worker_id,
                url=f"https://localhost:{self.https_port}",
                load_score=0.8,
                runtime=runtime,
                env_profile=env_profile,
                constraints=constraints,
                slo=slo,
                cost_tokens=cost_tokens,
                slo_bid=slo_bid,
                controller_affinity=controller_affinity
            )
        ]
```

**GPU Detection Helper** (`src/crank/worker_runtime/gpu_detection.py`):

```python
import platform
import subprocess

def detect_gpu_type() -> str | None:
    """Auto-detect GPU type for constraints."""
    system = platform.system()

    if system == "Darwin":  # macOS
        # Check for Apple Silicon
        if platform.processor() == "arm":
            return "apple-metal"

    elif system == "Linux":
        # Check for NVIDIA GPU
        try:
            result = subprocess.run(
                ["nvidia-smi", "-L"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return "nvidia"
        except FileNotFoundError:
            pass

    return None

def get_gpu_constraints() -> dict | None:
    """Auto-generate GPU constraints."""
    gpu_type = detect_gpu_type()

    if not gpu_type:
        return None

    if gpu_type == "nvidia":
        return {
            "gpu_count": 1,
            "gpu_memory_mb": 8192,
            "gpu_type": "nvidia"
        }
    elif gpu_type == "apple-metal":
        return {
            "gpu_count": 1,
            "gpu_memory_mb": 16384,  # Unified memory on M-series
            "gpu_type": "apple-metal"
        }
```

**Definition of Done**:
- [ ] All 3 zettel workers have FaaS metadata
- [ ] Image classifier has FaaS + SLO + economic + multi-controller
- [ ] GPU detection helper working
- [ ] All 10 workers have at least FaaS metadata
- [ ] Validation script passes for all workers

---

## Validation & Testing

### Metadata Completeness Check

```bash
# Run validation script
python scripts/validate_worker_metadata.py

# Expected output:
# ✅ crank_hello_world: FaaS + SLO + Identity + Economic + Multi-Controller
# ✅ crank_streaming: FaaS + SLO + Identity
# ✅ crank_document_conversion: FaaS + SLO
# ✅ crank_email_classifier: FaaS + SLO + Identity
# ✅ crank_semantic_search: FaaS + SLO
# ✅ crank_zettel_storage: FaaS
# ✅ crank_zettel_retrieval: FaaS
# ✅ crank_zettel_link_analysis: FaaS
# ✅ crank_image_classifier: FaaS + SLO + Economic + Multi-Controller
# All workers have complete metadata ✅
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_all_workers_register_with_metadata():
    """Verify all workers can register with extended metadata."""
    # Start all workers
    workers = [
        HelloWorldWorker(8500),
        StreamingWorker(8501),
        # ... all 10 workers
    ]

    for worker in workers:
        for capability in worker.capabilities:
            response = await client.post("/register", json=capability.to_dict())
            assert response.status_code == 200

@pytest.mark.asyncio
async def test_controller_queries_metadata():
    """Verify controller can query by metadata fields."""
    # Query by runtime
    response = await client.get("/capabilities?runtime=python3.11")
    assert len(response.json()["capabilities"]) == 10

    # Query by env_profile
    response = await client.get("/capabilities?env_profile=gpu-required")
    gpu_caps = response.json()["capabilities"]
    assert any(c["name"] == "image_objects" for c in gpu_caps)

    # Query by SLO (future: smart routing)
    response = await client.get("/capabilities?max_latency_p95=300")
    fast_caps = response.json()["capabilities"]
    assert all(c["slo"]["latency_p95_ms"] <= 300 for c in fast_caps)
```

### Backward Compatibility Test

```python
@pytest.mark.asyncio
async def test_controller_accepts_minimal_metadata():
    """Verify workers without extended metadata still work."""
    minimal_capability = CapabilitySchema(
        verb="test",
        name="minimal",
        version="1.0.0",
        worker_id="worker-minimal",
        url="https://localhost:9999",
        load_score=0.1
        # NO extended fields
    )

    response = await client.post("/register", json=minimal_capability.to_dict())
    assert response.status_code == 200  # Should succeed
```

## Success Metrics

- [ ] All 10 workers have FaaS metadata (`runtime`, `env_profile`, `constraints`)
- [ ] 5 workers have SLO metadata (hello_world, streaming, doc_conversion, email_classifier, image_classifier)
- [ ] 3 workers have identity metadata (hello_world, streaming, email_classifier)
- [ ] 2 workers have economic metadata (hello_world, image_classifier)
- [ ] 2 workers have multi-controller metadata (hello_world, image_classifier)
- [ ] Validation script passes for all workers
- [ ] Controller accepts all metadata fields
- [ ] Integration tests pass
- [ ] Backward compatibility verified (minimal metadata still works)

## Rollout Plan

**Day 1**:
- Session 1: Hello world (reference implementation)
- Session 2: Streaming + document conversion

**Day 2**:
- Session 3: Email classifier + semantic search
- Session 4: Zettel workers + image classifier
- Validation + integration tests

## Future Utilization

**FaaS Metadata** → Used by future FaaS deployment system
- Controller routes to workers matching runtime/constraints
- Container orchestration uses `env_profile` for node selection
- Resource allocation based on `constraints`

**SLO Metadata** → Used by [controller-slo-idempotency-plan.md](controller-slo-idempotency-plan.md)
- SLOManager checks worker SLO before routing
- Prometheus tracks SLO compliance
- CI enforces SLO budgets

**Identity Metadata** → Used by [controller-policy-observability-plan.md](controller-policy-observability-plan.md)
- OPA policy enforcement via `spiffe_id` and `required_capabilities`
- Worker manifests auto-generated from `required_capabilities`
- CAP model prevents unauthorized capability access

**Economic Metadata** → Used by future economic routing
- Cost-aware routing: prefer cheap workers when SLOs allow
- Priority bidding: high `slo_bid` workers get routed first under load

**Multi-Controller Metadata** → Used by future mesh coordination
- Worker placement hints via `controller_affinity`
- GPU workers prefer GPU-enabled controller nodes
- Load balancing across controller fleet

## Next Steps

1. **Complete Phase 3 Session 1** (extended schema deployed)
2. **Execute Sessions 1-4** above
3. **Run validation script** (`python scripts/validate_worker_metadata.py`)
4. **Integration testing** (all workers register successfully)
5. **Documentation** (capability-metadata-reference.md)
6. **Enable downstream features**:
   - SLO enforcement (once controller-slo-idempotency-plan.md complete)
   - Policy enforcement (once controller-policy-observability-plan.md complete)
   - Future FaaS deployment (roadmap item)

## References

- [ADR-0006](../decisions/0006-verb-capability-registry.md) - Extended capability schema
- [Phase 3 Attack Plan](PHASE_3_ATTACK_PLAN.md) - Extended schema API (Session 1)
- [FaaS Worker Proposal](../proposals/faas-worker-metadata.md) - FaaS metadata requirements
- [Enhancement Roadmap](../proposals/enhancement-roadmap.md) - SLO + economic routing
- [Enterprise Security](../proposals/enterprise-security.md) - Identity + CAP
- [Controller SLO Plan](controller-slo-idempotency-plan.md) - SLO enforcement implementation
- [Controller Policy Plan](controller-policy-observability-plan.md) - CAP enforcement implementation
