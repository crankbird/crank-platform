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
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Type alias for shutdown callbacks (supports both sync and async)
# Union type satisfies Pylance/Mypy type parameter requirements for Callable
# Allows flexibility: def callback() -> None OR async def callback() -> None
ShutdownCallback = Callable[[], None] | Callable[[], Awaitable[None]]


@dataclass
class ShutdownTask:
    """
    Metadata for a shutdown callback.

    Provides observability and per-task timeout control.
    Avoids relying on callback.__name__ which breaks with functools.partial.
    """

    name: str
    callback: ShutdownCallback
    description: str = ""
    timeout: float = 30.0
    tags: list[str] = field(default_factory=list)  # type: ignore[arg-type]


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
        self.shutdown_tasks: list[ShutdownTask] = []
        self._shutdown_event = asyncio.Event()

    def register_shutdown_callback(
        self,
        name: str,
        callback: ShutdownCallback,
        *,
        description: str = "",
        timeout: float = 30.0,
        tags: list[str] | None = None,
    ) -> None:
        """
        Register a callback to be invoked during shutdown.

        Callbacks are invoked in reverse order of registration
        (LIFO - last in, first out).

        Args:
            name: Human-readable name for this shutdown task
            callback: Sync or async function to call during shutdown
            description: Optional detailed description of what this task does
            timeout: Maximum seconds to wait for this specific task
            tags: Optional tags for categorization (e.g., ["database", "critical"])

        Example:
            handler.register_shutdown_callback(
                "database_cleanup",
                cleanup_db,
                description="Flush pending writes and close connections",
                timeout=10.0,
                tags=["database", "critical"],
            )
        """
        task = ShutdownTask(
            name=name,
            callback=callback,
            description=description,
            timeout=timeout,
            tags=tags or [],
        )
        self.shutdown_tasks.append(task)

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

    async def execute_shutdown(self, default_timeout: float = 30.0) -> None:
        """
        Execute all registered shutdown tasks.

        Tasks are executed in reverse order of registration (LIFO).
        Each task uses its own timeout setting.

        Args:
            default_timeout: Fallback timeout for tasks without explicit timeout
        """
        if not self.shutdown_requested:
            self.request_shutdown()

        logger.info(f"🛑 Executing {len(self.shutdown_tasks)} shutdown tasks")

        # Execute tasks in reverse order (LIFO)
        for task in reversed(self.shutdown_tasks):
            task_desc = f"{task.name}"
            if task.description:
                task_desc += f" ({task.description})"

            try:
                logger.debug(f"   Shutdown task: {task_desc}")
                if asyncio.iscoroutinefunction(task.callback):
                    await asyncio.wait_for(task.callback(), timeout=task.timeout)
                else:
                    task.callback()
                logger.debug(f"   ✓ {task.name} completed")
            except asyncio.TimeoutError:
                logger.warning(
                    f"⚠️  Shutdown task '{task.name}' timed out after {task.timeout}s"
                )
            except Exception as e:
                logger.exception(f"❌ Error in shutdown task '{task.name}': {e}")

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
        """
        Calculate uptime in seconds.

        NOTE: Clock injection via callable (self._clock) is DEFERRED.
        Current implementation calls datetime.now() directly.
        For tests requiring deterministic time, add optional _now parameter to get_health_response().
        Future trigger: If time-dependent logic becomes more complex or multiple methods need mocking.
        See: AGENT_CONTEXT.md "Code Beauty Philosophy" for rationale.
        """
        now = datetime.now(timezone.utc)
        uptime = (now - self.start_time).total_seconds()
        return uptime

    def get_health_response(self) -> HealthCheckResponse:
        """
        Generate current health check response.

        TODO: Add optional _now parameter for deterministic testing:
            def get_health_response(self, _now: Optional[datetime] = None) -> HealthCheckResponse:
                now = _now or datetime.now(timezone.utc)
                # Use now throughout to avoid calling datetime.now() 3 times

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
