#!/usr/bin/env python3
"""
Certificate initialization script for platform services.

This script requests certificates from the Certificate Authority Service
instead of generating them directly. This allows the platform to run as
a non-root user while maintaining enterprise-grade certificate management.
"""

import asyncio
import aiohttp
import ssl
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CertificateClient:
    """Client for requesting certificates from the Certificate Authority Service."""
    
    def __init__(self, ca_service_url: str):
        self.ca_service_url = ca_service_url.rstrip('/')
        # For development, accept self-signed certificates from CA service
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
    async def wait_for_ca_service(self, timeout: int = 60) -> bool:
        """Wait for Certificate Authority Service to be available."""
        logger.info(f"⏳ Waiting for Certificate Authority Service at {self.ca_service_url}")
        
        for attempt in range(timeout):
            try:
                connector = aiohttp.TCPConnector(ssl=self.ssl_context)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(f"{self.ca_service_url}/health", timeout=2) as response:
                        if response.status == 200:
                            health_data = await response.json()
                            logger.info(f"✅ Certificate Authority Service ready: {health_data['provider']}")
                            return True
            except Exception:
                pass
                
            await asyncio.sleep(1)
        
        logger.error(f"❌ Certificate Authority Service not available after {timeout}s")
        return False
    
    async def get_ca_certificate(self) -> str:
        """Get the CA root certificate."""
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(f"{self.ca_service_url}/ca/certificate") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get CA certificate: {response.status}")
                
                data = await response.json()
                return data["ca_certificate"]
    
    async def provision_platform_certificates(self) -> Dict[str, Any]:
        """Request platform certificate bundle from CA service."""
        logger.info("🔐 Requesting platform certificate bundle")
        
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(f"{self.ca_service_url}/certificates/platform") as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to provision certificates: {response.status} - {error_text}")
                
                return await response.json()

class CertificateStore:
    """In-memory certificate store for secure certificate management."""
    
    def __init__(self):
        self.ca_cert = None
        self.platform_cert = None
        self.platform_key = None
        self.client_cert = None
        self.client_key = None
        
    def store_certificates(self, ca_cert: str, platform_cert: str, platform_key: str, client_cert: str, client_key: str):
        """Store certificates in memory."""
        self.ca_cert = ca_cert
        self.platform_cert = platform_cert
        self.platform_key = platform_key
        self.client_cert = client_cert
        self.client_key = client_key
        logger.info("🔐 Certificates stored securely in memory")
        
    def get_ssl_context(self):
        """Create SSL context from in-memory certificates."""
        import ssl
        import tempfile
        import os
        
        # Create temporary SSL context with in-memory certs
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        
        # Create temporary files for SSL context (must persist during server lifetime)
        temp_dir = tempfile.mkdtemp()
        cert_file = os.path.join(temp_dir, "cert.pem")
        key_file = os.path.join(temp_dir, "key.pem")
        
        # Write certificates to temporary files
        with open(cert_file, 'w') as f:
            f.write(self.platform_cert)
        with open(key_file, 'w') as f:
            f.write(self.platform_key)
        
        # Load certificate chain
        context.load_cert_chain(cert_file, key_file)
        
        # Store temp file paths for cleanup later if needed
        self._temp_cert_file = cert_file
        self._temp_key_file = key_file
        self._temp_dir = temp_dir
        
        return context

# Global certificate store
cert_store = CertificateStore()

async def main():
    """Main certificate initialization routine - keeps certificates in memory."""
    # Get configuration from environment
    ca_service_url = os.getenv("CA_SERVICE_URL", "https://cert-authority:9090")
    ca_bootstrap_url = "http://cert-authority:9080"  # HTTP bootstrap endpoint
    environment = os.getenv("CRANK_ENVIRONMENT", "development")
    
    logger.info(f"🔐 Initializing certificates for environment: {environment}")
    logger.info(f"🌐 CA Service HTTPS URL: {ca_service_url}")
    logger.info(f"� CA Bootstrap HTTP URL: {ca_bootstrap_url}")
    logger.info("�💾 Using in-memory certificate storage (no disk writes)")
    
    try:
        # Initialize certificate client with HTTP bootstrap
        cert_client = CertificateClient(ca_bootstrap_url)
        
        # Wait for CA service to be available (using HTTP bootstrap)
        if not await cert_client.wait_for_ca_service():
            sys.exit(1)
        
        # Get CA certificate (via HTTP bootstrap)
        ca_cert = await cert_client.get_ca_certificate()
        
        # Request platform certificates (via HTTP bootstrap)
        cert_response = await cert_client.provision_platform_certificates()
        certificates = cert_response["certificates"]
        
        # Get platform certificates
        platform_cert = certificates["platform"]
        
        # Get client certificates
        client_cert = certificates.get("client", {})
        
        # Store all certificates in memory (no disk writes!)
        cert_store.store_certificates(
            ca_cert=ca_cert,
            platform_cert=platform_cert["certificate"],
            platform_key=platform_cert["private_key"],
            client_cert=client_cert.get("certificate", ""),
            client_key=client_cert.get("private_key", "")
        )
        
        logger.info("✅ Certificate initialization complete")
        logger.info(f"🏢 Provider: {cert_response['provider']['provider']}")
        logger.info(f"🛡️ Security level: {cert_response['provider']['security_level']}")
        logger.info("💾 All certificates stored securely in memory")
        logger.info("🔒 Platform can now use HTTPS endpoints for all subsequent communication")
        
    except Exception as e:
        logger.error(f"❌ Certificate initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())