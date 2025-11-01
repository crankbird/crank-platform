"""
Certificate Authority Service API
=================================

RESTful API for certificate provisioning that can be swapped between providers:
- Development: Self-signed certificates
- Enterprise: HashiCorp Vault, Active Directory
- Cloud: Azure Key Vault, AWS Certificate Manager, Google CA

This service runs as a separate container to isolate certificate operations
and enable easy replacement with external certificate authorities.
"""

import asyncio
import logging
import os
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from certificate_authority_service import (
    CertificateAuthorityService, 
    CertificateRequest,
    create_certificate_provider
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Certificate Authority Service",
    description="Pluggable certificate provisioning service for Crank Platform",
    version="1.0.0"
)

# Global certificate service instance
cert_service: CertificateAuthorityService = None

@app.on_event("startup")
async def startup_event():
    """Initialize certificate authority service on startup."""
    global cert_service
    
    logger.info("🔐 Starting Certificate Authority Service")
    
    try:
        # Create certificate provider based on environment
        provider = create_certificate_provider()
        cert_service = CertificateAuthorityService(provider)
        
        # Log provider information
        provider_info = cert_service.get_provider_status()
        logger.info(f"✅ Certificate provider initialized: {provider_info['provider_info']['provider']}")
        logger.info(f"🛡️ Security level: {provider_info['provider_info']['security_level']}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize certificate service: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "certificate-authority",
        "provider": cert_service.get_provider_status()["provider_info"]["provider"] if cert_service else "not-initialized"
    }

@app.get("/ca/certificate")
async def get_ca_certificate():
    """Get the Certificate Authority root certificate."""
    try:
        ca_cert = await cert_service.provider.get_ca_certificate()
        return {
            "ca_certificate": ca_cert,
            "provider": cert_service.provider.get_provider_info()["provider"]
        }
    except Exception as e:
        logger.error(f"Failed to get CA certificate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/certificates/platform")
async def provision_platform_certificates():
    """Provision complete certificate bundle for the platform."""
    try:
        logger.info("🔐 Provisioning platform certificate bundle")
        
        certificates = await cert_service.request_platform_certificates()
        
        return {
            "status": "success",
            "certificates": {
                "platform": {
                    "certificate": certificates["platform"].certificate,
                    "private_key": certificates["platform"].private_key,
                    "metadata": certificates["platform"].metadata
                },
                "client": {
                    "certificate": certificates["client"].certificate,
                    "private_key": certificates["client"].private_key,
                    "metadata": certificates["client"].metadata
                },
                "ca_certificate": certificates["ca"]
            },
            "provider": cert_service.provider.get_provider_info()
        }
        
    except Exception as e:
        logger.error(f"Failed to provision platform certificates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/certificates/csr")
async def sign_certificate_request(request: dict):
    """Sign a Certificate Signing Request (CSR) - SECURE PKI PATTERN."""
    try:
        csr_pem = request.get("csr")
        service_name = request.get("service_name", "platform")
        
        if not csr_pem:
            raise HTTPException(status_code=400, detail="CSR is required")
        
        logger.info(f"🔐 Processing CSR for service: {service_name}")
        
        # Validate and sign the CSR
        signed_cert = await cert_service.sign_certificate_request(csr_pem, service_name)
        
        return {
            "status": "success",
            "certificate": signed_cert,
            "ca_certificate": await cert_service.provider.get_ca_certificate(),
            "provider": cert_service.provider.get_provider_info()
        }
        
    except Exception as e:
        logger.error(f"Failed to sign CSR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/certificates/server")
async def provision_server_certificate(request: CertificateRequest):
    """Provision a server certificate."""
    try:
        logger.info(f"🔐 Provisioning server certificate for {request.common_name}")
        
        certificate = await cert_service.provider.provision_server_certificate(request)
        
        return {
            "status": "success",
            "certificate": certificate.certificate,
            "private_key": certificate.private_key,
            "certificate_chain": certificate.certificate_chain,
            "metadata": certificate.metadata
        }
        
    except Exception as e:
        logger.error(f"Failed to provision server certificate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/certificates/client")
async def provision_client_certificate(request: CertificateRequest):
    """Provision a client certificate."""
    try:
        logger.info(f"🔐 Provisioning client certificate for {request.common_name}")
        
        certificate = await cert_service.provider.provision_client_certificate(request)
        
        return {
            "status": "success", 
            "certificate": certificate.certificate,
            "private_key": certificate.private_key,
            "certificate_chain": certificate.certificate_chain,
            "metadata": certificate.metadata
        }
        
    except Exception as e:
        logger.error(f"Failed to provision client certificate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/certificates/{serial_number}")
async def revoke_certificate(serial_number: str):
    """Revoke a certificate by serial number."""
    try:
        logger.info(f"🚫 Revoking certificate with serial: {serial_number}")
        
        success = await cert_service.provider.revoke_certificate(serial_number)
        
        return {
            "status": "success" if success else "failed",
            "serial_number": serial_number,
            "revoked": success
        }
        
    except Exception as e:
        logger.error(f"Failed to revoke certificate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/provider/status")
async def get_provider_status():
    """Get certificate provider status and capabilities."""
    return cert_service.get_provider_status()

@app.get("/provider/config")  
async def get_provider_config():
    """Get certificate provider configuration (sanitized)."""
    provider_info = cert_service.provider.get_provider_info()
    
    # Remove sensitive information from response
    sanitized_info = {k: v for k, v in provider_info.items() 
                     if not any(sensitive in k.lower() 
                               for sensitive in ['secret', 'token', 'password', 'key'])}
    
    return {
        "provider_config": sanitized_info,
        "environment": os.getenv("CRANK_ENVIRONMENT", "development"),
        "cert_provider": os.getenv("CERT_PROVIDER", "development")
    }

if __name__ == "__main__":
    import uvicorn
    
    # Bootstrap Certificate Authority Service certificates
    cert_dir = Path(os.getenv("CERT_DIR", "/app/certificates"))
    cert_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate self-signed certificates for CA service if they don't exist
    ca_cert_path = cert_dir / "ca-service.crt"
    ca_key_path = cert_dir / "ca-service.key"
    
    if not ca_cert_path.exists() or not ca_key_path.exists():
        logger.info("🔧 Bootstrapping Certificate Authority Service certificates...")
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:4096",
            "-keyout", str(ca_key_path),
            "-out", str(ca_cert_path),
            "-days", "365", "-nodes",
            "-subj", "/CN=cert-authority/O=Crank Platform CA/OU=Certificate Authority"
        ], check=True)
        logger.info("✅ Certificate Authority Service certificates generated")
    
    # � SECURE CERTIFICATE AUTHORITY SERVICE - HTTPS ONLY
    # Private keys never transmitted - clients use CSR pattern
    logger.info("🔒 Starting Certificate Authority Service HTTPS-only on 0.0.0.0:9090")
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=9090,
        ssl_keyfile=str(ca_key_path),
        ssl_certfile=str(ca_cert_path),
        log_level="info"
    )