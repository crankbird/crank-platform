"""Controller package - privileged routing and registry logic."""

from .capability_registry import CapabilityRegistry, WorkerEndpoint

__all__ = ["CapabilityRegistry", "WorkerEndpoint"]
