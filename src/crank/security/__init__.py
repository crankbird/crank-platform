"""
Crank Security Module

Unified security and certificate management for the Crank Platform.
All service-to-service communication uses HTTPS with mutual TLS (mTLS).

Quick Start - Workers:
    >>> from crank.security import initialize_worker_certificates, create_mtls_client
    >>>
    >>> # Bootstrap certificates from CA service
    >>> cert, key, ca = await initialize_worker_certificates("streaming-worker-1")
    >>>
    >>> # Create mTLS HTTP client
    >>> async with create_mtls_client() as client:
    ...     response = await client.post("https://platform:8443/api/...")

Note:
    Controller CA operations (CertificateAuthorityManager) will be added
    during Phase 3 controller extraction (Issue #30).

Security Guarantees:
    - HTTPS-only (no HTTP capability exists)
    - Mutual TLS (mTLS) for all service communication
    - Certificate verification always enabled
    - Private keys never transmitted over network
    - CSR-based certificate provisioning
    - Observability hooks for all certificate lifecycle events
"""

from .certificates import CertificateBundle, CertificateManager
from .config import CertificatePaths, SecurityConfig, get_security_config, reset_security_config
from .constants import (
    CA_CERT_FILENAME,
    CLIENT_CERT_FILENAME,
    CLIENT_KEY_FILENAME,
    DEFAULT_CA_SERVICE_URL,
    DEFAULT_CERT_DIR,
    PLATFORM_CERT_FILENAME,
    PLATFORM_KEY_FILENAME,
)
from .events import (
    CertificateEvent,
    CertificateEventContext,
    emit_certificate_event,
    record_ca_unavailable,
    record_cert_expiration,
    record_cert_issuance,
    register_event_handler,
)
from .initialization import (
    CertificateInitializationError,
    generate_csr,
    get_ca_certificate,
    initialize_certificates_from_env,
    initialize_worker_certificates,
    submit_csr,
    wait_for_ca_service,
)
from .mtls_client import (
    CertificateVerificationError,
    create_ca_bootstrap_client,
    create_mtls_client,
    verify_certificate_chain,
)

__all__ = [
    "CA_CERT_FILENAME",
    "CLIENT_CERT_FILENAME",
    "CLIENT_KEY_FILENAME",
    "DEFAULT_CA_SERVICE_URL",
    "DEFAULT_CERT_DIR",
    "PLATFORM_CERT_FILENAME",
    "PLATFORM_KEY_FILENAME",
    "CertificateBundle",
    "CertificateEvent",
    "CertificateEventContext",
    "CertificateInitializationError",
    "CertificateManager",
    "CertificatePaths",
    "CertificateVerificationError",
    "SecurityConfig",
    "create_ca_bootstrap_client",
    "create_mtls_client",
    "emit_certificate_event",
    "generate_csr",
    "get_ca_certificate",
    "get_security_config",
    "initialize_certificates_from_env",
    "initialize_worker_certificates",
    "record_ca_unavailable",
    "record_cert_expiration",
    "record_cert_issuance",
    "register_event_handler",
    "reset_security_config",
    "submit_csr",
    "verify_certificate_chain",
    "wait_for_ca_service",
]

__version__ = "0.1.0"
__author__ = "Crank Platform Team"
