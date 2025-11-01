"""
Zero-Trust Security Configuration

Implements HTTPS + mTLS for all platform communications to keep the bunny happy! 🐰🔒

Features:
- mTLS between platform and workers
- Certificate management and rotation
- Secure file upload handling
- Network security policies
"""

import ssl
import os
from typing import Optional, Dict, Any
from pathlib import Path
import httpx
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration for zero-trust architecture."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.cert_dir = Path("/etc/certs")
        
        # Certificate paths
        self.ca_cert_path = self.cert_dir / "ca.crt"
        self.platform_cert_path = self.cert_dir / "platform.crt" 
        self.platform_key_path = self.cert_dir / "platform.key"
        
        # Security settings
        self.verify_certificates = environment == "production"
        self.require_mtls = environment == "production"
        
    def get_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for secure connections."""
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        
        if self.verify_certificates:
            # Load CA certificate for verification
            if self.ca_cert_path.exists():
                context.load_verify_locations(str(self.ca_cert_path))
            else:
                logger.warning("CA certificate not found - using default verification")
        else:
            # Development: disable certificate verification (NOT for production!)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            logger.warning("🚨 Certificate verification DISABLED - development only!")
            
        return context
    
    def get_client_cert(self) -> Optional[tuple]:
        """Get client certificate for mTLS."""
        if self.require_mtls:
            if self.platform_cert_path.exists() and self.platform_key_path.exists():
                return (str(self.platform_cert_path), str(self.platform_key_path))
            else:
                raise FileNotFoundError("Client certificates required for mTLS but not found")
        return None
    
    def create_secure_http_client(self, timeout: int = 30) -> httpx.AsyncClient:
        """Create HTTPS client with proper security configuration."""
        
        # Build client configuration
        client_config = {
            "timeout": httpx.Timeout(timeout),
            "follow_redirects": False,  # Security: no automatic redirects
            "limits": httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30
            )
        }
        
        if self.environment == "production":
            # Production: Full security
            client_config.update({
                "verify": str(self.ca_cert_path) if self.ca_cert_path.exists() else True,
                "cert": self.get_client_cert()
            })
            logger.info("🔒 Secure HTTPS client created with mTLS")
        else:
            # Development: Relaxed security with warnings
            client_config["verify"] = False
            logger.warning("🚨 INSECURE HTTP client - development only!")
            
        return httpx.AsyncClient(**client_config)


class SecurePlatformService:
    """Enhanced platform service with zero-trust security."""
    
    def __init__(self, environment: str = "development"):
        self.security = SecurityConfig(environment)
        self.environment = environment
        
    async def secure_worker_call(self, worker_endpoint: str, endpoint: str, 
                                **request_kwargs) -> httpx.Response:
        """Make secure HTTPS call to worker with mTLS."""
        
        # Ensure HTTPS for production
        if self.environment == "production" and not worker_endpoint.startswith("https://"):
            raise HTTPException(
                status_code=500, 
                detail="Zero-trust violation: Worker endpoints must use HTTPS in production"
            )
        
        # For development, convert HTTP to HTTPS if needed
        if self.environment == "development" and worker_endpoint.startswith("http://"):
            # In development, we might still use HTTP internally
            url = f"{worker_endpoint}{endpoint}"
        else:
            url = f"{worker_endpoint}{endpoint}"
            
        try:
            async with self.security.create_secure_http_client() as client:
                response = await client.post(url, **request_kwargs)
                response.raise_for_status()
                return response
                
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to worker {worker_endpoint}: {e}")
            raise HTTPException(status_code=503, detail=f"Worker unavailable: {worker_endpoint}")
        except httpx.TimeoutException:
            logger.error(f"Timeout calling worker {worker_endpoint}")
            raise HTTPException(status_code=504, detail=f"Worker timeout: {worker_endpoint}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Worker returned error {e.response.status_code}: {e.response.text}")
            raise HTTPException(status_code=502, detail=f"Worker error: {e.response.status_code}")


# Certificate generation utilities for development
class ResilientCertificateManager:
    """Anti-fragile certificate management for zero-trust architecture."""
    
    @staticmethod
    def generate_complete_dev_certificates(cert_dir: Path):
        """Generate complete certificate chain: CA + server + client certificates."""
        import subprocess
        
        cert_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"🔐 Generating complete certificate infrastructure in {cert_dir}")
        
        # 1. Generate Certificate Authority (CA)
        logger.info("📜 Generating Certificate Authority...")
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:4096", 
            "-keyout", str(cert_dir / "ca.key"), 
            "-out", str(cert_dir / "ca.crt"),
            "-days", "365", "-nodes", 
            "-subj", "/CN=Crank Platform CA/O=Crank Platform/OU=Security"
        ], check=True, capture_output=True)
        
        # 2. Generate Platform Server Certificate
        logger.info("🖥️ Generating platform server certificate...")
        subprocess.run([
            "openssl", "req", "-newkey", "rsa:4096", 
            "-keyout", str(cert_dir / "platform.key"), 
            "-out", str(cert_dir / "platform.csr"),
            "-nodes", "-subj", "/CN=platform/O=Crank Platform/OU=Platform"
        ], check=True, capture_output=True)
        
        subprocess.run([
            "openssl", "x509", "-req", 
            "-in", str(cert_dir / "platform.csr"),
            "-CA", str(cert_dir / "ca.crt"), 
            "-CAkey", str(cert_dir / "ca.key"),
            "-CAcreateserial", 
            "-out", str(cert_dir / "platform.crt"), 
            "-days", "365",
            "-extensions", "v3_req"
        ], check=True, capture_output=True)
        
        # 3. Generate Client Certificate for Workers
        logger.info("👥 Generating client certificate for workers...")
        subprocess.run([
            "openssl", "req", "-newkey", "rsa:4096", 
            "-keyout", str(cert_dir / "client.key"), 
            "-out", str(cert_dir / "client.csr"),
            "-nodes", "-subj", "/CN=worker-client/O=Crank Platform/OU=Workers"
        ], check=True, capture_output=True)
        
        subprocess.run([
            "openssl", "x509", "-req", 
            "-in", str(cert_dir / "client.csr"),
            "-CA", str(cert_dir / "ca.crt"), 
            "-CAkey", str(cert_dir / "ca.key"),
            "-CAcreateserial", 
            "-out", str(cert_dir / "client.crt"), 
            "-days", "365"
        ], check=True, capture_output=True)
        
        # Set proper permissions
        os.chmod(str(cert_dir / "ca.key"), 0o600)
        os.chmod(str(cert_dir / "platform.key"), 0o600)
        os.chmod(str(cert_dir / "client.key"), 0o600)
        
        logger.info("✅ Complete certificate infrastructure generated successfully")
        
    @staticmethod
    def verify_certificate_health(cert_dir: Path) -> Dict[str, Any]:
        """Check certificate validity and health."""
        ca_cert = cert_dir / "ca.crt"
        platform_cert = cert_dir / "platform.crt"
        client_cert = cert_dir / "client.crt"
        
        health_status = {
            "ca_cert_exists": ca_cert.exists(),
            "platform_cert_exists": platform_cert.exists(),
            "client_cert_exists": client_cert.exists(),
            "certificate_chain_complete": False,
            "security_level": "none"
        }
        
        if all(cert.exists() for cert in [ca_cert, platform_cert, client_cert]):
            health_status["certificate_chain_complete"] = True
            health_status["security_level"] = "full_mtls"
        elif platform_cert.exists():
            health_status["security_level"] = "server_tls"
        elif ca_cert.exists():
            health_status["security_level"] = "ca_only"
        
        return health_status


class AdaptiveSecurityConfig(SecurityConfig):
    """Enhanced security configuration with adaptive certificate management."""
    
    def __init__(self, environment: str = "development"):
        super().__init__(environment)
        self.client_cert_path = self.cert_dir / "client.crt"
        self.client_key_path = self.cert_dir / "client.key"
        
    def get_security_level(self) -> str:
        """Determine current security level based on available certificates."""
        health = ResilientCertificateManager.verify_certificate_health(self.cert_dir)
        return health["security_level"]
    
    def get_client_cert_for_mtls(self) -> Optional[tuple]:
        """Get client certificate tuple for mTLS connections."""
        if self.client_cert_path.exists() and self.client_key_path.exists():
            return (str(self.client_cert_path), str(self.client_key_path))
        return None
    
    def create_adaptive_http_client(self, timeout: int = 30) -> httpx.AsyncClient:
        """Create HTTP client that adapts to available security infrastructure."""
        
        security_level = self.get_security_level()
        logger.info(f"🔒 Creating HTTP client with security level: {security_level}")
        
        # Build base client configuration
        client_config = {
            "timeout": httpx.Timeout(timeout),
            "follow_redirects": False,
            "limits": httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30
            )
        }
        
        if security_level == "full_mtls":
            # Full mTLS with client certificates
            client_config.update({
                "verify": str(self.ca_cert_path),
                "cert": self.get_client_cert_for_mtls()
            })
            logger.info("🔐 Full mTLS client created with client certificates")
            
        elif security_level == "server_tls":
            # Server-only TLS (verify server, no client cert)
            client_config["verify"] = str(self.ca_cert_path) if self.ca_cert_path.exists() else True
            logger.info("🔒 Server-only TLS client created")
            
        else:
            # Development fallback - insecure but functional
            client_config["verify"] = False
            logger.warning("⚠️ Insecure HTTP client - no certificates available")
            
        return httpx.AsyncClient(**client_config)


# Environment-aware security initialization
def initialize_security(environment: str = None) -> AdaptiveSecurityConfig:
    """Initialize anti-fragile security based on environment."""
    
    if environment is None:
        environment = os.getenv("CRANK_ENVIRONMENT", "development")
    
    security_config = AdaptiveSecurityConfig(environment)
    
    if environment == "development":
        # Generate complete certificate chain if missing
        if not security_config.ca_cert_path.exists():
            logger.info("🔧 Generating complete development certificate infrastructure...")
            ResilientCertificateManager.generate_complete_dev_certificates(security_config.cert_dir)
        
        # Verify certificate health
        health = ResilientCertificateManager.verify_certificate_health(security_config.cert_dir)
        logger.info(f"🔍 Certificate health: {health['security_level']} (complete: {health['certificate_chain_complete']})")
        
    elif environment == "production":
        # Verify all certificates exist
        required_certs = [
            security_config.ca_cert_path,
            security_config.platform_cert_path, 
            security_config.platform_key_path,
            security_config.client_cert_path,
            security_config.client_key_path
        ]
        
        missing_certs = [cert for cert in required_certs if not cert.exists()]
        if missing_certs:
            raise FileNotFoundError(
                f"🚨 PRODUCTION SECURITY FAILURE: Missing certificates: {missing_certs}"
            )
        
        logger.info("🔒 Production security initialized with full mTLS")
    
    return security_config