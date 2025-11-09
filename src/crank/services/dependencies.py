from __future__ import annotations

from typing import cast

from fastapi import Request

from services.crank_platform_service import DiscoveryServiceInterface, PlatformService
from services.universal_protocol_service import UniversalProtocolService


def get_platform_service(request: Request) -> PlatformService:
    svc = getattr(request.app.state, "platform", None)
    if svc is None:
        raise RuntimeError("PlatformService not initialized")
    return cast(PlatformService, svc)


def get_protocol_service(request: Request) -> UniversalProtocolService:
    svc = getattr(request.app.state, "protocol_service", None)
    if svc is None:
        raise RuntimeError("UniversalProtocolService not initialized")
    return cast(UniversalProtocolService, svc)


def get_discovery_service(request: Request) -> DiscoveryServiceInterface:
    svc = getattr(request.app.state, "discovery_service", None)
    if svc is None:
        raise RuntimeError("DiscoveryServiceInterface not initialized")
    return cast(DiscoveryServiceInterface, svc)
