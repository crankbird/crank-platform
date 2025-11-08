#!/usr/bin/env python3
"""
Certificate initialization script for platform services.

This script requests certificates from the Certificate Authority Service
instead of generating them directly. This allows the platform to run as
a non-root user while maintaining enterprise-grade certificate management.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import aiohttp
from aiohttp import ClientTimeout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CertificateClient:
    """Client for requesting certificates from the Certificate Authority Service."""

    def __init__(self, ca_service_url: str):
        self.ca_service_url = ca_service_url.rstrip("/")

    async def wait_for_ca_service(self, timeout: int = 60) -> bool:
        """Wait for Certificate Authority Service to be available."""
        logger.info(
            "⏳ Waiting for Certificate Authority Service at %s",
            self.ca_service_url,
        )

        for _attempt in range(timeout):
            try:
                timeout_config = ClientTimeout(total=2)
                async with aiohttp.ClientSession(timeout=timeout_config) as session, session.get(f"{self.ca_service_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        logger.info(
                            "✅ Certificate Authority Service ready: %s",
                            health_data["provider"],
                        )
                        return True
            except Exception as exc:
                logger.debug("Health check failed: %s", exc)

            await asyncio.sleep(1)

        logger.error(
            "❌ Certificate Authority Service not available after %ss",
            timeout,
        )
        return False

    async def get_ca_certificate(self) -> str:
        """Get the CA root certificate."""
        async with aiohttp.ClientSession() as session, session.get(f"{self.ca_service_url}/ca/certificate") as response:
            if response.status != 200:
                raise RuntimeError(f"Failed to get CA certificate: {response.status}")

            data: dict[str, Any] = await response.json()
            ca_certificate: str = data["ca_certificate"]
            return ca_certificate

    async def provision_platform_certificates(self) -> dict[str, Any]:
        """Request platform certificate bundle from CA service."""
        logger.info("🔐 Requesting platform certificate bundle")

        async with aiohttp.ClientSession() as session, session.post(f"{self.ca_service_url}/certificates/platform") as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(
                    f"Failed to provision certificates: {response.status} - {error_text}",
                )

            result: dict[str, Any] = await response.json()
            return result


def write_certificate_file(cert_path: Path, content: str, permissions: int = 0o644) -> None:
    """Write certificate content to file with appropriate permissions."""
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_text(content)
    cert_path.chmod(permissions)
    logger.info(
        "📄 Written certificate: %s (permissions: %s)",
        cert_path,
        oct(permissions),
    )


async def main() -> None:
    """Main certificate initialization routine."""
    # Get configuration from environment
    ca_service_url = os.getenv("CA_SERVICE_URL", "https://cert-authority:9090")
    cert_dir = Path(os.getenv("CERT_DIR", "/app/certificates"))
    environment = os.getenv("CRANK_ENVIRONMENT", "development")

    logger.info("🔐 Initializing certificates for environment: %s", environment)
    logger.info("📁 Certificate directory: %s", cert_dir)
    logger.info("🌐 CA Service URL: %s", ca_service_url)

    try:
        # Initialize certificate client
        cert_client = CertificateClient(ca_service_url)

        # Wait for CA service to be available
        if not await cert_client.wait_for_ca_service():
            sys.exit(1)

        # Get CA certificate
        ca_cert = await cert_client.get_ca_certificate()
        write_certificate_file(cert_dir / "ca.crt", ca_cert)

        # Request platform certificates
        cert_response = await cert_client.provision_platform_certificates()
        certificates = cert_response["certificates"]

        # Write platform certificates
        platform_cert = certificates["platform"]
        write_certificate_file(cert_dir / "platform.crt", platform_cert["certificate"])

        # Set permissions based on environment
        key_permissions = 0o600 if environment == "production" else 0o644
        write_certificate_file(
            cert_dir / "platform.key", platform_cert["private_key"], key_permissions,
        )

        # Write client certificates
        client_cert = certificates["client"]
        write_certificate_file(cert_dir / "client.crt", client_cert["certificate"])
        write_certificate_file(cert_dir / "client.key", client_cert["private_key"], key_permissions)

        # Write certificate metadata
        metadata: dict[str, Any] = {
            "platform": platform_cert["metadata"],
            "client": client_cert["metadata"],
            "provider": cert_response["provider"],
            "environment": environment,
            "generated_at": platform_cert["metadata"]["issued_at"],
        }

        metadata_file = cert_dir / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))
        metadata_file.chmod(0o644)

        logger.info("✅ Certificate initialization complete")
        logger.info(
            "🏢 Provider: %s",
            cert_response["provider"]["provider"],
        )
        logger.info(
            "🛡️ Security level: %s",
            cert_response["provider"]["security_level"],
        )

    except Exception:
        logger.exception("❌ Certificate initialization failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
