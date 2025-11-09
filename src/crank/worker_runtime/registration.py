"""
Worker Registration and Controller Communication

Handles:
- Worker registration with controller
- Heartbeat mechanism with retry logic
- Controller discovery
- HTTP client management with proper SSL/TLS
"""

import asyncio
import logging
import os
from typing import Optional

import httpx
from pydantic import BaseModel, Field

from crank.capabilities.schema import CapabilityDefinition

logger = logging.getLogger(__name__)


class WorkerRegistration(BaseModel):
    """
    Worker registration information sent to controller.

    This model defines what information workers provide during
    registration. Controllers use this to route requests.
    """

    worker_id: str = Field(description="Unique identifier for this worker instance")
    service_type: str = Field(description="Legacy service type name (deprecated, use capabilities)")
    endpoint: str = Field(description="Base URL where this worker can be reached")
    health_url: str = Field(description="Health check endpoint URL")
    capabilities: list[str] = Field(
        description="List of capability IDs this worker provides",
        default_factory=list,
    )


class ControllerClient:
    """
    Manages communication with the controller.

    Handles:
    - Worker registration
    - Periodic heartbeats
    - Retry logic with exponential backoff
    - SSL/TLS configuration
    """

    def __init__(
        self,
        worker_id: str,
        worker_url: str,
        capabilities: list[CapabilityDefinition],
        controller_url: Optional[str] = None,
        auth_token: Optional[str] = None,
    ) -> None:
        """
        Initialize controller client.

        Args:
            worker_id: Unique identifier for this worker
            worker_url: Base URL where this worker is accessible
            capabilities: List of capabilities this worker provides
            controller_url: Controller endpoint (defaults to PLATFORM_URL env var)
            auth_token: Authentication token (defaults to PLATFORM_AUTH_TOKEN env var)
        """
        self.worker_id = worker_id
        self.worker_url = worker_url
        self.capabilities = capabilities

        # Controller connection settings (with backwards-compatible defaults)
        self.controller_url = controller_url or os.getenv(
            "PLATFORM_URL",
            "https://crank-platform-dev:8443",
        )
        self.auth_token = auth_token or os.getenv(
            "PLATFORM_AUTH_TOKEN",
            "local-dev-key",
        )

        # Heartbeat state
        self.heartbeat_task: Optional[asyncio.Task[None]] = None
        self.heartbeat_interval = int(os.getenv("WORKER_HEARTBEAT_INTERVAL", "30"))
        self.heartbeat_retry_interval = int(os.getenv("WORKER_HEARTBEAT_RETRY", "5"))

    def _create_http_client(self, timeout: float = 30.0) -> httpx.AsyncClient:
        """
        Create HTTP client with proper SSL configuration.

        For development environments, SSL verification is disabled
        but connection pooling is maintained for stability.
        """
        return httpx.AsyncClient(
            verify=False,  # TODO: Enable SSL verification with proper cert chain
            timeout=timeout,
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
            ),
        )

    async def register(self) -> None:
        """
        Register this worker with the controller.

        Uses exponential backoff retry logic to handle controller
        startup race conditions.
        """
        # Build capability ID list from capability definitions
        capability_ids = [cap.id for cap in self.capabilities]

        # Legacy service_type - derive from first capability or use generic
        service_type = (
            self.capabilities[0].id.split(".")[0]
            if self.capabilities
            else "generic_worker"
        )

        worker_info = WorkerRegistration(
            worker_id=self.worker_id,
            service_type=service_type,
            endpoint=self.worker_url,
            health_url=f"{self.worker_url}/health",
            capabilities=capability_ids,
        )

        registration_url = f"{self.controller_url}/v1/workers/register"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

        # Retry registration with exponential backoff
        max_retries = 5
        retry_count = 0

        while retry_count < max_retries:
            try:
                async with self._create_http_client() as client:
                    logger.info(
                        f"📝 Registering worker {self.worker_id} with controller "
                        f"(attempt {retry_count + 1}/{max_retries})"
                    )

                    response = await client.post(
                        registration_url,
                        json=worker_info.model_dump(),
                        headers=headers,
                    )

                    if response.status_code == 200:
                        logger.info(f"✅ Worker {self.worker_id} registered successfully")
                        logger.info(f"   Capabilities: {', '.join(capability_ids)}")
                        return

                    logger.warning(
                        f"⚠️  Registration returned status {response.status_code}: {response.text}"
                    )

            except Exception as e:
                logger.warning(f"⚠️  Registration attempt {retry_count + 1} failed: {e}")

            retry_count += 1
            if retry_count < max_retries:
                backoff = min(2**retry_count, 30)  # Cap at 30 seconds
                logger.info(f"   Retrying in {backoff} seconds...")
                await asyncio.sleep(backoff)

        logger.error(f"❌ Failed to register worker after {max_retries} attempts")

    async def send_heartbeat(self) -> None:
        """Send a heartbeat to the controller to maintain registration."""
        heartbeat_url = f"{self.controller_url}/v1/workers/{self.worker_id}/heartbeat"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

        try:
            async with self._create_http_client(timeout=10.0) as client:
                response = await client.post(heartbeat_url, headers=headers)

                if response.status_code == 200:
                    logger.debug(f"💓 Heartbeat sent for worker {self.worker_id}")
                else:
                    logger.warning(
                        f"⚠️  Heartbeat failed with status {response.status_code}"
                    )

        except Exception as e:
            logger.warning(f"💔 Heartbeat error: {e}")

    def start_heartbeat(self) -> None:
        """Start the background heartbeat task."""

        async def heartbeat_loop() -> None:
            """Run heartbeat loop with error handling."""
            # Initial delay before first heartbeat
            await asyncio.sleep(5)

            while True:
                try:
                    await self.send_heartbeat()
                    await asyncio.sleep(self.heartbeat_interval)
                except Exception as e:
                    logger.exception(f"💔 Heartbeat loop error: {e}")
                    # Shorter retry interval on failure
                    await asyncio.sleep(self.heartbeat_retry_interval)

        # Create and store task reference to prevent garbage collection
        self.heartbeat_task = asyncio.create_task(heartbeat_loop())
        logger.info(
            f"💓 Heartbeat started (interval: {self.heartbeat_interval}s, "
            f"retry: {self.heartbeat_retry_interval}s)"
        )

    async def stop_heartbeat(self) -> None:
        """Stop the heartbeat task gracefully."""
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
            logger.info("💓 Heartbeat stopped")
