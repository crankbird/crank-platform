"""
Security Constants

Centralized security-related constants for the Crank Platform.
All services use HTTPS with mTLS - no HTTP capability exists.
"""

import os
from pathlib import Path


def _running_in_container() -> bool:
    """Return True if common container markers are present."""
    return (
        os.path.exists("/.dockerenv")
        or os.path.exists("/run/.containerenv")
        or os.getenv("KUBERNETES_SERVICE_HOST") is not None
    )


def get_default_cert_dir() -> Path:
    """
    Determine the default certificate directory.

    Priority order:
    1. CERT_DIR environment variable (explicit override)
    2. /etc/certs if it exists and is writable (standard production mounts)
    3. /etc/certs if running in a container (fail fast if mounts are missing)
    4. ~/.crank/certs (stable, user-writable development default)
    """
    env_override = os.getenv("CERT_DIR")
    if env_override:
        return Path(env_override).expanduser()

    etc_certs = Path("/etc/certs")
    if etc_certs.exists() and os.access(etc_certs, os.W_OK):
        return etc_certs

    if _running_in_container():
        # In containers we expect /etc/certs to be mounted; keep pointing there so
        # a missing volume produces a clear, actionable error.
        return etc_certs

    return Path.home() / ".crank" / "certs"


# Certificate Directories
DEFAULT_CERT_DIR = get_default_cert_dir()
SHARED_CA_CERT_DIR = Path("/shared/ca-certs")

# Certificate Filenames
CA_CERT_FILENAME = "ca.crt"
CA_KEY_FILENAME = "ca.key"
PLATFORM_CERT_FILENAME = "platform.crt"
PLATFORM_KEY_FILENAME = "platform.key"
CLIENT_CERT_FILENAME = "client.crt"
CLIENT_KEY_FILENAME = "client.key"

# Security Defaults
DEFAULT_CA_SERVICE_URL = "https://cert-authority:9090"
DEFAULT_CA_SERVICE_TIMEOUT = 60  # seconds
DEFAULT_HTTP_CLIENT_TIMEOUT = 30  # seconds

# Certificate Settings
CERTIFICATE_VALIDITY_DAYS = 365
RSA_KEY_SIZE = 4096

# Certificate Renewal Windows (for observability)
CERT_RENEWAL_WARNING_DAYS = 30  # Emit EXPIRING_SOON event
CERT_RENEWAL_CRITICAL_DAYS = 7  # Attempt automatic renewal
CERT_EXPIRATION_CHECK_INTERVAL = 3600  # Check hourly (seconds)

# HTTP Client Limits
MAX_KEEPALIVE_CONNECTIONS = 10
MAX_CONNECTIONS = 20
KEEPALIVE_EXPIRY = 30  # seconds

# Environment Names
ENV_DEVELOPMENT = "development"
ENV_PRODUCTION = "production"

# Security Policy - HTTPS Only
# Development uses self-signed certificates from CA service
# Production uses enterprise certificates
# NO HTTP FALLBACK EXISTS IN ANY ENVIRONMENT
HTTPS_ONLY = True
REQUIRE_MTLS = True
VERIFY_CERTIFICATES = True  # Always verify against our CA cert
