"""
Worker Lifecycle Management

Handles:
- Health check endpoints
- Graceful shutdown coordination
- Readiness probes
- Liveness probes
"""

import asyncio
import logging
import signal
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Type alias for shutdown callbacks (supports both sync and async)
# Union type satisfies Pylance/Mypy type parameter requirements for Callable
# Allows flexibility: def callback() -> None OR async def callback() -> None
ShutdownCallback = Callable[[], None] | Callable[[], Awaitable[None]]


class HealthStatus(str, Enum):
    """
    Health status values for worker health checks.

    Inherits from str to enable direct JSON serialization.
    Use .value when comparing to strings in tests/assertions.
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"


class HealthCheckResponse(BaseModel):
    """Standard health check response model."""

    status: HealthStatus = Field(description="Current health status")
    worker_id: str = Field(description="Unique worker identifier")
    uptime_seconds: float = Field(description="Seconds since worker started")
    timestamp: str = Field(description="ISO timestamp of health check")
    details: dict[str, str] = Field(
        default_factory=dict,
        description="Additional health check details",
    )


class ShutdownHandler:
    """
    Manages graceful shutdown of worker processes.

    Coordinates shutdown across:
    - Heartbeat tasks
    - Active request handlers
    - Background tasks
    - External connections
    """

    def __init__(self) -> None:
        """Initialize shutdown handler."""
        self.shutdown_requested = False
        self.shutdown_callbacks: list[ShutdownCallback] = []
        self._shutdown_event = asyncio.Event()

    def register_shutdown_callback(
        self,
        callback: ShutdownCallback,
    ) -> None:
        """
        Register a callback to be invoked during shutdown.

        Callbacks are invoked in reverse order of registration
        (LIFO - last in, first out).

        Args:
            callback: Sync or async function to call during shutdown
        """
        self.shutdown_callbacks.append(callback)

    def request_shutdown(self) -> None:
        """
        Request graceful shutdown.

        Can be called from signal handlers or application code.
        """
        if not self.shutdown_requested:
            self.shutdown_requested = True
            self._shutdown_event.set()
            logger.info("🛑 Graceful shutdown requested")

    async def wait_for_shutdown(self) -> None:
        """Wait until shutdown is requested."""
        await self._shutdown_event.wait()

    async def execute_shutdown(self, timeout: float = 30.0) -> None:
        """
        Execute all registered shutdown callbacks.

        Args:
            timeout: Maximum time to wait for shutdown completion (seconds)
        """
        if not self.shutdown_requested:
            self.request_shutdown()

        logger.info(f"🛑 Executing shutdown callbacks ({len(self.shutdown_callbacks)})")

        # Execute callbacks in reverse order (LIFO)
        for callback in reversed(self.shutdown_callbacks):
            try:
                logger.debug(f"   Calling shutdown callback: {callback.__name__}")
                if asyncio.iscoroutinefunction(callback):
                    await asyncio.wait_for(callback(), timeout=timeout)
                else:
                    callback()
            except asyncio.TimeoutError:
                logger.warning(f"⚠️  Shutdown callback {callback.__name__} timed out")
            except Exception as e:
                logger.exception(f"❌ Error in shutdown callback {callback.__name__}: {e}")

        logger.info("✅ Shutdown complete")

    def setup_signal_handlers(self) -> None:
        """
        Configure signal handlers for graceful shutdown.

        Handles SIGTERM and SIGINT by requesting graceful shutdown.
        """

        def handle_signal(signum: int, frame: object) -> None:
            """Signal handler that requests shutdown."""
            sig_name = signal.Signals(signum).name
            logger.info(f"📡 Received signal {sig_name}")
            self.request_shutdown()

        # Register signal handlers
        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)
        logger.info("📡 Signal handlers registered (SIGTERM, SIGINT)")


class HealthCheckManager:
    """
    Manages worker health status and health check endpoints.

    Tracks:
    - Worker lifecycle state
    - Uptime
    - Custom health metrics
    """

    def __init__(self, worker_id: str) -> None:
        """
        Initialize health check manager.

        Args:
            worker_id: Unique identifier for this worker
        """
        self.worker_id = worker_id
        self.status = HealthStatus.STARTING
        self.start_time = datetime.now(timezone.utc)
        self.custom_details: dict[str, str] = {}

    def set_status(self, status: HealthStatus) -> None:
        """Update worker health status."""
        old_status = self.status
        self.status = status
        logger.info(f"💊 Health status: {old_status} → {status}")

    def set_detail(self, key: str, value: str) -> None:
        """Add or update a custom health detail."""
        self.custom_details[key] = value

    def get_uptime(self) -> float:
        """Calculate uptime in seconds."""
        now = datetime.now(timezone.utc)
        uptime = (now - self.start_time).total_seconds()
        return uptime

    def get_health_response(self) -> HealthCheckResponse:
        """
        Generate current health check response.

        Returns:
            HealthCheckResponse with current status and details
        """
        return HealthCheckResponse(
            status=self.status,
            worker_id=self.worker_id,
            uptime_seconds=self.get_uptime(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=self.custom_details.copy(),
        )
