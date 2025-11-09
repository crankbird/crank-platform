#!/usr/bin/env python3
"""
Worker Certificate Pattern Library
==================================

Standardized certificate initialization for Crank Platform workers.
Eliminates timing issues and ensures consistent security patterns.

Usage:
    from worker_cert_pattern import WorkerCertificatePattern

    def main():
        # Initialize certificates synchronously BEFORE FastAPI
        cert_pattern = WorkerCertificatePattern("crank-email-classifier")
        cert_store = cert_pattern.initialize_certificates()

        # Create FastAPI app with pre-loaded certificates
        app = create_worker_app(cert_store=cert_store)

        # Start server with certificates
        cert_pattern.start_server(app, port=8201)
"""

import asyncio
import logging
import os
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


class WorkerCertificatePattern:
    """Standardized certificate pattern for Crank Platform workers."""

    def __init__(self, service_name: str):
        """Initialize worker certificate pattern.

        Args:
            service_name: Name of the service (e.g., 'crank-email-classifier')
        """
        self.service_name = service_name
        self.https_only = os.getenv("HTTPS_ONLY", "true").lower() == "true"
        self.ca_service_url = os.getenv("CA_SERVICE_URL")

    def initialize_certificates(self):
        """Initialize certificates synchronously BEFORE FastAPI creation.

        Returns:
            cert_store: Pre-loaded certificate store for FastAPI

        Raises:
            RuntimeError: If certificate initialization fails
        """
        if not self.https_only or not self.ca_service_url:
            raise RuntimeError("🚫 Worker requires HTTPS_ONLY=true and CA_SERVICE_URL")

        print(f"🔐 Initializing certificates for {self.service_name} using SECURE CSR pattern...")

        try:
            # Import certificate initialization using package imports
            from crank_platform.security import cert_store, init_certificates

            # Set SERVICE_NAME for individual service certificates
            os.environ["SERVICE_NAME"] = self.service_name

            # Run secure certificate initialization SYNCHRONOUSLY
            asyncio.run(init_certificates())

            # Verify certificates were loaded
            if cert_store.platform_cert is None:
                raise RuntimeError(
                    "🚫 Certificate initialization completed but no certificates in memory",
                )

            print("✅ Certificates loaded successfully using SECURE CSR pattern")
            print("🔒 SECURITY: Private keys generated locally and never transmitted")

            return cert_store

        except Exception as e:
            raise RuntimeError(f"🚫 Certificate initialization failed for {self.service_name}: {e}") from e

    def start_server(self, app: "FastAPI", port: int, host: str = "0.0.0.0"):
        """Start uvicorn server with pre-loaded certificates.

        Args:
            app: FastAPI application
            port: HTTPS port to run on
            host: Host to bind to (default: 0.0.0.0)
        """
        import uvicorn

        print(f"🔒 Starting {self.service_name} with HTTPS/mTLS ONLY on port {port}")
        print("🔐 Using certificates from synchronous initialization")

        try:
            # Import certificate store using package imports
            from crank_platform.security import cert_store

            # Get certificate file paths for uvicorn
            cert_file = cert_store.temp_cert_file
            key_file = cert_store.temp_key_file

            print("🔒 Using certificates obtained via SECURE CSR pattern")

            uvicorn.run(
                app,
                host=host,
                port=port,
                ssl_keyfile=key_file,
                ssl_certfile=cert_file,
            )

        except Exception as e:
            raise RuntimeError(f"🚫 Failed to start {self.service_name} with certificates: {e}") from e


def create_worker_fastapi_with_certs(
    title: str,
    service_name: str,
    platform_url: Optional[str] = None,
    worker_url: Optional[str] = None,
    cert_store: Optional[object] = None,
):
    """Helper to create FastAPI worker with certificate store.

    Args:
        title: FastAPI title
        service_name: Service name for URLs
        platform_url: Platform URL (optional)
        worker_url: Worker URL (optional)
        cert_store: Pre-loaded certificate store

    Returns:
        dict with app and configuration
    """
    from fastapi import FastAPI

    app = FastAPI(title=title, version="1.0.0")

    config = {
        "app": app,
        "cert_store": cert_store,
        "platform_url": platform_url or os.getenv("PLATFORM_URL", "https://platform:8443"),
        "worker_url": worker_url or os.getenv("WORKER_URL", f"https://{service_name}:8201"),
        "service_name": service_name,
    }

    if cert_store is not None:
        logger.info("🔐 Using pre-loaded certificates from synchronous initialization")
    else:
        logger.warning("⚠️ No certificate store provided - worker may have certificate issues")

    return config


# Example usage pattern for workers:
"""
def main():
    # Step 1: Initialize certificates SYNCHRONOUSLY
    cert_pattern = WorkerCertificatePattern("crank-email-classifier")
    cert_store = cert_pattern.initialize_certificates()

    # Step 2: Create FastAPI with pre-loaded certificates
    worker_config = create_worker_fastapi_with_certs(
        title="Crank Email Classifier",
        service_name="crank-email-classifier",
        cert_store=cert_store
    )

    # Step 3: Setup your worker routes
    setup_worker_routes(worker_config["app"], worker_config)

    # Step 4: Start server with certificates
    cert_pattern.start_server(worker_config["app"], port=8201)
"""
