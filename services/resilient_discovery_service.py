"""
Resilient Discovery Service - KISS Approach

Simple in-memory worker registry with:
- Worker heartbeats (every 30-60 seconds)
- Automatic expiration of stale workers
- Fast worker re-registration on platform restart
- No complex persistence - just resilient patterns

This solves the fragility issue without adding complexity.
"""

import asyncio
import contextlib
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from crank_platform_service import DiscoveryServiceInterface, WorkerInfo

logger = logging.getLogger(__name__)


class ResilientDiscoveryService(DiscoveryServiceInterface):
    """Simple resilient discovery service with worker heartbeats."""

    def __init__(self):
        self.workers: dict[str, list[WorkerInfo]] = {}

        # Configurable timeouts via environment variables
        self.heartbeat_interval = int(os.getenv("WORKER_HEARTBEAT_INTERVAL", "45"))  # seconds
        self.worker_timeout = int(os.getenv("WORKER_TIMEOUT", "120"))  # seconds
        self.cleanup_interval = int(os.getenv("WORKER_CLEANUP_INTERVAL", "30"))  # seconds

        # Derived settings
        self.heartbeat_grace = int(
            os.getenv("WORKER_HEARTBEAT_GRACE", str(self.heartbeat_interval * 2)),
        )

        self.cleanup_task = None

        logger.info("🔄 Resilient discovery configuration:")
        logger.info("   • Heartbeat interval: {self.heartbeat_interval}s")
        logger.info("   • Worker timeout: {self.worker_timeout}s")
        logger.info("   • Cleanup interval: {self.cleanup_interval}s")
        logger.info("   • Heartbeat grace period: {self.heartbeat_grace}s")

    async def initialize(self):
        """Start the cleanup task for expired workers."""
        self.cleanup_task = asyncio.create_task(self._cleanup_expired_workers())
        logger.info("✅ Resilient discovery service initialized")

    async def register_worker(self, worker_info: WorkerInfo) -> bool:
        """Register worker with current timestamp."""
        try:
            # Update last_seen to current time
            worker_info.last_seen = datetime.now(timezone.utc)

            service_type = worker_info.service_type
            if service_type not in self.workers:
                self.workers[service_type] = []

            # Remove existing worker with same ID (if any)
            self.workers[service_type] = [
                w for w in self.workers[service_type] if w.worker_id != worker_info.worker_id
            ]

            # Add new/updated worker
            self.workers[service_type].append(worker_info)

            logger.info("✅ Registered worker {worker_info.worker_id} ({service_type})")
            return True

        except Exception:
            logger.exception("❌ Failed to register worker {worker_info.worker_id}: {e}")
            return False

    async def find_worker(self, service_type: str) -> Optional[WorkerInfo]:
        """Find best available worker for service type."""
        workers = self.workers.get(service_type, [])
        if not workers:
            return None

        # Filter out expired workers
        active_workers = self._filter_active_workers(workers)
        if not active_workers:
            # Clean up the expired workers
            self.workers[service_type] = []
            return None

        # Update the list with only active workers
        self.workers[service_type] = active_workers

        # Return least loaded worker
        return min(active_workers, key=lambda w: w.load_score)

    async def list_workers(self) -> dict[str, list[dict[str, Any]]]:
        """List all active workers by service type."""
        result = {}

        for service_type, workers in self.workers.items():
            active_workers = self._filter_active_workers(workers)

            if active_workers:
                # Update the stored list
                self.workers[service_type] = active_workers

                # Convert to JSON-serializable format
                result[service_type] = [
                    {
                        "worker_id": w.worker_id,
                        "endpoint": w.endpoint,
                        "capabilities": w.capabilities,
                        "last_seen": w.last_seen.isoformat(),
                        "load_score": w.load_score,
                    }
                    for w in active_workers
                ]
            else:
                # Clean up empty service types
                self.workers[service_type] = []

        return result

    async def get_workers(self) -> dict[str, list[WorkerInfo]]:
        """Get all registered workers grouped by service type (interface method)."""
        result = {}

        for service_type, workers in self.workers.items():
            active_workers = self._filter_active_workers(workers)

            if active_workers:
                # Update the stored list
                self.workers[service_type] = active_workers
                result[service_type] = active_workers
            else:
                # Clean up empty service types
                self.workers[service_type] = []

        return result

    def _filter_active_workers(self, workers: list[WorkerInfo]) -> list[WorkerInfo]:
        """Filter out workers that haven't been seen recently."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.worker_timeout)
        return [w for w in workers if w.last_seen > cutoff]

    async def _cleanup_expired_workers(self):
        """Background task to periodically clean up expired workers."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)

                expired_count = 0
                for service_type in list(self.workers.keys()):
                    before_count = len(self.workers[service_type])
                    self.workers[service_type] = self._filter_active_workers(
                        self.workers[service_type],
                    )
                    after_count = len(self.workers[service_type])
                    expired_count += before_count - after_count

                if expired_count > 0:
                    logger.info("🧹 Cleaned up {expired_count} expired workers")

            except asyncio.CancelledError:
                logger.info("🛑 Worker cleanup task cancelled")
                break
            except Exception:
                logger.exception("❌ Error in worker cleanup: {e}")
                # Continue running despite errors

    async def update_worker_load(self, worker_id: str, service_type: str, load_score: float):
        """Update worker load score for load balancing."""
        workers = self.workers.get(service_type, [])
        for worker in workers:
            if worker.worker_id == worker_id:
                worker.load_score = load_score
                worker.last_seen = datetime.now(timezone.utc)  # Update heartbeat
                logger.debug(f"📊 Updated load for {worker_id}: {load_score}")
                break

    async def heartbeat_worker(self, worker_id: str, service_type: str) -> bool:
        """Record a heartbeat from a worker."""
        workers = self.workers.get(service_type, [])
        for worker in workers:
            if worker.worker_id == worker_id:
                worker.last_seen = datetime.now(timezone.utc)
                logger.debug(f"💓 Heartbeat from {worker_id}")
                return True

        # Worker not found - might need to re-register
        logger.warning("💔 Heartbeat from unknown worker {worker_id} ({service_type})")
        return False

    async def cleanup(self):
        """Cleanup resources."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.cleanup_task

        logger.info("🧹 Cleaned up resilient discovery service")


# Factory function
async def create_discovery_service() -> DiscoveryServiceInterface:
    """Create and initialize the resilient discovery service."""

    # Check if we should use the old in-memory stub for testing
    if os.getenv("DISCOVERY_RESILIENT", "true").lower() == "false":
        logger.info("🧪 Using basic in-memory discovery service (testing mode)")
        from crank_platform_service import DiscoveryServiceStub

        return DiscoveryServiceStub()

    # Create resilient service
    service = ResilientDiscoveryService()
    await service.initialize()
    return service
