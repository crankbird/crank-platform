#!/usr/bin/env python3
"""
Certificate initialization script for platform services.

This script requests certificates from the Certificate Authority Service
instead of generating them directly. This allows the platform to run as
a non-root user while maintaining enterprise-grade certificate management.
"""

import asyncio
import aiohttp
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
        
    async def wait_for_ca_service(self, timeout: int = 60) -> bool:
        """Wait for Certificate Authority Service to be available."""
        logger.info(f"⏳ Waiting for Certificate Authority Service at {self.ca_service_url}")
        
        for attempt in range(timeout):
            try:
                async with aiohttp.ClientSession() as session:
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
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.ca_service_url}/ca/certificate") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get CA certificate: {response.status}")
                
                data = await response.json()
                return data["ca_certificate"]
    
    async def provision_platform_certificates(self) -> Dict[str, Any]:
        """Request platform certificate bundle from CA service."""
        logger.info("🔐 Requesting platform certificate bundle")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.ca_service_url}/certificates/platform") as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to provision certificates: {response.status} - {error_text}")
                
                return await response.json()

def write_certificate_file(cert_path: Path, content: str, permissions: int = 0o644):
    """Write certificate content to file with appropriate permissions."""
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_text(content)
    cert_path.chmod(permissions)
    logger.info(f"📄 Written certificate: {cert_path} (permissions: {oct(permissions)})")

async def main():
    """Main certificate initialization routine."""
    # Get configuration from environment
    ca_service_url = os.getenv("CA_SERVICE_URL", "https://cert-authority:9090")
    cert_dir = Path(os.getenv("CERT_DIR", "/app/certificates"))
    environment = os.getenv("CRANK_ENVIRONMENT", "development")
    
    logger.info(f"🔐 Initializing certificates for environment: {environment}")
    logger.info(f"📁 Certificate directory: {cert_dir}")
    logger.info(f"🌐 CA Service URL: {ca_service_url}")
    
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
        write_certificate_file(cert_dir / "platform.key", platform_cert["private_key"], key_permissions)
        
        # Write client certificates
        client_cert = certificates["client"]
        write_certificate_file(cert_dir / "client.crt", client_cert["certificate"])
        write_certificate_file(cert_dir / "client.key", client_cert["private_key"], key_permissions)
        
        # Write certificate metadata
        metadata = {
            "platform": platform_cert["metadata"],
            "client": client_cert["metadata"], 
            "provider": cert_response["provider"],
            "environment": environment,
            "generated_at": platform_cert["metadata"]["issued_at"]
        }
        
        metadata_file = cert_dir / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))
        metadata_file.chmod(0o644)
        
        logger.info("✅ Certificate initialization complete")
        logger.info(f"🏢 Provider: {cert_response['provider']['provider']}")
        logger.info(f"🛡️ Security level: {cert_response['provider']['security_level']}")
        
    except Exception as e:
        logger.error(f"❌ Certificate initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())