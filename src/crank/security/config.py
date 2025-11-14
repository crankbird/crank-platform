"""
Security Configuration

Environment-aware security settings with strict HTTPS-only enforcement.
No HTTP capability exists - all communication uses mTLS.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .constants import (
    CA_CERT_FILENAME,
    CLIENT_CERT_FILENAME,
    CLIENT_KEY_FILENAME,
    DEFAULT_CERT_DIR,
    ENV_DEVELOPMENT,
    PLATFORM_CERT_FILENAME,
    PLATFORM_KEY_FILENAME,
)

logger = logging.getLogger(__name__)


@dataclass
class CertificatePaths:
    """Standard certificate file paths."""

    cert_dir: Path
    ca_cert: Path
    platform_cert: Path
    platform_key: Path
    client_cert: Path
    client_key: Path

    @classmethod
    def from_cert_dir(cls, cert_dir: Path) -> "CertificatePaths":
        """Create certificate paths from base directory."""
        return cls(
            cert_dir=cert_dir,
            ca_cert=cert_dir / CA_CERT_FILENAME,
            platform_cert=cert_dir / PLATFORM_CERT_FILENAME,
            platform_key=cert_dir / PLATFORM_KEY_FILENAME,
            client_cert=cert_dir / CLIENT_CERT_FILENAME,
            client_key=cert_dir / CLIENT_KEY_FILENAME,
        )

    def validate_exists(self, require_client_cert: bool = True) -> None:
        """
        Validate required certificates exist.

        Args:
            require_client_cert: Whether client cert is required

        Raises:
            FileNotFoundError: If required certificates don't exist
        """
        required = [self.ca_cert, self.platform_cert, self.platform_key]
        if require_client_cert:
            required.extend([self.client_cert, self.client_key])

        missing = [str(cert) for cert in required if not cert.exists()]
        if missing:
            raise FileNotFoundError(
                f"Required certificates missing: {', '.join(missing)}. "
                "Run certificate initialization first."
            )


class SecurityConfig:
    """
    Security configuration for zero-trust architecture.

    HTTPS-only enforcement - no HTTP capability exists.
    Development and production both use mTLS with certificate verification.
    Only difference: development uses self-signed certs from CA service.
    """

    def __init__(
        self,
        environment: Optional[str] = None,
        cert_dir: Optional[Path] = None,
    ):
        """
        Initialize security configuration.

        Args:
            environment: "development" or "production" (default: from env)
            cert_dir: Certificate directory (default: /etc/certs, or CERT_DIR env)
                     Development: Set CERT_DIR=./certs for user-writable location
        """
        self.environment = environment or os.getenv("CRANK_ENVIRONMENT", ENV_DEVELOPMENT)
        # Use DEFAULT_CERT_DIR (/etc/certs) for stable absolute path
        # Development can override with CERT_DIR=./certs for user-writable location
        self.cert_dir = cert_dir or Path(os.getenv("CERT_DIR", str(DEFAULT_CERT_DIR)))

        # Certificate paths
        self.paths = CertificatePaths.from_cert_dir(self.cert_dir)

        # Certificate filename mapping for dynamic access
        self.cert_filenames = {
            "ca": CA_CERT_FILENAME,
            "cert": PLATFORM_CERT_FILENAME,  # or CLIENT_CERT_FILENAME for workers
            "key": PLATFORM_KEY_FILENAME,  # or CLIENT_KEY_FILENAME for workers
            "client_cert": CLIENT_CERT_FILENAME,
            "client_key": CLIENT_KEY_FILENAME,
        }

        # Security policy - HTTPS/mTLS ONLY
        # No environment-based relaxation
        self.https_only = True
        self.require_mtls = True
        self.verify_certificates = True  # Always verify against our CA

        logger.info(
            "🔒 Security initialized: environment=%s, cert_dir=%s, HTTPS-only with mTLS",
            self.environment,
            self.cert_dir,
        )

    def get_ca_cert_path(self) -> Path:
        """Get CA certificate path for verification."""
        return self.paths.ca_cert

    def get_client_cert_tuple(self) -> tuple[str, str]:
        """
        Get client certificate tuple for mTLS.

        Returns:
            Tuple of (cert_path, key_path)

        Raises:
            FileNotFoundError: If client certificates don't exist
        """
        if not self.paths.client_cert.exists() or not self.paths.client_key.exists():
            raise FileNotFoundError(
                f"Client certificates not found in {self.cert_dir}. "
                "mTLS requires both client.crt and client.key."
            )
        return (str(self.paths.client_cert), str(self.paths.client_key))

    def get_server_cert_tuple(self) -> tuple[str, str]:
        """
        Get server certificate tuple for HTTPS server.

        Returns:
            Tuple of (cert_path, key_path)

        Raises:
            FileNotFoundError: If server certificates don't exist
        """
        if not self.paths.platform_cert.exists() or not self.paths.platform_key.exists():
            raise FileNotFoundError(
                f"Server certificates not found in {self.cert_dir}. "
                "HTTPS server requires both platform.crt and platform.key."
            )
        return (str(self.paths.platform_cert), str(self.paths.platform_key))


# Global singleton config
_security_config: Optional[SecurityConfig] = None


def get_security_config(
    environment: Optional[str] = None,
    cert_dir: Optional[Path] = None,
) -> SecurityConfig:
    """
    Get global security configuration (singleton pattern).

    Args:
        environment: Override environment (default: from env var)
        cert_dir: Override cert directory (default: from env var)

    Returns:
        Singleton SecurityConfig instance
    """
    global _security_config
    if _security_config is None:
        _security_config = SecurityConfig(environment=environment, cert_dir=cert_dir)
    return _security_config


def reset_security_config() -> None:
    """Reset global security config (useful for testing)."""
    global _security_config
    _security_config = None
