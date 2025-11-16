"""Integration tests for Crank Controller.

Tests the controller service API endpoints with actual capability registry.
"""

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from fastapi.testclient import TestClient

from services.crank_controller import ControllerService


@pytest.fixture
def temp_state_file() -> Path:
    """Provide temporary state file for controller tests."""
    with NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
        return Path(f.name)


@pytest.fixture
def controller(temp_state_file: Path) -> ControllerService:
    """Create controller service for testing."""
    # Override environment to use test state file
    import os
    os.environ["CONTROLLER_STATE_FILE"] = str(temp_state_file)

    # ControllerService.__init__ now registers routes automatically
    # (no longer extends WorkerApplication, so no duplicate registration)
    controller = ControllerService(https_port=9999)
    return controller
@pytest.fixture
def client(controller: ControllerService) -> TestClient:
    """Create test client for controller API."""
    return TestClient(controller.app)


def test_health_check(client: TestClient) -> None:
    """Test controller health endpoint."""
    response = client.get("/health")

    # Note: /health is provided by WorkerApplication base class
    # It returns health manager status, which will be unhealthy until
    # controller registers with itself (which doesn't happen in tests)
    # For controller-specific health, use /workers or /status endpoints
    assert response.status_code in [200, 503]  # Either is acceptable
    data = response.json()
    assert "status" in data
def test_register_worker(client: TestClient) -> None:
    """Test worker registration."""
    registration = {
        "worker_id": "test-worker-1",
        "worker_url": "https://localhost:8500",
        "capabilities": [
            {
                "name": "email.classify",
                "verb": "invoke",
                "version": "1.0.0",
            }
        ],
    }

    response = client.post("/register", json=registration)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "registered"
    assert data["worker_id"] == "test-worker-1"
    assert data["capabilities_registered"] == 1


def test_heartbeat_registered_worker(client: TestClient) -> None:
    """Test heartbeat for registered worker."""
    # First register a worker
    registration = {
        "worker_id": "test-worker-2",
        "worker_url": "https://localhost:8501",
        "capabilities": [
            {"name": "test.capability", "verb": "invoke", "version": "1.0.0"}
        ],
    }
    client.post("/register", json=registration)

    # Send heartbeat
    heartbeat = {"worker_id": "test-worker-2"}
    response = client.post("/heartbeat", json=heartbeat)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["acknowledged"] is True


def test_heartbeat_unknown_worker(client: TestClient) -> None:
    """Test heartbeat for unknown worker."""
    heartbeat = {"worker_id": "unknown-worker"}
    response = client.post("/heartbeat", json=heartbeat)

    assert response.status_code == 404
    data = response.json()
    assert data["status"] == "unknown_worker"
    assert data["acknowledged"] is False


def test_route_capability(client: TestClient) -> None:
    """Test capability routing."""
    # Register a worker with capability
    registration = {
        "worker_id": "test-worker-3",
        "worker_url": "https://localhost:8502",
        "capabilities": [
            {"name": "document.convert", "verb": "invoke", "version": "1.0.0"}
        ],
    }
    client.post("/register", json=registration)

    # Route to the capability
    route_request = {
        "verb": "invoke",
        "capability": "document.convert",
    }
    response = client.post("/route", json=route_request)

    assert response.status_code == 200
    data = response.json()
    assert data["worker_id"] == "test-worker-3"
    assert data["worker_url"] == "https://localhost:8502"
    assert data["capability"] == "invoke:document.convert"


def test_route_missing_capability(client: TestClient) -> None:
    """Test routing for capability with no workers."""
    route_request = {
        "verb": "invoke",
        "capability": "missing.capability",
    }
    response = client.post("/route", json=route_request)

    assert response.status_code == 404
    assert "No worker available" in response.json()["detail"]


def test_deregister_worker(client: TestClient) -> None:
    """Test worker deregistration."""
    # Register a worker
    registration = {
        "worker_id": "test-worker-4",
        "worker_url": "https://localhost:8503",
        "capabilities": [
            {"name": "test.capability", "verb": "invoke", "version": "1.0.0"}
        ],
    }
    client.post("/register", json=registration)

    # Deregister the worker
    response = client.delete("/deregister/test-worker-4")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deregistered"
    assert data["worker_id"] == "test-worker-4"

    # Verify worker is gone (routing should fail)
    route_request = {"verb": "invoke", "capability": "test.capability"}
    route_response = client.post("/route", json=route_request)
    assert route_response.status_code == 404


def test_get_capabilities(client: TestClient) -> None:
    """Test getting all capabilities."""
    # Register workers with capabilities
    client.post("/register", json={
        "worker_id": "worker-a",
        "worker_url": "https://localhost:8510",
        "capabilities": [
            {"name": "cap.a", "verb": "invoke", "version": "1.0.0"}
        ],
    })
    client.post("/register", json={
        "worker_id": "worker-b",
        "worker_url": "https://localhost:8511",
        "capabilities": [
            {"name": "cap.a", "verb": "invoke", "version": "1.0.0"},  # Same capability
            {"name": "cap.b", "verb": "query", "version": "1.0.0"},
        ],
    })

    response = client.get("/capabilities")

    assert response.status_code == 200
    data = response.json()
    capabilities = data["capabilities"]

    assert "invoke:cap.a" in capabilities
    assert capabilities["invoke:cap.a"]["workers"] == 2
    assert "query:cap.b" in capabilities
    assert capabilities["query:cap.b"]["workers"] == 1


def test_get_workers(client: TestClient) -> None:
    """Test getting all workers."""
    # Register some workers
    client.post("/register", json={
        "worker_id": "worker-x",
        "worker_url": "https://localhost:8520",
        "capabilities": [
            {"name": "test.x", "verb": "invoke", "version": "1.0.0"}
        ],
    })
    client.post("/register", json={
        "worker_id": "worker-y",
        "worker_url": "https://localhost:8521",
        "capabilities": [
            {"name": "test.y", "verb": "invoke", "version": "1.0.0"}
        ],
    })

    response = client.get("/workers")

    assert response.status_code == 200
    data = response.json()
    workers = data["workers"]

    assert len(workers) == 2
    worker_ids = [w["worker_id"] for w in workers]
    assert "worker-x" in worker_ids
    assert "worker-y" in worker_ids

    # Check worker structure
    worker_x = next(w for w in workers if w["worker_id"] == "worker-x")
    assert worker_x["worker_url"] == "https://localhost:8520"
    assert worker_x["is_healthy"] is True
    assert "last_heartbeat" in worker_x
    assert "invoke:test.x" in worker_x["capabilities"]


def test_multiple_workers_same_capability(client: TestClient) -> None:
    """Test routing when multiple workers provide same capability."""
    # Register multiple workers with same capability
    for i in range(3):
        client.post("/register", json={
            "worker_id": f"worker-multi-{i}",
            "worker_url": f"https://localhost:{8600+i}",
            "capabilities": [
                {"name": "common.capability", "verb": "invoke", "version": "1.0.0"}
            ],
        })

    # Route should return one of the workers (first healthy)
    route_request = {"verb": "invoke", "capability": "common.capability"}
    response = client.post("/route", json=route_request)

    assert response.status_code == 200
    data = response.json()
    assert data["worker_id"] in ["worker-multi-0", "worker-multi-1", "worker-multi-2"]


def test_extended_capability_fields(client: TestClient) -> None:
    """Test registration with extended capability fields."""
    registration = {
        "worker_id": "worker-extended",
        "worker_url": "https://localhost:8700",
        "capabilities": [
            {
                "name": "advanced.process",
                "verb": "invoke",
                "version": "2.0.0",
                "runtime": "python3.11",
                "env_profile": "gpu-required",
                "constraints": {"min_memory_mb": 4096, "gpu_count": 1},
                "slo": {"latency_p95_ms": 100},
                "spiffe_id": "spiffe://crank.local/worker/advanced",
                "required_capabilities": ["storage:write"],
                "cost_tokens_per_invocation": 0.05,
                "slo_bid": 0.1,
                "controller_affinity": ["controller-primary"],
            }
        ],
    }

    response = client.post("/register", json=registration)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "registered"
    assert data["capabilities_registered"] == 1

    # Verify we can route to this capability
    route_response = client.post("/route", json={
        "verb": "invoke",
        "capability": "advanced.process",
    })
    assert route_response.status_code == 200
    assert route_response.json()["worker_id"] == "worker-extended"
