"""
Security Constants

Centralized security-related constants for the Crank Platform.
All services use HTTPS with mTLS - no HTTP capability exists.
"""

from pathlib import Path

# Certificate Directories
DEFAULT_CERT_DIR = Path("/etc/certs")
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
