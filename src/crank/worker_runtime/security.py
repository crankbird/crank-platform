"""
Worker Security and Certificate Management

Handles:
- Certificate retrieval from controller
- mTLS configuration
- Security context management

Workers should NOT self-generate certificates. This module
provides the interface for workers to retrieve certificates
from the controller (the only privileged component).
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CertificateBundle:
    """
    Validated bundle of certificate files for mTLS.

    All paths are validated to exist on construction.
    Provides clean conversion to uvicorn SSL config.
    """

    cert_file: Path
    key_file: Path
    ca_file: Path
    worker_id: str

    def __post_init__(self) -> None:
        """Validate all certificate files exist."""
        missing = [
            str(path) for path in [self.cert_file, self.key_file, self.ca_file]
            if not path.exists()
        ]
        if missing:
            raise FileNotFoundError(
                f"Missing certificate files for worker '{self.worker_id}': "
                f"{', '.join(missing)}"
            )

    def to_uvicorn_config(self) -> dict[str, str]:
        """
        Convert bundle to uvicorn SSL configuration dict.

        Returns:
            Dictionary with ssl_certfile, ssl_keyfile, ssl_ca_certs keys
        """
        return {
            "ssl_certfile": str(self.cert_file),
            "ssl_keyfile": str(self.key_file),
            "ssl_ca_certs": str(self.ca_file),
        }

    def __repr__(self) -> str:
        """Human-readable representation."""
        return (
            f"CertificateBundle(worker_id='{self.worker_id}', "
            f"cert={self.cert_file.name}, key={self.key_file.name}, "
            f"ca={self.ca_file.name})"
        )


class CertificateManager:
    """
    Manages worker certificates for mTLS communication.

    Workers retrieve certificates from the controller rather than
    generating them directly. This maintains the security boundary
    where only the controller has CA privileges.
    """

    def __init__(
        self,
        worker_id: str,
        cert_dir: Optional[Path] = None,
    ) -> None:
        """
        Initialize certificate manager.

        Args:
            worker_id: Unique identifier for this worker
            cert_dir: Directory for certificate storage (defaults to ./certs)
        """
        self.worker_id = worker_id
        self.cert_dir = cert_dir or Path(os.getenv("CERT_DIR", "./certs"))
        self.cert_dir.mkdir(parents=True, exist_ok=True)

    def get_cert_path(self) -> Path:
        """Get path to worker certificate file."""
        return self.cert_dir / f"{self.worker_id}.crt"

    def get_key_path(self) -> Path:
        """Get path to worker private key file."""
        return self.cert_dir / f"{self.worker_id}.key"

    def get_ca_cert_path(self) -> Path:
        """Get path to CA certificate file."""
        return self.cert_dir / "ca.crt"

    def certificates_exist(self) -> bool:
        """
        Check if certificates are already present locally.

        Returns:
            True if all required certificates exist
        """
        return (
            self.get_cert_path().exists()
            and self.get_key_path().exists()
            and self.get_ca_cert_path().exists()
        )

    async def retrieve_certificates_from_controller(
        self,
        controller_url: str,
        auth_token: str,
    ) -> bool:
        """
        Retrieve certificates from the controller.

        This is a placeholder for the future certificate retrieval
        mechanism. Currently, workers rely on certificates being
        pre-provisioned in the certificate directory.

        Args:
            controller_url: Controller endpoint
            auth_token: Authentication token

        Returns:
            True if certificates were successfully retrieved

        TODO: Implement actual certificate retrieval via controller API
        """
        # Check if certificates already exist
        if self.certificates_exist():
            logger.info(f"✅ Certificates found for worker {self.worker_id}")
            return True

        # Future: Request certificates from controller
        # For now, we expect certificates to be pre-provisioned
        logger.warning(
            f"⚠️  Certificate retrieval not yet implemented. "
            f"Expected certificates in {self.cert_dir}"
        )
        return False

    def ensure_certificates(self) -> CertificateBundle:
        """
        Ensure certificates exist and return validated bundle.

        Returns:
            CertificateBundle with validated paths

        Raises:
            FileNotFoundError: If required certificates don't exist
        """
        return CertificateBundle(
            cert_file=self.get_cert_path(),
            key_file=self.get_key_path(),
            ca_file=self.get_ca_cert_path(),
            worker_id=self.worker_id,
        )

    def get_ssl_context(self) -> dict[str, str]:
        """
        Get SSL context configuration for HTTPS server.

        Deprecated: Use ensure_certificates().to_uvicorn_config() instead.

        Returns:
            Dictionary with cert file paths for SSL configuration

        Raises:
            FileNotFoundError: If required certificates don't exist
        """
        bundle = self.ensure_certificates()
        return bundle.to_uvicorn_config()


def load_certificates_sync(worker_id: str) -> dict[str, str]:
    """
    Synchronous helper to load certificates at worker startup.

    This is a convenience function for workers that need to load
    certificates during initialization (before async context is available).

    Args:
        worker_id: Unique identifier for this worker

    Returns:
        Dictionary with SSL configuration

    Raises:
        FileNotFoundError: If required certificates don't exist
    """
    cert_manager = CertificateManager(worker_id)

    if not cert_manager.certificates_exist():
        logger.error(
            f"❌ Certificates not found for worker {worker_id}. "
            f"Expected in: {cert_manager.cert_dir}"
        )
        raise FileNotFoundError(
            f"Worker certificates not found in {cert_manager.cert_dir}"
        )

    logger.info(f"🔒 Loaded certificates for worker {worker_id}")
    return cert_manager.get_ssl_context()
