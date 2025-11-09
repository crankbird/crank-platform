"""
FastAPI Dependency Injection for Crank Platform Services

Provides type-safe dependency injection with runtime checks and type narrowing.
This resolves FastAPI lifespan typing issues with explicit validation.
"""

from crank_platform_service import DiscoveryServiceInterface, PlatformService
from fastapi import Request
from universal_protocol_service import UniversalProtocolService


def get_platform_service(request: Request) -> PlatformService:
    """Get the initialized platform service with runtime validation."""
    svc = getattr(request.app.state, "platform", None)
    if svc is None:
        raise RuntimeError("PlatformService not initialized")
    assert isinstance(svc, PlatformService)  # satisfies mypy/pyright
    return svc


def get_protocol_service(request: Request) -> UniversalProtocolService:
    """Get the initialized universal protocol service with runtime validation."""
    svc = getattr(request.app.state, "protocol_service", None)
    if svc is None:
        raise RuntimeError("UniversalProtocolService not initialized")
    assert isinstance(svc, UniversalProtocolService)  # satisfies mypy/pyright
    return svc


def get_discovery_service(request: Request) -> DiscoveryServiceInterface:
    """Get the initialized discovery service with runtime validation."""
    svc = getattr(request.app.state, "discovery_service", None)
    if svc is None:
        raise RuntimeError("DiscoveryServiceInterface not initialized")
    assert isinstance(svc, DiscoveryServiceInterface)  # satisfies mypy/pyright
    return svc
