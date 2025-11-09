"""
Worker Application Base Class

Provides the foundation for all Crank workers, handling:
- Lifecycle management (startup, shutdown)
- Controller registration and heartbeat
- Health check endpoints
- Certificate management
- FastAPI application setup

Workers subclass WorkerApplication and implement business logic.

Implementation Notes:
- Route handlers use explicit binding (self.app.get("/path")(handler))
  instead of decorators to avoid Pylance "not accessed" warnings
- Optional hooks (on_startup, on_shutdown) have explicit return None
  to satisfy Ruff B027 linter rule
- Lifespan context manager used instead of deprecated @app.on_event()
"""

import abc
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from crank.capabilities.schema import CapabilityDefinition
from crank.worker_runtime.lifecycle import (
    HealthCheckManager,
    HealthStatus,
    ShutdownHandler,
)
from crank.worker_runtime.registration import ControllerClient
from crank.worker_runtime.security import CertificateManager

logger = logging.getLogger(__name__)


class WorkerApplication(abc.ABC):
    """
    Base class for all Crank workers.

    Provides common infrastructure:
    - FastAPI application with health checks
    - Controller registration and heartbeat
    - Graceful shutdown handling
    - Certificate management

    Subclasses implement:
    - get_capabilities(): Return list of CapabilityDefinition
    - setup_routes(): Register FastAPI routes for business logic
    - on_startup(): Optional additional startup logic
    - on_shutdown(): Optional additional shutdown logic
    """

    def __init__(
        self,
        worker_id: Optional[str] = None,
        service_name: Optional[str] = None,
        https_port: int = 8500,
    ) -> None:
        """
        Initialize worker application.

        Args:
            worker_id: Unique identifier (defaults to auto-generated UUID)
            service_name: Service name for URL construction (defaults to hostname)
            https_port: HTTPS port for this worker
        """
        # Worker identity
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.service_name = service_name or f"{self.worker_id}-service"
        self.https_port = https_port
        self.worker_url = f"https://{self.service_name}:{https_port}"

        # Core components
        self.shutdown_handler = ShutdownHandler()
        self.health_manager = HealthCheckManager(self.worker_id)
        self.cert_manager = CertificateManager(self.worker_id)
        self.controller_client: Optional[ControllerClient] = None

        # Initialize FastAPI with lifespan handler
        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncIterator[None]:
            """Lifespan context manager for startup and shutdown."""
            # Startup
            await self._startup_handler()
            yield
            # Shutdown
            await self._shutdown_handler()

        self.app = FastAPI(
            title=f"Crank Worker: {self.worker_id}",
            lifespan=lifespan,
        )

        # Set up core infrastructure
        self._setup_core_routes()
        self.shutdown_handler.setup_signal_handlers()

        logger.info(f"🏗️  Worker {self.worker_id} initialized")
        logger.info(f"   URL: {self.worker_url}")

    # ========================================================================
    # Abstract Methods - Subclasses MUST implement
    # ========================================================================

    @abc.abstractmethod
    def get_capabilities(self) -> list[CapabilityDefinition]:
        """
        Return the capabilities this worker provides.

        Returns:
            List of CapabilityDefinition objects from capabilities.schema

        Example:
            from crank.capabilities.schema import STREAMING_CLASSIFICATION

            def get_capabilities(self):
                return [STREAMING_CLASSIFICATION]
        """
        ...

    @abc.abstractmethod
    def setup_routes(self) -> None:
        """
        Register FastAPI routes for business logic.

        Use self.app to register routes:
            @self.app.post("/classify")
            async def classify(request: ClassifyRequest):
                return result

        This is called during worker initialization.
        """
        ...

    # ========================================================================
    # Optional Override Methods
    # ========================================================================

    async def on_startup(self) -> None:
        """
        Optional startup hook for additional initialization.

        Called after controller registration but before accepting requests.
        Override this to perform custom startup tasks.

        Note: Explicit 'return None' satisfies Ruff B027 (empty method in ABC).
        """
        return None

    async def on_shutdown(self) -> None:
        """
        Optional shutdown hook for cleanup.

        Called during graceful shutdown before heartbeat stops.
        Override this to perform custom cleanup tasks.

        Note: Explicit 'return None' satisfies Ruff B027 (empty method in ABC).
        """
        return None

    # ========================================================================
    # Core Infrastructure (Private)
    # ========================================================================

    def _setup_core_routes(self) -> None:
        """Set up standard health check and status routes."""

        async def health_check() -> JSONResponse:
            """Health check endpoint for container orchestration."""
            health = self.health_manager.get_health_response()
            status_code = 200 if health.status == HealthStatus.HEALTHY else 503
            return JSONResponse(
                content=health.model_dump(),
                status_code=status_code,
            )

        # Use explicit binding instead of @decorator to avoid Pylance "not accessed" warnings
        # Pattern: self.app.get("/path")(handler) gives language server a concrete reference
        self.app.get("/health")(health_check)

        async def status() -> dict[str, Any]:
            """Detailed status endpoint."""
            return {
                "worker_id": self.worker_id,
                "capabilities": [cap.id for cap in self.get_capabilities()],
                "uptime_seconds": self.health_manager.get_uptime(),
                "health_status": self.health_manager.status.value,
            }

        # Same explicit binding pattern for consistency
        self.app.get("/status")(status)

    async def _startup_handler(self) -> None:
        """Handle application startup (called by lifespan)."""
        logger.info("🚀 Worker startup initiated")

        # Initialize capabilities and controller client
        capabilities = self.get_capabilities()
        self.controller_client = ControllerClient(
            worker_id=self.worker_id,
            worker_url=self.worker_url,
            capabilities=capabilities,
        )

        # Register with controller
        await self.controller_client.register()

        # Start heartbeat
        self.controller_client.start_heartbeat()

        # Mark worker as healthy
        self.health_manager.set_status(HealthStatus.HEALTHY)

        # Call subclass startup hook
        await self.on_startup()

        logger.info("✅ Worker startup complete")

    async def _shutdown_handler(self) -> None:
        """Handle application shutdown (called by lifespan)."""
        logger.info("🛑 Worker shutdown initiated")
        self.health_manager.set_status(HealthStatus.STOPPING)

        # Call subclass shutdown hook
        await self.on_shutdown()

        # Stop heartbeat
        if self.controller_client:
            await self.controller_client.stop_heartbeat()

        # Execute registered shutdown callbacks
        await self.shutdown_handler.execute_shutdown()

        logger.info("✅ Worker shutdown complete")

    # ========================================================================
    # Public Methods
    # ========================================================================

    def get_ssl_config(self) -> dict[str, str]:
        """
        Get SSL configuration for uvicorn.

        Returns:
            Dictionary with SSL cert paths

        Raises:
            FileNotFoundError: If certificates don't exist
        """
        return self.cert_manager.get_ssl_context()

    def run(
        self,
        host: str = "0.0.0.0",
        log_level: str = "info",
    ) -> None:
        """
        Run the worker application.

        This is typically called from the worker's main script:
            if __name__ == "__main__":
                worker = MyWorker()
                worker.run()

        Args:
            host: Host to bind to
            log_level: Uvicorn log level
        """
        import uvicorn

        # Ensure routes are registered before running
        self.setup_routes()

        # Get SSL configuration
        ssl_config = self.get_ssl_config()

        logger.info(f"🚀 Starting worker {self.worker_id} on {self.worker_url}")

        # Run with uvicorn
        uvicorn.run(
            self.app,
            host=host,
            port=self.https_port,
            log_level=log_level,
            ssl_certfile=ssl_config["ssl_certfile"],
            ssl_keyfile=ssl_config["ssl_keyfile"],
            ssl_ca_certs=ssl_config["ssl_ca_certs"],
        )
