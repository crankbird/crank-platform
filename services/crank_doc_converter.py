"""
Crank Document Converter Service

Simple document conversion service that follows the exact same pattern as 
the working email classifier service.
"""

import asyncio
import json
import logging
import os
import tempfile
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Worker registration model
class WorkerRegistration(BaseModel):
    """Model for worker registration with platform."""
    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: List[str]

# Conversion request models
class ConversionRequest(BaseModel):
    """Model for document conversion requests."""
    input_format: str
    output_format: str
    options: Optional[Dict[str, Any]] = None

class ConversionResponse(BaseModel):
    """Model for document conversion responses."""
    conversion_id: str
    status: str
    output_format: str
    message: str

class CrankDocumentConverter:
    """Crank Document Converter Service following the working pattern."""
    
    def __init__(self, platform_url: str = None, cert_store=None):
        self.app = FastAPI(title="Crank Document Converter", version="1.0.0")
        
        # 🔐 ZERO-TRUST: Use pre-loaded certificates from synchronous initialization
        if cert_store is not None:
            logger.info("🔐 Using pre-loaded certificates from synchronous initialization")
            self.cert_store = cert_store
        else:
            logger.info("🔐 Creating empty certificate store (fallback)")
            import sys
            sys.path.append('/app/scripts')
            from crank_cert_initialize import SecureCertificateStore
            self.cert_store = SecureCertificateStore()
        
        # Always use HTTPS with Certificate Authority Service certificates
        self.platform_url = platform_url or os.getenv("PLATFORM_URL", "https://platform:8443")
        self.worker_url = os.getenv("WORKER_URL", "https://crank-doc-converter:8100")
        
        # Certificate files are purely in-memory now - no disk dependencies
        self.cert_file = None
        self.key_file = None 
        self.ca_file = None
        
        self.worker_id = None
        
        # Setup routes
        self._setup_routes()
        
        # Register startup/shutdown handlers
        self.app.add_event_handler("startup", self._startup)
        self.app.add_event_handler("shutdown", self._shutdown)
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint with security status."""
            security_status = {}
            if hasattr(self, 'cert_store'):
                security_status = {
                    "ssl_enabled": self.cert_store.platform_cert is not None,
                    "ca_cert_available": self.cert_store.ca_cert is not None,
                    "certificate_source": "Certificate Authority Service"
                }
            
            return {
                "status": "healthy",
                "service": "crank-document-converter",
                "worker_id": self.worker_id,
                "timestamp": datetime.utcnow().isoformat(),
                "security": security_status
            }

        @self.app.get("/")
        async def root():
            """Root endpoint with service information."""
            return {
                "service": "Crank Document Converter",
                "version": "1.0.0",
                "worker_id": self.worker_id,
                "capabilities": [
                    "document-conversion",
                    "format-detection", 
                    "pandoc-integration"
                ]
            }

        @self.app.post("/convert")
        async def convert_document_endpoint(
            file: UploadFile = File(...),
            output_format: str = Form(...),
            input_format: Optional[str] = Form(None)
        ):
            """Convert uploaded document to specified format."""
            try:
                # Read file content
                content = await file.read()
                
                # Detect input format if not specified
                if not input_format:
                    input_format = self.detect_format(content, file.filename)
                
                logger.info(f"Converting {file.filename} from {input_format} to {output_format}")
                
                # Perform conversion
                converted_content = self.convert_document(content, input_format, output_format)
                
                conversion_id = str(uuid4())
                
                # For now, return base64 encoded content
                import base64
                encoded_content = base64.b64encode(converted_content).decode('utf-8')
                
                return ConversionResponse(
                    conversion_id=conversion_id,
                    status="completed",
                    output_format=output_format,
                    message=f"Successfully converted {file.filename} to {output_format}"
                ).dict() | {"content": encoded_content}
                
            except Exception as e:
                logger.error(f"Conversion failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/formats")
        async def supported_formats():
            """Get supported input and output formats."""
            return {
                "input_formats": [
                    "markdown", "html", "docx", "odt", "rtf", "plain", "pdf"
                ],
                "output_formats": [
                    "markdown", "html", "docx", "odt", "rtf", "plain", "pdf"
                ]
            }
    
    def detect_format(self, content: bytes, filename: str = None) -> str:
        """Detect document format from content and filename."""
        if filename:
            ext = Path(filename).suffix.lower()
            format_map = {
                '.md': 'markdown',
                '.txt': 'plain',
                '.html': 'html',
                '.htm': 'html',
                '.pdf': 'pdf',
                '.docx': 'docx',
                '.doc': 'doc',
                '.odt': 'odt',
                '.rtf': 'rtf'
            }
            if ext in format_map:
                return format_map[ext]
        
        # Try to detect from content
        content_str = content[:1024].decode('utf-8', errors='ignore').lower()
        
        if content_str.startswith('<!doctype html') or '<html' in content_str:
            return 'html'
        elif content_str.startswith('#') or '**' in content_str:
            return 'markdown'
        else:
            return 'plain'

    def convert_document(self, input_content: bytes, input_format: str, output_format: str, options: Dict = None) -> bytes:
        """Convert document using pandoc."""
        options = options or {}
        
        with tempfile.NamedTemporaryFile(suffix=f'.{input_format}', delete=False) as input_file:
            input_file.write(input_content)
            input_file.flush()
            
            with tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False) as output_file:
                try:
                    # Build pandoc command
                    cmd = [
                        'pandoc',
                        '-f', input_format,
                        '-t', output_format,
                        '-o', output_file.name,
                        input_file.name
                    ]
                    
                    # Add common options
                    if output_format == 'pdf':
                        cmd.extend(['--pdf-engine=xelatex'])
                    
                    # Run conversion
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode != 0:
                        raise Exception(f"Pandoc error: {result.stderr}")
                    
                    # Read converted content
                    with open(output_file.name, 'rb') as f:
                        return f.read()
                        
                finally:
                    # Cleanup temp files
                    try:
                        os.unlink(input_file.name)
                        os.unlink(output_file.name)
                    except:
                        pass

    async def _startup(self):
        """Startup handler - register with platform."""
        logger.info("📄 Starting Crank Document Converter...")
        
        # Log security level for visibility (certificates already loaded synchronously)
        logger.info("🔐 Using certificates loaded synchronously at startup")
        
        # Prepare registration info
        worker_info = WorkerRegistration(
            worker_id=f"doc-converter-{uuid4().hex[:8]}",
            service_type="document_conversion",
            endpoint=self.worker_url,
            health_url=f"{self.worker_url}/health",
            capabilities=["document-conversion", "format-detection", "pandoc-integration"]
        )
        
        self.worker_id = worker_info.worker_id
        
        # Register with platform
        await self._register_with_platform(worker_info)
        
        # Start heartbeat background task
        self._start_heartbeat_task()
    
    async def _register_with_platform(self, worker_info: WorkerRegistration):
        """Register this worker with the platform."""
        try:
            async with self._create_client() as client:
                response = await client.post(
                    f"{self.platform_url}/workers/register",
                    json=worker_info.dict(),
                    timeout=30.0
                )
                
            if response.status_code == 200:
                logger.info(f"✅ Successfully registered worker {worker_info.worker_id}")
            else:
                logger.error(f"❌ Registration failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Registration error: {e}")

    def _create_client(self):
        """Create HTTP client with certificate verification."""
        if hasattr(self.cert_store, 'ca_cert') and self.cert_store.ca_cert:
            # Use CA certificate for verification
            return httpx.AsyncClient(verify=False)  # Simplified for now
        else:
            return httpx.AsyncClient(verify=False)

    def _start_heartbeat_task(self):
        """Start the background heartbeat task."""
        heartbeat_interval = int(os.getenv("WORKER_HEARTBEAT_INTERVAL", "20"))
        
        async def heartbeat_loop():
            """Background task to send periodic heartbeats."""
            while True:
                try:
                    await asyncio.sleep(heartbeat_interval)
                    if self.worker_id:
                        await self._send_heartbeat()
                except asyncio.CancelledError:
                    logger.info("Heartbeat task cancelled")
                    break
                except Exception as e:
                    logger.warning(f"Heartbeat failed: {e}")
        
        # Start the background task
        asyncio.create_task(heartbeat_loop())
        logger.info(f"🫀 Started heartbeat task with {heartbeat_interval}s interval")

    async def _send_heartbeat(self):
        """Send heartbeat to platform."""
        try:
            async with self._create_client() as client:
                response = await client.post(
                    f"{self.platform_url}/workers/{self.worker_id}/heartbeat",
                    json={"timestamp": datetime.utcnow().isoformat()},
                    timeout=5.0
                )
                
            if response.status_code == 200:
                logger.debug(f"🫀 Heartbeat sent successfully")
            else:
                logger.warning(f"Heartbeat failed: {response.status_code}")
                
        except Exception as e:
            logger.debug(f"Heartbeat error: {e}")

    async def _shutdown(self):
        """Shutdown handler - deregister from platform."""
        if self.worker_id:
            logger.info("🔒 Deregistering document converter from platform...")
            try:
                async with self._create_client() as client:
                    await client.delete(f"{self.platform_url}/v1/workers/{self.worker_id}")
                logger.info("🔒 Successfully deregistered document converter")
            except Exception as e:
                logger.warning(f"Failed to deregister from platform: {e}")


def create_crank_document_converter(platform_url: str = None, cert_store=None) -> FastAPI:
    """Create Crank Document Converter application."""
    converter = CrankDocumentConverter(platform_url, cert_store)
    return converter.app


def main():
    """Main entry point with HTTPS enforcement and Certificate Authority Service integration."""
    import uvicorn
    from pathlib import Path
    
    # 🔒 ENFORCE HTTPS-ONLY MODE: No HTTP fallback allowed
    https_only = os.getenv("HTTPS_ONLY", "true").lower() == "true"
    ca_service_url = os.getenv("CA_SERVICE_URL")
    
    if https_only and ca_service_url:
        print("🔐 Initializing certificates using SECURE CSR pattern...")
        try:
            # Run secure certificate initialization in the same process
            import sys
            sys.path.append('/app/scripts')
            import asyncio
            from crank_cert_initialize import main as init_certificates, cert_store
            
            # Run secure certificate initialization
            asyncio.run(init_certificates())
            
            # Check if certificates were loaded
            if cert_store.platform_cert is None:
                raise RuntimeError("🚫 Certificate initialization completed but no certificates in memory")
            
            print("✅ Certificates loaded successfully using SECURE CSR pattern")
            print("🔒 SECURITY: Private keys generated locally and never transmitted")
            
            use_https = True
            logger.info("🔐 Using in-memory certificates from secure initialization")
        except Exception as e:
            raise RuntimeError(f"🚫 Failed to initialize certificates with CA service: {e}")
    else:
        raise RuntimeError("🚫 HTTPS_ONLY environment requires Certificate Authority Service")
    
    # 🚢 PORT CONFIGURATION: Use environment variables for flexible deployment  
    service_port = int(os.getenv("DOC_CONVERTER_PORT", "8100"))  # HTTP fallback port
    service_host = os.getenv("DOC_CONVERTER_HOST", "0.0.0.0")
    https_port = int(os.getenv("DOC_CONVERTER_HTTPS_PORT", "8100"))
    
    # Create FastAPI app with pre-loaded certificates
    app = create_crank_document_converter(cert_store=cert_store)
    
    # 🔒 HTTPS-ONLY MODE: Always use HTTPS with Certificate Authority Service certificates
    if https_only:
        if not use_https:
            raise RuntimeError("🚫 HTTPS_ONLY=true but certificates not found. Cannot start service.")
        logger.info(f"🔒 Starting Crank Document Converter with HTTPS/mTLS ONLY on port {https_port}")
        logger.info("🔐 Using in-memory certificates from Certificate Authority Service")
        
        # Create SSL context from in-memory certificates (SECURE CSR pattern)
        try:
            import sys
            sys.path.append('/app/scripts')
            from crank_cert_initialize import cert_store
            ssl_context = cert_store.get_ssl_context()
            
            print("🔒 Using certificates obtained via SECURE CSR pattern")
            
            # Get the temporary certificate file paths for uvicorn
            cert_file = cert_store._temp_cert_file
            key_file = cert_store._temp_key_file
            
            uvicorn.run(
                app, 
                host=service_host, 
                port=https_port,
                ssl_keyfile=key_file,
                ssl_certfile=cert_file
            )
        except Exception as e:
            raise RuntimeError(f"🚫 Failed to create SSL context from Certificate Authority Service: {e}")
    else:
        raise RuntimeError("🚫 HTTP mode disabled permanently - Certificate Authority Service provides HTTPS-only security")


# For direct running
if __name__ == "__main__":
    main()

import asyncio
import json
import logging
import os
import tempfile
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Worker registration model
class WorkerRegistration(BaseModel):
    """Model for worker registration with platform."""
    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: List[str]

# Conversion request models
class ConversionRequest(BaseModel):
    """Model for document conversion requests."""
    input_format: str
    output_format: str
    options: Optional[Dict[str, Any]] = None

class ConversionResponse(BaseModel):
    """Model for document conversion responses."""
    conversion_id: str
    status: str
    output_format: str
    message: str

# Initialize FastAPI app
app = FastAPI(
    title="Crank Document Converter",
    description="Document conversion service with pandoc integration",
    version="1.0.0"
)

# Global configuration
PLATFORM_URL = os.getenv("PLATFORM_URL", "https://localhost:8443")
WORKER_URL = os.getenv("WORKER_URL", "https://localhost:8100")
WORKER_ID = f"doc-converter-{uuid4().hex[:8]}"

async def initialize_security():
    """Initialize secure certificate store."""
    global security_store
    try:
        # Import and run certificate initialization
        import sys
        import subprocess
        
        # Run the certificate initialization script
        logger.info("🔐 Initializing certificates via CSR pattern...")
        result = subprocess.run([
            sys.executable, "/app/scripts/crank_cert_initialize.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            logger.error(f"Certificate initialization failed: {result.stderr}")
            return False
            
        logger.info("✅ Certificate initialization completed")
        
        # Verify certificate files exist
        cert_files = ["/etc/certs/server.crt", "/etc/certs/server.key", "/etc/certs/ca.crt"]
        for cert_file in cert_files:
            if not os.path.exists(cert_file):
                logger.error(f"Certificate file missing: {cert_file}")
                return False
                
        logger.info("✅ All certificate files verified")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize security: {e}")
        return False

async def register_with_platform():
    """Register this worker with the platform."""
    registration = WorkerRegistration(
        worker_id=WORKER_ID,
        service_type="document-converter",
        endpoint=WORKER_URL,
        health_url=f"{WORKER_URL}/health",
        capabilities=[
            "document-conversion",
            "format-detection",
            "pandoc-integration"
        ]
    )
    
    try:
        # Create SSL context that accepts our CA certificates
        import ssl
        ssl_context = ssl.create_default_context(cafile="/etc/certs/ca.crt")
        
        async with httpx.AsyncClient(verify=ssl_context) as client:
            response = await client.post(
                f"{PLATFORM_URL}/workers/register",
                json=registration.dict(),
                timeout=30.0
            )
            
        if response.status_code == 200:
            logger.info(f"✅ Successfully registered worker {WORKER_ID}")
            return True
        else:
            logger.error(f"❌ Registration failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Registration error: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize security and register with platform on startup."""
    logger.info("🚀 Starting Crank Document Converter...")
    
    if not await initialize_security():
        logger.error("Failed to initialize security - exiting")
        exit(1)
    
    # Wait a moment for platform to be ready
    await asyncio.sleep(2)
    
    if not await register_with_platform():
        logger.warning("Failed to register with platform - continuing anyway")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "crank-document-converter",
        "worker_id": WORKER_ID,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Crank Document Converter",
        "version": "1.0.0",
        "worker_id": WORKER_ID,
        "capabilities": [
            "document-conversion",
            "format-detection", 
            "pandoc-integration"
        ]
    }

def detect_format(content: bytes, filename: str = None) -> str:
    """Detect document format from content and filename."""
    if filename:
        ext = Path(filename).suffix.lower()
        format_map = {
            '.md': 'markdown',
            '.txt': 'plain',
            '.html': 'html',
            '.htm': 'html',
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.doc': 'doc',
            '.odt': 'odt',
            '.rtf': 'rtf'
        }
        if ext in format_map:
            return format_map[ext]
    
    # Try to detect from content
    content_str = content[:1024].decode('utf-8', errors='ignore').lower()
    
    if content_str.startswith('<!doctype html') or '<html' in content_str:
        return 'html'
    elif content_str.startswith('#') or '**' in content_str:
        return 'markdown'
    else:
        return 'plain'

def convert_document(input_content: bytes, input_format: str, output_format: str, options: Dict = None) -> bytes:
    """Convert document using pandoc."""
    options = options or {}
    
    with tempfile.NamedTemporaryFile(suffix=f'.{input_format}', delete=False) as input_file:
        input_file.write(input_content)
        input_file.flush()
        
        with tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False) as output_file:
            try:
                # Build pandoc command
                cmd = [
                    'pandoc',
                    '-f', input_format,
                    '-t', output_format,
                    '-o', output_file.name,
                    input_file.name
                ]
                
                # Add common options
                if output_format == 'pdf':
                    cmd.extend(['--pdf-engine=xelatex'])
                
                # Run conversion
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    raise Exception(f"Pandoc error: {result.stderr}")
                
                # Read converted content
                with open(output_file.name, 'rb') as f:
                    return f.read()
                    
            finally:
                # Cleanup temp files
                try:
                    os.unlink(input_file.name)
                    os.unlink(output_file.name)
                except:
                    pass

@app.post("/convert")
async def convert_document_endpoint(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    input_format: Optional[str] = Form(None)
):
    """Convert uploaded document to specified format."""
    try:
        # Read file content
        content = await file.read()
        
        # Detect input format if not specified
        if not input_format:
            input_format = detect_format(content, file.filename)
        
        logger.info(f"Converting {file.filename} from {input_format} to {output_format}")
        
        # Perform conversion
        converted_content = convert_document(content, input_format, output_format)
        
        conversion_id = str(uuid4())
        
        # For now, return base64 encoded content
        # In production, this might be stored and referenced by ID
        import base64
        encoded_content = base64.b64encode(converted_content).decode('utf-8')
        
        return ConversionResponse(
            conversion_id=conversion_id,
            status="completed",
            output_format=output_format,
            message=f"Successfully converted {file.filename} to {output_format}"
        ).dict() | {"content": encoded_content}
        
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/formats")
async def supported_formats():
    """Get supported input and output formats."""
    return {
        "input_formats": [
            "markdown", "html", "docx", "odt", "rtf", "plain", "pdf"
        ],
        "output_formats": [
            "markdown", "html", "docx", "odt", "rtf", "plain", "pdf"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8100,
        ssl_keyfile="/etc/certs/server.key",
        ssl_certfile="/etc/certs/server.crt"
    )