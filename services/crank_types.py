"""
Typed Application State Types for Crank Platform

Provides clean TypedDict-based app state typing with single cast location.
This replaces the Pydantic approach with a simpler, more direct pattern.
"""

from typing import TypedDict

from crank_platform_service import DiscoveryServiceInterface, PlatformService
from universal_protocol_service import UniversalProtocolService


class CrankAppState(TypedDict):
    """Typed application state for FastAPI app.state."""

    platform: PlatformService
    protocol_service: UniversalProtocolService
    discovery_service: DiscoveryServiceInterface
