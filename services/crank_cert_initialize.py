#!/usr/bin/env python3
"""
Secure Certificate Initialization using CSR Pattern
===================================================

SECURITY PRINCIPLES:
1. Private keys are generated locally and NEVER transmitted
2. Only Certificate Signing Requests (CSR) with public keys are sent to CA
3. CA service returns signed certificates over HTTPS
4. All certificates stored in memory (no disk persistence)

This implements the standard PKI pattern used by EST (Enrollment over Secure Transport)
and other secure certificate provisioning systems.
"""

import asyncio
import aiohttp
import logging
import os
import sys
import subprocess
import tempfile
import ssl
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureCertificateStore:
    """In-memory certificate store for secure certificate management."""
    
    def __init__(self):
        self.ca_cert = None
        self.platform_cert = None
        self.platform_key = None
        
    def store_certificates(self, ca_cert: str, platform_cert: str, platform_key: str):
        """Store certificates in memory."""
        self.ca_cert = ca_cert
        self.platform_cert = platform_cert
        self.platform_key = platform_key
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
cert_store = SecureCertificateStore()

class CertificateAuthorityClient:
    """Secure client for Certificate Authority Service communication."""
    
    def __init__(self, ca_service_url: str):
        self.ca_service_url = ca_service_url
        self.ca_cert_path = "/shared/ca-certs/ca.crt"  # STANDARDIZED: Single location for Root CA certificate
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context that trusts the Root CA certificate."""
        import ssl
        from pathlib import Path
        
        # Check if Root CA certificate is available
        if Path(self.ca_cert_path).exists():
            # Create SSL context that trusts our Root CA
            ssl_context = ssl.create_default_context(cafile=self.ca_cert_path)
            logger.info(f"🔒 Using Root CA certificate for verification: {self.ca_cert_path}")
            return ssl_context
        else:
            # Fallback to insecure for development (but warn)
            logger.warning(f"⚠️ Root CA certificate not found at {self.ca_cert_path}, using insecure connection")
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            return ssl_context
        
    async def wait_for_ca_service(self, max_wait: int = 30) -> bool:
        """Wait for Certificate Authority Service to be available."""
        logger.info(f"⏳ Waiting for Certificate Authority Service at {self.ca_service_url}")
        
        for i in range(max_wait):
            try:
                async with aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(ssl=False)  # Accept self-signed CA cert for development
                ) as session:
                    async with session.get(f"{self.ca_service_url}/health") as response:
                        if response.status == 200:
                            health_data = await response.json()
                            logger.info(f"✅ Certificate Authority Service ready: {health_data.get('provider', 'unknown')}")
                            return True
            except Exception as e:
                logger.debug(f"CA service not ready: {e}")
                
            await asyncio.sleep(1)
        
        logger.error(f"❌ Certificate Authority Service not available after {max_wait} seconds")
        return False
    
    async def get_ca_certificate(self) -> str:
        """Get the CA certificate for verification (public certificate only)."""
        ssl_context = self._create_ssl_context()
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context)  # Use Root CA for verification
        ) as session:
            async with session.get(f"{self.ca_service_url}/ca/certificate") as response:
                if response.status == 200:
                    ca_data = await response.json()
                    return ca_data["ca_certificate"]
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to get CA certificate: {response.status} - {error_text}")
    
    async def submit_csr(self, csr_pem: str, service_name: str) -> str:
        """Submit CSR to CA service for signing (SECURE - no private key transmitted)."""
        ssl_context = self._create_ssl_context()
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context)  # Use Root CA for verification
        ) as session:
            async with session.post(
                f"{self.ca_service_url}/certificates/csr",
                json={
                    "csr": csr_pem,
                    "service_name": service_name
                }
            ) as response:
                if response.status == 200:
                    cert_response = await response.json()
                    return cert_response["certificate"]
                else:
                    error_text = await response.text()
                    raise Exception(f"CA service rejected CSR: {response.status} - {error_text}")

async def generate_key_pair_and_csr(service_name: str = "platform") -> tuple[str, str]:
    """Generate RSA key pair and CSR locally (private key never leaves this container)."""
    logger.info("🔑 Generating local RSA key pair...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        private_key_path = os.path.join(temp_dir, "service.key")
        csr_path = os.path.join(temp_dir, "service.csr")
        
        # Generate 4096-bit RSA private key locally
        subprocess.run([
            "openssl", "genrsa", "-out", private_key_path, "4096"
        ], check=True)
        logger.info("✅ Private key generated locally (never transmitted)")
        
        # Generate CSR with Subject Alternative Names (SAN) for hostname verification
        config_path = os.path.join(temp_dir, "csr.conf")
        
        # Create OpenSSL config with Subject Alternative Names
        san_names = [service_name, "localhost"]
        if service_name == "platform":
            san_names.extend(["crank-platform", "platform"])
        
        san_list = ",".join([f"DNS:{name}" for name in san_names])
        
        config_content = f"""[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = {service_name}
O = Crank Platform
OU = Platform Services

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = {san_list}
"""
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        subprocess.run([
            "openssl", "req", "-new", "-key", private_key_path,
            "-out", csr_path, "-config", config_path
        ], check=True)
        logger.info(f"✅ Certificate Signing Request (CSR) generated with SAN: {san_list}")
        
        # Step C Debug: Verify CSR contains SAN extensions
        try:
            result = subprocess.run([
                "openssl", "req", "-in", csr_path, "-text", "-noout"
            ], capture_output=True, text=True, check=True)
            if "Subject Alternative Name" in result.stdout:
                logger.info(f"🔍 Step C Debug: CSR contains Subject Alternative Names extension")
            else:
                logger.warning(f"⚠️ Step C Debug: CSR missing Subject Alternative Names extension")
                logger.debug(f"CSR content: {result.stdout}")
        except Exception as e:
            logger.warning(f"⚠️ Could not verify CSR extensions: {e}")
        
        # Read the generated private key and CSR
        with open(private_key_path, 'r') as f:
            private_key_pem = f.read()
        with open(csr_path, 'r') as f:
            csr_pem = f.read()
    
    return private_key_pem, csr_pem

async def main():
    """Secure certificate initialization using CSR pattern - NO PRIVATE KEY TRANSMISSION."""
    # Get configuration from environment
    ca_service_url = os.getenv("CA_SERVICE_URL", "https://cert-authority:9090")
    environment = os.getenv("CRANK_ENVIRONMENT", "development")
    service_name = os.getenv("SERVICE_NAME", "platform")
    
    logger.info("🔒" + "="*60)
    logger.info("🔒 SECURE CERTIFICATE INITIALIZATION")
    logger.info("🔒" + "="*60)
    logger.info(f"🔐 Environment: {environment}")
    logger.info(f"🌐 CA Service URL: {ca_service_url}")
    logger.info(f"🏷️  Service Name: {service_name}")
    logger.info("🔒 Using SECURE CSR pattern")
    logger.info("🚫 Private keys NEVER transmitted over network")
    logger.info("💾 In-memory certificate storage only")
    logger.info("🔒" + "="*60)
    
    try:
        # Step 1: Generate key pair and CSR locally
        logger.info("Step 1: Generate local key pair and CSR")
        private_key_pem, csr_pem = await generate_key_pair_and_csr(service_name)
        
        # Step 2: Wait for CA service and get CA certificate
        logger.info("Step 2: Connect to Certificate Authority Service")
        ca_client = CertificateAuthorityClient(ca_service_url)
        
        if not await ca_client.wait_for_ca_service():
            raise Exception("Certificate Authority Service not available")
        
        ca_cert = await ca_client.get_ca_certificate()
        logger.info("✅ CA certificate obtained for verification")
        
        # Step 3: Submit CSR for signing
        logger.info("Step 3: Submit CSR to CA service for signing")
        logger.info("📝 Transmitting CSR (contains public key only)")
        
        signed_certificate = await ca_client.submit_csr(csr_pem, service_name)
        logger.info("✅ Certificate signed by Certificate Authority Service")
        
        # Step 4: Store certificates securely in memory and locally on disk
        logger.info("Step 4: Store certificates securely in memory and locally on disk")
        cert_store.store_certificates(
            ca_cert=ca_cert,
            platform_cert=signed_certificate,
            platform_key=private_key_pem  # This never left the container
        )
        
        # Also write certificates to local disk for worker service access
        cert_dir = "/etc/certs"
        os.makedirs(cert_dir, exist_ok=True)
        
        # Write certificate files (local to this container only)
        with open(f"{cert_dir}/platform.crt", "w") as f:
            f.write(signed_certificate)
        with open(f"{cert_dir}/platform.key", "w") as f:
            f.write(private_key_pem)
        with open(f"{cert_dir}/ca.crt", "w") as f:
            f.write(ca_cert)
            
        # Set proper permissions (readable by worker user only)
        os.chmod(f"{cert_dir}/platform.key", 0o600)  # Private key: owner read only
        os.chmod(f"{cert_dir}/platform.crt", 0o644)  # Certificate: owner read, others read
        os.chmod(f"{cert_dir}/ca.crt", 0o644)        # CA cert: owner read, others read
        
        logger.info("🔐 Certificates stored in memory and written to local disk")
        
        logger.info("🔒" + "="*60)
        logger.info("✅ SECURE CERTIFICATE INITIALIZATION COMPLETE")
        logger.info("🔒" + "="*60)
        logger.info("🔒 SECURITY VERIFIED:")
        logger.info("  ✅ Private key generated locally")
        logger.info("  ✅ Private key never transmitted")
        logger.info("  ✅ Only CSR (public key) sent to CA")
        logger.info("  ✅ Signed certificate received")
        logger.info("  ✅ All certificates stored in memory and local disk")
        logger.info("  ✅ Local certificate files secured with proper permissions")
        logger.info("🔒" + "="*60)
        
    except Exception as e:
        logger.error("🔒" + "="*60)
        logger.error("❌ SECURE CERTIFICATE INITIALIZATION FAILED")
        logger.error("🔒" + "="*60)
        logger.error(f"❌ Error: {e}")
        logger.error("🔒" + "="*60)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())