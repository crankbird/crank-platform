"""Unit tests for CapabilityRegistry.

Tests core functionality:
- Worker registration with capabilities
- Heartbeat tracking
- Routing (capability -> worker lookup)
- Stale worker cleanup
- State persistence (JSONL)
- Extended schema fields (future-proof)
"""

import time
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from crank.controller.capability_registry import (
    CapabilityRegistry,
    CapabilitySchema,
)


# --- Fixtures ---


@pytest.fixture
def temp_state_file() -> Path:
    """Temporary state file for testing persistence."""
    with NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        return Path(f.name)


@pytest.fixture
def registry(temp_state_file: Path) -> CapabilityRegistry:
    """Fresh registry with temporary state file."""
    return CapabilityRegistry(state_file=temp_state_file, heartbeat_timeout=5)


@pytest.fixture
def minimal_capability() -> CapabilitySchema:
    """Minimal capability (core fields only)."""
    return CapabilitySchema(
        name="hello_world",
        verb="greet",
        version="1.0.0",
    )


@pytest.fixture
def extended_capability() -> CapabilitySchema:
    """Full capability with all extended fields."""
    return CapabilitySchema(
        # Core fields
        name="document_to_pdf",
        verb="convert",
        version="1.0.0",
        requires_gpu=False,
        max_concurrency=5,
        # FaaS metadata
        runtime="python3.11",
        env_profile="memory-intensive",
        constraints={"min_memory_mb": 2048, "disk_type": "ssd"},
        # SLO
        slo={"latency_p95_ms": 500, "availability_pct": 99.5},
        # Identity
        spiffe_id="spiffe://crank.local/worker/doc-conversion",
        required_capabilities=["classify:document_type"],
        # Economic
        cost_tokens_per_invocation=1.5,
        slo_bid=2.0,
        # Multi-controller
        controller_affinity=["controller-primary"],
    )


# --- Registration Tests ---


def test_register_worker_minimal_capability(
    registry: CapabilityRegistry, minimal_capability: CapabilitySchema
) -> None:
    """Test registration with minimal capability (backward compatible)."""
    registry.register(
        worker_id="worker-1",
        worker_url="https://localhost:8500",
        capabilities=[minimal_capability],
    )

    assert "worker-1" in registry._workers
    worker = registry._workers["worker-1"]
    assert worker.worker_id == "worker-1"
    assert len(worker.capabilities) == 1
    assert worker.capabilities[0].name == "hello_world"


def test_register_worker_extended_capability(
    registry: CapabilityRegistry, extended_capability: CapabilitySchema
) -> None:
    """Test registration with extended capability (all fields)."""
    registry.register(
        worker_id="worker-doc",
        worker_url="https://localhost:8501",
        capabilities=[extended_capability],
    )

    worker = registry._workers["worker-doc"]
    cap = worker.capabilities[0]

    # Verify core fields
    assert cap.name == "document_to_pdf"
    assert cap.verb == "convert"

    # Verify FaaS metadata
    assert cap.runtime == "python3.11"
    assert cap.env_profile == "memory-intensive"
    assert cap.constraints["min_memory_mb"] == 2048

    # Verify SLO
    assert cap.slo["latency_p95_ms"] == 500

    # Verify identity
    assert cap.spiffe_id == "spiffe://crank.local/worker/doc-conversion"
    assert "classify:document_type" in cap.required_capabilities

    # Verify economic
    assert cap.cost_tokens_per_invocation == 1.5
    assert cap.slo_bid == 2.0

    # Verify multi-controller
    assert "controller-primary" in cap.controller_affinity


def test_register_multiple_capabilities(
    registry: CapabilityRegistry,
) -> None:
    """Test worker with multiple capabilities."""
    caps = [
        CapabilitySchema(name="text_events", verb="stream", version="1.0.0"),
        CapabilitySchema(name="sse_events", verb="stream", version="1.0.0"),
    ]

    registry.register(
        worker_id="worker-streaming",
        worker_url="https://localhost:8502",
        capabilities=caps,
    )

    worker = registry._workers["worker-streaming"]
    assert len(worker.capabilities) == 2


# --- Routing Tests ---


def test_route_finds_worker(
    registry: CapabilityRegistry, minimal_capability: CapabilitySchema
) -> None:
    """Test routing finds correct worker."""
    registry.register(
        worker_id="worker-1",
        worker_url="https://localhost:8500",
        capabilities=[minimal_capability],
    )

    worker = registry.route(verb="greet", capability="hello_world")

    assert worker is not None
    assert worker.worker_id == "worker-1"


def test_route_no_worker_available(registry: CapabilityRegistry) -> None:
    """Test routing returns None when no worker available."""
    worker = registry.route(verb="convert", capability="nonexistent")
    assert worker is None


def test_route_multiple_workers_returns_first_healthy(
    registry: CapabilityRegistry,
) -> None:
    """Test routing with multiple workers returns first healthy."""
    cap = CapabilitySchema(name="classify", verb="classify", version="1.0.0")

    registry.register(
        worker_id="worker-1",
        worker_url="https://localhost:8500",
        capabilities=[cap],
    )
    registry.register(
        worker_id="worker-2",
        worker_url="https://localhost:8501",
        capabilities=[cap],
    )

    worker = registry.route(verb="classify", capability="classify")
    assert worker is not None
    assert worker.worker_id in ["worker-1", "worker-2"]


# --- Heartbeat Tests ---


def test_heartbeat_updates_timestamp(registry: CapabilityRegistry) -> None:
    """Test heartbeat updates last_heartbeat timestamp."""
    cap = CapabilitySchema(name="test", verb="test", version="1.0.0")
    registry.register(
        worker_id="worker-1",
        worker_url="https://localhost:8500",
        capabilities=[cap],
    )

    original_time = registry._workers["worker-1"].last_heartbeat
    time.sleep(0.1)

    success = registry.heartbeat("worker-1")

    assert success is True
    assert registry._workers["worker-1"].last_heartbeat > original_time


def test_heartbeat_unknown_worker_returns_false(
    registry: CapabilityRegistry,
) -> None:
    """Test heartbeat for unknown worker returns False."""
    success = registry.heartbeat("unknown-worker")
    assert success is False


# --- Staleness Tests ---


def test_worker_becomes_stale_after_timeout(
    registry: CapabilityRegistry,
) -> None:
    """Test worker marked stale after heartbeat timeout."""
    cap = CapabilitySchema(name="test", verb="test", version="1.0.0")
    registry.register(
        worker_id="worker-1",
        worker_url="https://localhost:8500",
        capabilities=[cap],
    )

    # Worker starts healthy
    worker = registry._workers["worker-1"]
    assert worker.is_healthy(registry.heartbeat_timeout) is True

    # Simulate timeout (manually set old timestamp)
    worker.last_heartbeat = datetime.now() - timedelta(seconds=10)

    # Worker now stale
    assert worker.is_healthy(registry.heartbeat_timeout) is False


def test_cleanup_stale_removes_workers(registry: CapabilityRegistry) -> None:
    """Test cleanup removes stale workers."""
    cap = CapabilitySchema(name="test", verb="test", version="1.0.0")
    registry.register(
        worker_id="worker-stale",
        worker_url="https://localhost:8500",
        capabilities=[cap],
    )

    # Make worker stale
    registry._workers["worker-stale"].last_heartbeat = datetime.now() - timedelta(
        seconds=10
    )

    removed = registry.cleanup_stale()

    assert removed == 1
    assert "worker-stale" not in registry._workers


def test_route_excludes_stale_workers(registry: CapabilityRegistry) -> None:
    """Test routing excludes stale workers."""
    cap = CapabilitySchema(name="test", verb="test", version="1.0.0")
    registry.register(
        worker_id="worker-stale",
        worker_url="https://localhost:8500",
        capabilities=[cap],
    )

    # Make worker stale
    registry._workers["worker-stale"].last_heartbeat = datetime.now() - timedelta(
        seconds=10
    )

    worker = registry.route(verb="test", capability="test")
    assert worker is None  # Stale worker not returned


# --- Deregistration Tests ---


def test_deregister_removes_worker(registry: CapabilityRegistry) -> None:
    """Test deregister removes worker."""
    cap = CapabilitySchema(name="test", verb="test", version="1.0.0")
    registry.register(
        worker_id="worker-1",
        worker_url="https://localhost:8500",
        capabilities=[cap],
    )

    assert "worker-1" in registry._workers

    registry.deregister("worker-1")

    assert "worker-1" not in registry._workers


# --- Persistence Tests ---


def test_state_persists_to_file(
    registry: CapabilityRegistry,
    temp_state_file: Path,
    minimal_capability: CapabilitySchema,
) -> None:
    """Test state saves to JSONL file."""
    registry.register(
        worker_id="worker-1",
        worker_url="https://localhost:8500",
        capabilities=[minimal_capability],
    )

    assert temp_state_file.exists()
    content = temp_state_file.read_text()
    assert "worker-1" in content
    assert "hello_world" in content


def test_state_loads_on_startup(
    temp_state_file: Path, minimal_capability: CapabilitySchema
) -> None:
    """Test state loads from file on registry startup."""
    # Create registry, register worker, state saves
    registry1 = CapabilityRegistry(state_file=temp_state_file)
    registry1.register(
        worker_id="worker-1",
        worker_url="https://localhost:8500",
        capabilities=[minimal_capability],
    )

    # Create new registry (simulates restart)
    registry2 = CapabilityRegistry(state_file=temp_state_file)

    assert "worker-1" in registry2._workers
    assert len(registry2._workers["worker-1"].capabilities) == 1


# --- Introspection Tests ---


def test_get_all_capabilities(registry: CapabilityRegistry) -> None:
    """Test get_all_capabilities returns capability summary."""
    cap1 = CapabilitySchema(name="cap1", verb="test", version="1.0.0")
    cap2 = CapabilitySchema(name="cap2", verb="test", version="1.0.0")

    registry.register(
        worker_id="worker-1",
        worker_url="https://localhost:8500",
        capabilities=[cap1],
    )
    registry.register(
        worker_id="worker-2",
        worker_url="https://localhost:8501",
        capabilities=[cap2],
    )

    caps = registry.get_all_capabilities()

    assert "test:cap1" in caps
    assert "test:cap2" in caps
    assert caps["test:cap1"]["workers"] == 1
    assert caps["test:cap1"]["healthy_workers"] == 1


def test_get_all_workers(registry: CapabilityRegistry) -> None:
    """Test get_all_workers returns worker summary."""
    cap = CapabilitySchema(name="test", verb="test", version="1.0.0")
    registry.register(
        worker_id="worker-1",
        worker_url="https://localhost:8500",
        capabilities=[cap],
    )

    workers = registry.get_all_workers()

    assert len(workers) == 1
    assert workers[0]["worker_id"] == "worker-1"
    assert workers[0]["is_healthy"] is True
    assert "test:test" in workers[0]["capabilities"]


# --- Multi-Controller Tests (Scaffolding) ---


def test_export_state(registry: CapabilityRegistry) -> None:
    """Test export_state returns serializable state."""
    cap = CapabilitySchema(name="test", verb="test", version="1.0.0")
    registry.register(
        worker_id="worker-1",
        worker_url="https://localhost:8500",
        capabilities=[cap],
    )

    state = registry.export_state()

    assert "workers" in state
    assert len(state["workers"]) == 1
    assert state["workers"][0]["worker_id"] == "worker-1"
    assert "exported_at" in state


def test_import_remote_state_stub(registry: CapabilityRegistry) -> None:
    """Test import_remote_state (stub for future work)."""
    state = {
        "workers": [
            {
                "worker_id": "remote-worker",
                "worker_url": "https://remote:8500",
                "capabilities": [],
                "last_heartbeat": datetime.now().isoformat(),
                "registered_at": datetime.now().isoformat(),
            }
        ],
        "exported_at": datetime.now().isoformat(),
    }

    # Should not raise (stub implementation)
    registry.import_remote_state("controller-remote", state)
