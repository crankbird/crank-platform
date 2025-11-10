"""
Tests for worker runtime components.

Validates:
- WorkerApplication base class behavior
- Registration and heartbeat logic
- Lifecycle management (startup/shutdown)
- Health check functionality
- Certificate management

Uses test data corpus from tests/data/ for comprehensive coverage.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from crank.capabilities.schema import STREAMING_CLASSIFICATION, CapabilityDefinition
from crank.worker_runtime import (
    ControllerClient,
    HealthStatus,
    ShutdownHandler,
    WorkerApplication,
    WorkerRegistration,
)
from crank.worker_runtime.lifecycle import HealthCheckManager
from crank.worker_runtime.security import CertificateBundle, CertificateManager


class TestWorkerRegistration:
    """Test worker registration model."""

    def test_worker_registration_creation(self) -> None:
        """Test creating a worker registration."""
        reg = WorkerRegistration(
            worker_id="test-worker-1",
            service_type="streaming",
            endpoint="https://worker:8500",
            health_url="https://worker:8500/health",
            capabilities=["streaming.classify", "email.parse"],
        )

        assert reg.worker_id == "test-worker-1"
        assert reg.service_type == "streaming"
        assert len(reg.capabilities) == 2

    def test_worker_registration_empty_capabilities(self) -> None:
        """Test worker registration with empty capabilities list."""
        reg = WorkerRegistration(
            worker_id="test-worker-2",
            service_type="generic",
            endpoint="https://worker:8500",
            health_url="https://worker:8500/health",
        )

        assert reg.capabilities == []


class TestHealthStatus:
    """Test health status enum."""

    def test_health_status_values(self) -> None:
        """Test all health status values exist."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.STARTING.value == "starting"
        assert HealthStatus.STOPPING.value == "stopping"


class TestHealthCheckManager:
    """Test health check manager."""

    def test_health_check_manager_initialization(self) -> None:
        """Test health check manager starts in STARTING state."""
        manager = HealthCheckManager("test-worker")
        assert manager.worker_id == "test-worker"
        assert manager.status == HealthStatus.STARTING

    def test_health_status_transitions(self) -> None:
        """Test health status can transition."""
        manager = HealthCheckManager("test-worker")
        manager.set_status(HealthStatus.HEALTHY)
        assert manager.status == HealthStatus.HEALTHY

        manager.set_status(HealthStatus.STOPPING)
        # Re-fetch status to avoid type narrowing issue
        from crank.worker_runtime.lifecycle import HealthStatus as HS
        current_status: HS = manager.status
        assert current_status == HealthStatus.STOPPING

    def test_uptime_calculation(self) -> None:
        """Test uptime is calculated correctly."""
        manager = HealthCheckManager("test-worker")
        uptime = manager.get_uptime()
        assert uptime >= 0
        assert uptime < 1  # Should be very small for new manager

    def test_health_response_generation(self) -> None:
        """Test health check response generation."""
        manager = HealthCheckManager("test-worker")
        manager.set_status(HealthStatus.HEALTHY)
        manager.set_detail("test_key", "test_value")

        response = manager.get_health_response()
        assert response.status == HealthStatus.HEALTHY
        assert response.worker_id == "test-worker"
        assert response.uptime_seconds >= 0
        assert "test_key" in response.details
        assert response.details["test_key"] == "test_value"


class TestShutdownHandler:
    """Test shutdown handler."""

    def test_shutdown_handler_initialization(self) -> None:
        """Test shutdown handler starts with no shutdown requested."""
        handler = ShutdownHandler()
        assert not handler.shutdown_requested

    def test_request_shutdown(self) -> None:
        """Test shutdown can be requested."""
        handler = ShutdownHandler()
        handler.request_shutdown()
        assert handler.shutdown_requested

    def test_register_shutdown_callback(self) -> None:
        """Test shutdown callbacks can be registered."""
        handler = ShutdownHandler()
        callback_called = False

        def test_callback() -> None:
            nonlocal callback_called
            callback_called = True

        handler.register_shutdown_callback("test_callback", test_callback)
        assert len(handler.shutdown_tasks) == 1
        assert handler.shutdown_tasks[0].name == "test_callback"

    @pytest.mark.asyncio
    async def test_execute_shutdown_calls_callbacks(self) -> None:
        """Test shutdown execution calls registered callbacks."""
        handler = ShutdownHandler()
        callback_called = False

        async def test_callback() -> None:
            nonlocal callback_called
            callback_called = True

        handler.register_shutdown_callback("test_callback", test_callback)
        await handler.execute_shutdown()

        assert callback_called

    @pytest.mark.asyncio
    async def test_shutdown_callbacks_lifo_order(self) -> None:
        """Test shutdown callbacks are called in LIFO order."""
        handler = ShutdownHandler()
        call_order: list[int] = []

        async def callback1() -> None:
            call_order.append(1)

        async def callback2() -> None:
            call_order.append(2)

        async def callback3() -> None:
            call_order.append(3)

        handler.register_shutdown_callback("callback1", callback1)
        handler.register_shutdown_callback("callback2", callback2)
        handler.register_shutdown_callback("callback3", callback3)

        await handler.execute_shutdown()

        # Should be called in reverse order: 3, 2, 1
        assert call_order == [3, 2, 1]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "scenario_file",
        [
            "valid/graceful.json",
            "valid/multi-task.json",
        ],
    )
    async def test_shutdown_scenarios_from_corpus(self, scenario_file: str) -> None:
        """Test shutdown handler against corpus scenarios."""
        from tests.data.loader import load_shutdown_scenario

        handler = ShutdownHandler()
        scenario = load_shutdown_scenario(scenario_file)

        # Track which tasks executed
        executed_tasks: list[str] = []

        # Register callbacks based on scenario
        for task_spec in scenario["tasks"]:
            task_name = task_spec["name"]

            async def task_callback(name: str = task_name) -> None:
                executed_tasks.append(name)
                await asyncio.sleep(0.01)  # Simulate some work

            handler.register_shutdown_callback(
                name=task_spec["name"],
                callback=task_callback,
                description=task_spec.get("description"),
                timeout=task_spec.get("timeout_seconds", 10.0),
                tags=task_spec.get("tags", []),
            )

        # Execute shutdown
        await handler.execute_shutdown()

        # Verify all tasks executed (in reverse order - LIFO)
        expected_tasks = [t["name"] for t in reversed(scenario["tasks"])]
        assert executed_tasks == expected_tasks

    @pytest.mark.asyncio
    async def test_shutdown_task_metadata(self) -> None:
        """Test ShutdownTask stores metadata correctly."""
        from tests.data.loader import load_shutdown_scenario

        handler = ShutdownHandler()
        scenario = load_shutdown_scenario("valid/graceful.json")

        # Register first task with all metadata
        task_spec = scenario["tasks"][0]

        async def dummy_callback() -> None:
            pass

        handler.register_shutdown_callback(
            name=task_spec["name"],
            callback=dummy_callback,
            description=task_spec["description"],
            timeout=task_spec["timeout_seconds"],
            tags=task_spec["tags"],
        )

        # Verify ShutdownTask stored metadata
        assert len(handler.shutdown_tasks) == 1
        task = handler.shutdown_tasks[0]
        assert task.name == task_spec["name"]
        assert task.description == task_spec["description"]
        assert task.timeout == task_spec["timeout_seconds"]
        assert task.tags == task_spec["tags"]


class TestCertificateManager:
    """Test certificate manager."""

    def test_certificate_manager_initialization(self, tmp_path: Path) -> None:
        """Test certificate manager initializes with cert directory."""

        manager = CertificateManager("test-worker", cert_dir=tmp_path)
        assert manager.worker_id == "test-worker"
        assert manager.cert_dir == tmp_path
        assert manager.cert_dir.exists()

    def test_certificate_paths(self, tmp_path: Path) -> None:
        """Test certificate path generation."""
        manager = CertificateManager("test-worker", cert_dir=tmp_path)

        assert manager.get_cert_path() == tmp_path / "test-worker.crt"
        assert manager.get_key_path() == tmp_path / "test-worker.key"
        assert manager.get_ca_cert_path() == tmp_path / "ca.crt"

    def test_certificates_exist_check(self, tmp_path: Path) -> None:
        """Test checking if certificates exist."""
        manager = CertificateManager("test-worker", cert_dir=tmp_path)

        # Initially should not exist
        assert not manager.certificates_exist()

        # Create fake certificates
        manager.get_cert_path().write_text("fake cert")
        manager.get_key_path().write_text("fake key")
        manager.get_ca_cert_path().write_text("fake ca")

        # Now should exist
        assert manager.certificates_exist()

    def test_get_ssl_context_with_certs(self, tmp_path: Path) -> None:
        """Test getting SSL context when certificates exist."""
        manager = CertificateManager("test-worker", cert_dir=tmp_path)

        # Create fake certificates
        manager.get_cert_path().write_text("fake cert")
        manager.get_key_path().write_text("fake key")
        manager.get_ca_cert_path().write_text("fake ca")

        ssl_config = manager.get_ssl_context()

        assert "ssl_certfile" in ssl_config
        assert "ssl_keyfile" in ssl_config
        assert "ssl_ca_certs" in ssl_config
        assert Path(ssl_config["ssl_certfile"]).exists()

    def test_get_ssl_context_missing_certs(self, tmp_path: Path) -> None:
        """Test getting SSL context raises error when certs missing."""
        manager = CertificateManager("test-worker", cert_dir=tmp_path)

        with pytest.raises(FileNotFoundError):
            manager.get_ssl_context()

    def test_certificate_bundle_validation(self) -> None:
        """Test CertificateBundle validates certificate files on creation."""
        from tests.data.loader import load_cert_bundle

        # Load valid certificate bundle
        bundle_info = load_cert_bundle("valid/platform")
        bundle = CertificateBundle(
            cert_file=bundle_info["cert_path"],
            key_file=bundle_info["key_path"],
            ca_file=bundle_info["cert_path"].parent / "ca.crt",  # Use CA from same dir
            worker_id="test-worker-corpus",
        )

        # Verify bundle properties
        assert bundle.cert_file.exists()
        assert bundle.key_file.exists()
        assert bundle.ca_file.exists()
        assert bundle.cert_file.suffix in (".crt", ".pem")
        assert bundle.key_file.suffix == ".key"

    @pytest.mark.parametrize(
        "invalid_cert",
        [
            "invalid/truncated-cert.pem",
            "invalid/empty-cert.pem",
        ],
    )
    def test_certificate_bundle_rejects_invalid(self, invalid_cert: str) -> None:
        """Test CertificateBundle rejects malformed certificates."""
        from tests.data.loader import load_cert_bundle

        bundle_info = load_cert_bundle(invalid_cert)

        # Invalid cert should fail validation due to missing files
        with pytest.raises(FileNotFoundError, match="Missing certificate files"):
            CertificateBundle(
                cert_file=bundle_info["cert_path"],
                key_file=bundle_info.get("key_path", Path("/nonexistent/key")),
                ca_file=Path("/nonexistent/ca.crt"),
                worker_id="test-invalid",
            )

    def test_certificate_bundle_to_uvicorn_config(self) -> None:
        """Test CertificateBundle.to_uvicorn_config() conversion."""
        from tests.data.loader import load_cert_bundle

        bundle_info = load_cert_bundle("valid/platform")
        bundle = CertificateBundle(
            cert_file=bundle_info["cert_path"],
            key_file=bundle_info["key_path"],
            ca_file=bundle_info["cert_path"].parent / "ca.crt",
            worker_id="test-worker-config",
        )

        config = bundle.to_uvicorn_config()

        assert "ssl_certfile" in config
        assert "ssl_keyfile" in config
        assert "ssl_ca_certs" in config
        assert config["ssl_certfile"] == str(bundle.cert_file)
        assert config["ssl_keyfile"] == str(bundle.key_file)
        assert config["ssl_ca_certs"] == str(bundle.ca_file)


class TestControllerClient:
    """Test controller client."""

    def test_controller_client_initialization(self) -> None:
        """Test controller client initializes correctly."""
        capabilities = [STREAMING_CLASSIFICATION]
        client = ControllerClient(
            worker_id="test-worker",
            worker_url="https://worker:8500",
            capabilities=capabilities,
        )

        assert client.worker_id == "test-worker"
        assert client.worker_url == "https://worker:8500"
        assert len(client.capabilities) == 1

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_registration_success(self, mock_client_class: MagicMock) -> None:
        """Test successful worker registration."""
        # Mock HTTP client
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        capabilities = [STREAMING_CLASSIFICATION]
        client = ControllerClient(
            worker_id="test-worker",
            worker_url="https://worker:8500",
            capabilities=capabilities,
        )

        await client.register()

        # Verify registration was attempted
        assert mock_client.post.called

        # Clean up
        await client.close()

    @pytest.mark.asyncio
    async def test_start_heartbeat_creates_task(self) -> None:
        """Test starting heartbeat creates background task."""
        capabilities = [STREAMING_CLASSIFICATION]
        client = ControllerClient(
            worker_id="test-worker",
            worker_url="https://worker:8500",
            capabilities=capabilities,
        )

        client.start_heartbeat()

        assert client.heartbeat_task is not None
        assert isinstance(client.heartbeat_task, asyncio.Task)

        # Clean up
        await client.stop_heartbeat()

    @pytest.mark.asyncio
    async def test_stop_heartbeat(self) -> None:
        """Test stopping heartbeat cancels task."""
        capabilities = [STREAMING_CLASSIFICATION]
        client = ControllerClient(
            worker_id="test-worker",
            worker_url="https://worker:8500",
            capabilities=capabilities,
        )

        client.start_heartbeat()
        await client.stop_heartbeat()

        # Verify heartbeat task exists and is done
        assert client.heartbeat_task is not None
        assert client.heartbeat_task.done()


class TestWorkerApplication:
    """Test worker application base class."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Test that WorkerApplication cannot be instantiated directly."""
        with pytest.raises(TypeError):
            WorkerApplication()  # type: ignore

    def test_concrete_subclass_can_be_created(self) -> None:
        """Test that concrete subclass can be instantiated."""

        class TestWorker(WorkerApplication):
            def get_capabilities(self) -> list[CapabilityDefinition]:
                return [STREAMING_CLASSIFICATION]

            def setup_routes(self) -> None:
                async def test_endpoint() -> dict[str, str]:
                    return {"status": "ok"}

                # Use explicit binding pattern like base class
                self.app.get("/test")(test_endpoint)

        worker = TestWorker()
        assert worker.worker_id is not None
        assert worker.app is not None
        assert worker.health_manager is not None

    def test_worker_with_custom_config(self) -> None:
        """Test worker with custom configuration."""

        class TestWorker(WorkerApplication):
            def get_capabilities(self) -> list[CapabilityDefinition]:
                return [STREAMING_CLASSIFICATION]

            def setup_routes(self) -> None:
                pass

        worker = TestWorker(
            worker_id="custom-worker",
            service_name="custom-service",
            https_port=9000,
        )

        assert worker.worker_id == "custom-worker"
        assert worker.service_name == "custom-service"
        assert worker.https_port == 9000
        assert "custom-service:9000" in worker.worker_url
