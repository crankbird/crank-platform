"""
Crank Platform Capability Schema

This module defines the capability schema system that serves as the source of truth
for worker capabilities, routing decisions, and contract validation.

Design Principles:
- Capabilities are versioned contracts between workers and controllers
- Schema validation ensures type safety and compatibility
- Workers declare capabilities, controllers validate and route
"""

from .schema import (
    CSR_SIGNING,
    DOCUMENT_CONVERSION,
    EMAIL_CLASSIFICATION,
    EMAIL_PARSING,
    IMAGE_CLASSIFICATION,
    STREAMING_CLASSIFICATION,
    CapabilityDefinition,
    CapabilityVersion,
    ErrorCode,
    IOContract,
)

__all__ = [
    "CSR_SIGNING",
    "DOCUMENT_CONVERSION",
    "EMAIL_CLASSIFICATION",
    "EMAIL_PARSING",
    "IMAGE_CLASSIFICATION",
    "STREAMING_CLASSIFICATION",
    "CapabilityDefinition",
    "CapabilityVersion",
    "ErrorCode",
    "IOContract",
]
