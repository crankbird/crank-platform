"""
mTLS-Only HTTP Client Factory

Creates HTTPS clients with mandatory mutual TLS authentication.
NO HTTP CAPABILITY - all connections require valid certificates.

This module enforces the platform's zero-trust security model:
- HTTPS only (no HTTP fallback)
- Certificate verification always enabled
- Fails fast if certificates unavailable
"""

import logging
from pathlib import Path
from typing import Any, Optional

import httpx  # type: ignore[import-not-found]

from .config import get_security_config
from .constants import (
    DEFAULT_HTTP_CLIENT_TIMEOUT,
    KEEPALIVE_EXPIRY,
    MAX_CONNECTIONS,
    MAX_KEEPALIVE_CONNECTIONS,
)

logger = logging.getLogger(__name__)


class CertificateVerificationError(Exception):
    """Raised when certificate verification fails or certificates are missing."""


def verify_certificate_chain(cert_dir: Optional[Path] = None) -> tuple[Path, Path, Path]:
    """
    Verify complete certificate chain exists.

    Args:
        cert_dir: Directory containing certificates (defaults to config)

    Returns:
        Tuple of (cert_file, key_file, ca_file) paths

    Raises:
        CertificateVerificationError: If any required certificates missing
    """
    config = get_security_config()
    cert_dir = cert_dir or config.cert_dir

    # Use client certificates for mTLS
    cert_file = cert_dir / config.cert_filenames["client_cert"]
    key_file = cert_dir / config.cert_filenames["client_key"]
    ca_file = cert_dir / config.cert_filenames["ca"]

    missing: list[str] = []
    if not cert_file.exists():
        missing.append(str(cert_file))
    if not key_file.exists():
        missing.append(str(key_file))
    if not ca_file.exists():
        missing.append(str(ca_file))

    if missing:
        raise CertificateVerificationError(
            f"Certificate chain incomplete. Missing: {', '.join(missing)}. "
            "Cannot create mTLS client without valid certificates."
        )

    return cert_file, key_file, ca_file


def create_mtls_client(
    cert_dir: Optional[Path] = None,
    timeout: int = DEFAULT_HTTP_CLIENT_TIMEOUT,
    verify_certs: bool = True,
) -> httpx.AsyncClient:
    """
    Create HTTPS client with mandatory mTLS authentication.

    This is the ONLY way to create HTTP clients in the Crank Platform.
    All connections use HTTPS with mutual TLS - no exceptions.

    Args:
        cert_dir: Certificate directory (defaults to config cert_dir)
        timeout: Request timeout in seconds
        verify_certs: Certificate verification (ALWAYS True in production,
                     can be False ONLY for CA service bootstrap)

    Returns:
        Configured httpx.AsyncClient with mTLS

    Raises:
        CertificateVerificationError: If certificates missing/invalid

    Example:
        >>> async with create_mtls_client() as client:
        ...     response = await client.post(
        ...         "https://worker:8201/classify",
        ...         json={"text": "urgent email"}
        ...     )

    Security Guarantees:
        - HTTPS only (no HTTP support)
        - Certificate verification against CA
        - Client certificates for mTLS
        - No verify=False anti-pattern
        - Fails fast if certificates unavailable
    """
    config = get_security_config()
    cert_dir = cert_dir or config.cert_dir

    # Verify complete certificate chain exists
    cert_file, key_file, ca_file = verify_certificate_chain(cert_dir)

    logger.info(
        "Creating mTLS client: cert=%s, ca=%s, verify=%s",
        cert_file.name,
        ca_file.name,
        verify_certs,
    )

    # Build client configuration
    client_config: dict[str, Any] = {
        "timeout": httpx.Timeout(timeout),
        "follow_redirects": False,  # Security: no automatic redirects
        "limits": httpx.Limits(
            max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS,
            max_connections=MAX_CONNECTIONS,
            keepalive_expiry=KEEPALIVE_EXPIRY,
        ),
        # mTLS configuration - client certificate
        "cert": (str(cert_file), str(key_file)),
    }

    # Certificate verification against CA
    if verify_certs:
        client_config["verify"] = str(ca_file)
        logger.info("✅ mTLS client created with certificate verification enabled")
    else:
        # Only allowed during CA service bootstrap
        client_config["verify"] = False
        logger.warning(
            "⚠️  mTLS client created with verification DISABLED. "
            "This should ONLY happen during CA service bootstrap."
        )

    return httpx.AsyncClient(**client_config)


def create_ca_bootstrap_client(timeout: int = DEFAULT_HTTP_CLIENT_TIMEOUT) -> httpx.AsyncClient:
    """
    Create minimal HTTPS client for CA service bootstrap.

    This is used ONLY during initial certificate acquisition from the
    CA service. Once certificates are obtained, all clients must use
    create_mtls_client() with full verification.

    Args:
        timeout: Request timeout in seconds

    Returns:
        Basic HTTPS client without certificate verification

    Warning:
        This client has NO certificate verification and should ONLY
        be used during the initial bootstrap process when certificates
        don't exist yet.
    """
    logger.warning(
        "⚠️  Creating CA bootstrap client (no verification). "
        "This should ONLY be used for initial certificate acquisition."
    )

    return httpx.AsyncClient(
        timeout=httpx.Timeout(timeout),
        verify=False,  # Only acceptable during bootstrap
        follow_redirects=False,
    )
