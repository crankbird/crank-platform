"""Integration tests for worker-controller interaction.

Tests the complete lifecycle: worker startup -> register -> heartbeat -> routing.
"""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from fastapi.testclient import TestClient

from services.crank_controller import ControllerService
from services.crank_hello_world import HelloWorldWorker


@pytest.fixture
def temp_state_file() -> Path:
    """Provide temporary state file for controller tests."""
    with NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
        return Path(f.name)


@pytest.fixture
def controller(temp_state_file: Path) -> ControllerService:
    """Create controller service for testing."""
    # Override environment to use test state file
    os.environ["CONTROLLER_STATE_FILE"] = str(temp_state_file)
    controller = ControllerService(https_port=9999)
    return controller


@pytest.fixture
def controller_client(controller: ControllerService) -> TestClient:
    """Create test client for controller API."""
    return TestClient(controller.app)


@pytest.fixture
def worker() -> HelloWorldWorker:
    """Create hello world worker for testing."""
    # Set controller URL to test controller (HTTPS only - no HTTP capability exists)
    os.environ["CONTROLLER_URL"] = "https://localhost:9999"
    os.environ["HELLO_WORLD_HTTPS_PORT"] = "8500"

    worker = HelloWorldWorker()
    return worker


def test_worker_registers_with_controller(
    controller_client: TestClient,
    worker: HelloWorldWorker,
) -> None:
    """Test worker registration lifecycle.

    Flow:
    1. Worker prepares capabilities
    2. Registration sent to controller via HTTPS API
    3. Controller tracks worker
    4. Routing finds worker by capability
    """
    # Manually register worker using controller's API
    # (simulates what worker.on_startup() does)
    capabilities = [
        {
            "name": cap.id,
            "verb": "invoke",
            "version": f"{cap.version.major}.{cap.version.minor}.{cap.version.patch}",
            "input_schema": cap.contract.input_schema,
            "output_schema": cap.contract.output_schema,
        }
        for cap in worker.get_capabilities()
    ]

    registration_payload = {
        "worker_id": worker.worker_id,
        "worker_url": worker.worker_url,
        "capabilities": capabilities,
    }

    # Send registration via TestClient
    response = controller_client.post("/register", json=registration_payload)
    assert response.status_code == 200

    result = response.json()
    assert result["status"] == "registered"
    assert result["worker_id"] == worker.worker_id
    assert result["capabilities_registered"] == 1

    # Verify controller sees worker
    response = controller_client.get("/workers")
    assert response.status_code == 200

    workers = response.json()["workers"]
    assert len(workers) == 1
    assert workers[0]["worker_id"] == worker.worker_id
    assert workers[0]["worker_url"] == worker.worker_url
@pytest.mark.asyncio
async def test_controller_routes_to_registered_worker(
    controller_client: TestClient,
    worker: HelloWorldWorker,
) -> None:
    """Test capability-based routing to registered worker.

    Flow:
    1. Worker registers with controller
    2. Request routing for capability
    3. Controller returns worker endpoint
    """
    # Register worker
    await worker.on_startup()

    # Request routing for hello world capability
    route_request = {
        "verb": "invoke",
        "capability": "example.hello_world",
    }

    response = controller_client.post("/route", json=route_request)
    assert response.status_code == 200

    route = response.json()
    assert route["worker_id"] == worker.worker_id
    assert route["worker_url"] == worker.worker_url
    assert route["capability"] == "invoke:example.hello_world"


@pytest.mark.asyncio
async def test_controller_lists_worker_capabilities(
    controller_client: TestClient,
    worker: HelloWorldWorker,
) -> None:
    """Test controller capability introspection.

    Flow:
    1. Worker registers with capabilities
    2. Query controller for all capabilities
    3. Verify hello world capability present
    """
    # Register worker
    await worker.on_startup()

    # Query capabilities
    response = controller_client.get("/capabilities")
    assert response.status_code == 200

    capabilities = response.json()["capabilities"]

    # Verify hello world capability registered
    assert "invoke:example.hello_world" in capabilities
    cap_info = capabilities["invoke:example.hello_world"]
    assert cap_info["workers"] == 1
    assert cap_info["healthy_workers"] == 1


@pytest.mark.asyncio
async def test_worker_runs_standalone_without_controller(
    temp_state_file: Path,
) -> None:
    """Test worker operates without controller (graceful degradation).

    Flow:
    1. Worker starts without CONTROLLER_URL set
    2. Worker continues operating
    3. No registration errors
    """
    # Remove controller URL
    if "CONTROLLER_URL" in os.environ:
        del os.environ["CONTROLLER_URL"]

    worker = HelloWorldWorker()

    # Trigger startup - should not fail
    await worker.on_startup()

    # Verify worker not registered
    assert not worker.registered_with_controller

    # But worker is still functional
    assert len(worker.get_capabilities()) == 1
    assert worker.engine.greeting_count == 0
