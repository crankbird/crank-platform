"""
Worker Runtime Package

Shared runtime infrastructure for all Crank workers. Provides:
- WorkerApplication base class with lifecycle management
- Controller registration and heartbeat logic
- Health check and graceful shutdown
- Certificate management (retrieval from controller)

This eliminates code duplication across workers and enforces
consistent behavior per the controller/worker/capability architecture.

Usage:
    from crank.worker_runtime import WorkerApplication
    from crank.capabilities.schema import STREAMING_CLASSIFICATION

    class StreamingWorker(WorkerApplication):
        def get_capabilities(self):
            return [STREAMING_CLASSIFICATION]

        async def handle_request(self, request_data):
            # Business logic here
            return result
"""

from crank.worker_runtime.base import WorkerApplication
from crank.worker_runtime.lifecycle import HealthStatus, ShutdownHandler, ShutdownTask
from crank.worker_runtime.registration import (
    ControllerClient,
    WorkerRegistration,
)
from crank.worker_runtime.security import CertificateBundle, CertificateManager

__all__: list[str] = [
    "CertificateBundle",
    "CertificateManager",
    "ControllerClient",
    "HealthStatus",
    "ShutdownHandler",
    "ShutdownTask",
    "WorkerApplication",
    "WorkerRegistration",
]
