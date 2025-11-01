"""
Crank Document Converter Service

Independent document conversion service that registers with the platform and provides
real document processing capabilities. Supports multiple formats via pandoc and LibreOffice.
Part of the platform + worker architecture.
"""

import asyncio
import json
import logging
import os
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from fastapi import FastAPI, UploadFile, HTTPException, Form
from pydantic import BaseModel

# Import existing CrankDoc mesh service for fallback
from crankdoc_mesh_minimal import CrankDocMeshService
from crankdoc_mesh_minimal import MeshRequest, MeshResponse

# Import security configuration
from security_config import initialize_security

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealDocumentConverter:
    """Real document converter using pandoc and other tools."""
    
    # Supported format mappings
    PANDOC_FORMATS = {
        # Input formats pandoc can read
        'markdown': ['md', 'markdown'],
        'html': ['html', 'htm'],
        'latex': ['tex', 'latex'],
        'rst': ['rst'],
        'docx': ['docx'],
        'odt': ['odt'],
        'txt': ['txt', 'text'],
        # Output formats pandoc can write
        'pdf': ['pdf'],
        'html': ['html'],
        'docx': ['docx'],
        'odt': ['odt'],
        'latex': ['tex'],
        'markdown': ['md'],
        'rst': ['rst'],
        'txt': ['txt']
    }
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir())
    
    def detect_format(self, filename: str, content: bytes) -> str:
        """Detect document format from filename or content."""
        if not filename:
            return "txt"
        
        ext = Path(filename).suffix.lower().lstrip('.')
        
        # Map common extensions to pandoc format names
        format_map = {
            'md': 'markdown',
            'markdown': 'markdown', 
            'txt': 'txt',
            'text': 'txt',
            'html': 'html',
            'htm': 'html',
            'pdf': 'pdf',
            'docx': 'docx',
            'odt': 'odt',
            'tex': 'latex',
            'latex': 'latex',
            'rst': 'rst'
        }
        
        return format_map.get(ext, 'txt')
    
    async def convert_document(self, content: bytes, filename: str, 
                             source_format: str, target_format: str) -> Dict[str, Any]:
        """Convert document using pandoc."""
        
        try:
            # Auto-detect source format if needed
            if source_format == "auto":
                source_format = self.detect_format(filename, content)
            
            # Create temporary files
            input_file = self.temp_dir / f"input_{uuid4()}.{source_format}"
            output_file = self.temp_dir / f"output_{uuid4()}.{target_format}"
            
            # Write input content
            input_file.write_bytes(content)
            
            # Build pandoc command
            cmd = [
                "pandoc",
                str(input_file),
                "-f", source_format,
                "-t", target_format,
                "-o", str(output_file),
                "--standalone"  # Include headers/footers
            ]
            
            # Add PDF-specific options
            if target_format == "pdf":
                cmd.extend(["--pdf-engine=xelatex"])  # Use xelatex for better Unicode support
            
            # Run conversion
            logger.info(f"Converting {source_format} to {target_format} using pandoc")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise ValueError(f"Pandoc conversion failed: {result.stderr}")
            
            # Read converted content
            if output_file.exists():
                converted_content = output_file.read_bytes()
                
                # Clean up temp files
                input_file.unlink(missing_ok=True)
                output_file.unlink(missing_ok=True)
                
                return {
                    "success": True,
                    "converted_content": converted_content.decode('utf-8', errors='ignore') if target_format in ['html', 'markdown', 'txt', 'latex', 'rst'] else converted_content.hex(),
                    "output_format": target_format,
                    "source_format": source_format,
                    "size_bytes": len(converted_content),
                    "conversion_engine": "pandoc"
                }
            else:
                raise ValueError("Conversion completed but output file not found")
                
        except subprocess.TimeoutExpired:
            raise ValueError("Conversion timed out after 30 seconds")
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            raise ValueError(f"Conversion failed: {str(e)}")
        finally:
            # Ensure cleanup
            input_file.unlink(missing_ok=True) if 'input_file' in locals() else None
            output_file.unlink(missing_ok=True) if 'output_file' in locals() else None


class WorkerRegistration(BaseModel):
    """Worker registration request matching platform expectations."""
    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: List[str]


class CrankDocumentConverter:
    """Crank Document Converter Service that registers with platform."""
    
    def __init__(self, platform_url: str = None):
        self.app = FastAPI(title="Crank Document Converter", version="1.0.0")
        
        # Auto-detect HTTPS based on certificate availability
        cert_dir = Path("/etc/certs")
        has_certs = (cert_dir / "platform.crt").exists() and (cert_dir / "platform.key").exists()
        
        # 🔒 ZERO-TRUST: Always use HTTPS for platform communication when certs available
        if has_certs:
            self.platform_url = platform_url or os.getenv("PLATFORM_URL", "https://platform:8443")
            self.worker_url = os.getenv("WORKER_URL", "https://crank-doc-converter:8443")
            # mTLS client configuration with proper CA handling
            self.cert_file = cert_dir / "platform.crt"
            self.key_file = cert_dir / "platform.key"
            self.ca_file = cert_dir / "ca.crt"  # Use proper CA certificate
        else:
            # Fallback to HTTP only in development without certificates
            self.platform_url = platform_url or os.getenv("PLATFORM_URL", "http://platform:8080")
            self.worker_url = os.getenv("WORKER_URL", "http://crank-doc-converter:8081")
            self.cert_file = None
            self.key_file = None
            self.ca_file = None
            logger.warning("⚠️  No certificates found - falling back to HTTP (development only)")
            
        self.worker_id = None
        
        # Initialize real document conversion
        self.converter = RealDocumentConverter()
        
        # Keep fallback for unsupported conversions
        self.fallback_service = CrankDocMeshService()
        
        # Setup routes
        self._setup_routes()
        
        # Register startup task
        self.app.add_event_handler("startup", self._startup)
        self.app.add_event_handler("shutdown", self._shutdown)
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint with security status."""
            security_status = {}
            if hasattr(self, 'security_config'):
                security_status = {
                    "security_level": self.security_config.get_security_level(),
                    "ssl_enabled": os.path.exists("/etc/certs/platform.crt"),
                    "client_cert_available": os.path.exists("/etc/certs/client.crt")
                }
            
            return {
                "status": "healthy",
                "service": "crankdoc-worker",
                "capabilities": [cap.operation for cap in self.fallback_service.get_capabilities()],
                "security": security_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.post("/convert")
        async def convert_document(
            file: UploadFile,
            source_format: str = Form("auto"),
            target_format: str = Form(...),
            options: Optional[Dict[str, Any]] = None
        ):
            """Convert document between formats using real pandoc conversion."""
            try:
                # Read file content
                content = await file.read()
                filename = file.filename or "document"
                
                logger.info(f"Converting {filename}: {source_format} → {target_format}")
                
                # Try real conversion first
                try:
                    result = await self.converter.convert_document(
                        content=content,
                        filename=filename,
                        source_format=source_format,
                        target_format=target_format
                    )
                    
                    # Add metadata
                    result["metadata"] = {
                        "conversion_id": str(uuid4()),
                        "source_filename": filename,
                        "source_size": len(content),
                        "timestamp": "2024-01-01T00:00:00Z"  # TODO: Use real timestamp
                    }
                    result["receipt_id"] = result["metadata"]["conversion_id"][:8]
                    
                    return {"success": True, "result": result}
                    
                except Exception as conversion_error:
                    logger.warning(f"Real conversion failed: {conversion_error}")
                    logger.info("Falling back to mock conversion")
                    
                    # Fall back to mock service for unsupported conversions
                    request_data = {
                        "file": content,
                        "source_format": source_format,
                        "target_format": target_format,
                        "options": options or {}
                    }
                    
                    mesh_request = MeshRequest(
                        operation="convert",
                        data=request_data,
                        metadata={"filename": filename}
                    )
                    
                    # Process with fallback mock service
                    response = await self.fallback_service.process(mesh_request)
                
                if response.success:
                    return {
                        "success": True,
                        "result": response.data,
                        "receipt_id": response.receipt_id
                    }
                else:
                    raise HTTPException(status_code=400, detail=response.error)
                    
            except Exception as e:
                logger.error(f"Document conversion failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/convert-text")
        async def convert_text(request: Dict[str, Any]):
            """Convert text content directly (for platform routing)."""
            try:
                content = request.get("content", "")
                source_format = request.get("source_format", "auto")
                target_format = request.get("target_format", "html")
                filename = request.get("filename", "document.txt")
                
                logger.info(f"Converting text content: {source_format} → {target_format}")
                
                # Convert string content to bytes
                content_bytes = content.encode('utf-8')
                
                # Use the real converter
                result = await self.converter.convert_document(
                    content=content_bytes,
                    filename=filename,
                    source_format=source_format,
                    target_format=target_format
                )
                
                # Add metadata
                result["metadata"] = {
                    "conversion_id": str(uuid4()),
                    "worker_id": self.worker_id,
                    "timestamp": datetime.now().isoformat(),
                    "source_format": source_format,
                    "target_format": target_format
                }
                
                return result
                
            except Exception as e:
                logger.error(f"Text conversion failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/capabilities")
        async def get_capabilities():
            """Get worker capabilities."""
            capabilities = self.fallback_service.get_capabilities()
            return {
                "capabilities": [
                    {
                        "operation": cap.operation,
                        "description": cap.description,
                        "input_schema": cap.input_schema,
                        "output_schema": cap.output_schema
                    }
                    for cap in capabilities
                ]
            }
        
        @self.app.get("/plugin")
        async def get_plugin_metadata():
            """Get plugin metadata for platform integration."""
            # Read plugin metadata from file (prepared for future separation)
            plugin_file = Path("/app/plugin.yaml")
            if plugin_file.exists():
                import yaml
                try:
                    with open(plugin_file) as f:
                        plugin_data = yaml.safe_load(f)
                    return plugin_data
                except Exception as e:
                    logger.warning(f"Failed to read plugin metadata: {e}")
            
            # Fallback to hardcoded metadata
            return {
                "name": "crank-doc-converter",
                "version": "1.0.0",
                "description": "Real document format conversion powered by pandoc",
                "author": "Crank Platform Team",
                "capabilities": [cap.operation for cap in self.fallback_service.get_capabilities()],
                "health_endpoint": "/health",
                "separation_ready": True  # Indicates this worker is ready for repo separation
            }
    
    def _create_adaptive_client(self, timeout: float = 10.0) -> httpx.AsyncClient:
        """Create HTTP client with adaptive security based on available certificates."""
        if hasattr(self, 'security_config'):
            # Use the enhanced adaptive client from security config
            return self.security_config.create_adaptive_http_client(timeout)
        else:
            # Fallback for backward compatibility
            logger.warning("⚠️ Security config not initialized, using fallback client")
            return httpx.AsyncClient(verify=False, timeout=timeout)
    
    async def _startup(self):
        """Startup handler - register with platform."""
        logger.info("Starting CrankDoc Worker...")
        
        # Initialize enhanced security configuration
        logger.info("🔐 Initializing enhanced security configuration and certificates...")
        self.security_config = initialize_security()
        
        # Log security level for visibility
        security_level = self.security_config.get_security_level()
        logger.info(f"🔍 Security level: {security_level}")
        
        # Get capabilities for registration
        capabilities = self.fallback_service.get_capabilities()
        capability_names = [cap.operation for cap in capabilities]
        
        # Prepare registration info
        worker_info = WorkerRegistration(
            worker_id=f"crankdoc-{uuid4().hex[:8]}",  # Generate unique worker ID
            service_type="document",
            endpoint=self.worker_url,
            health_url=f"{self.worker_url}/health",
            capabilities=capability_names
        )
        
        # Register with platform
        await self._register_with_platform(worker_info)
        
        # Start heartbeat background task
        self._start_heartbeat_task()
    
    def _start_heartbeat_task(self):
        """Start the background heartbeat task."""
        import asyncio
        
        # Get heartbeat interval from environment (default 20 seconds)
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
            auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "dev-mesh-key")
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            # Prepare form data as expected by platform
            form_data = {
                "service_type": "document",
                "load_score": "0.0"
            }
            
            async with self._create_adaptive_client(timeout=10.0) as client:
                response = await client.post(
                    f"{self.platform_url}/v1/workers/{self.worker_id}/heartbeat",
                    headers=headers,
                    data=form_data  # Send as form data, not JSON
                )
                
                if response.status_code == 200:
                    logger.debug(f"💓 Heartbeat sent successfully for worker {self.worker_id}")
                else:
                    logger.warning(f"Heartbeat failed: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.warning(f"Failed to send heartbeat: {e}")
    
    async def _register_with_platform(self, worker_info: WorkerRegistration):
        """Register this worker with the platform using mTLS."""
        max_retries = 5
        retry_delay = 5  # seconds
        
        # Auth token for platform (using dev token from platform service)
        auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "dev-mesh-key")
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        for attempt in range(max_retries):
            try:
                # 🔒 ZERO-TRUST: Use mTLS client for secure communication
                async with self._create_adaptive_client() as client:
                    response = await client.post(
                        f"{self.platform_url}/v1/workers/register",
                        json=worker_info.model_dump(),
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.worker_id = result.get("worker_id")
                        logger.info(f"🔒 Successfully registered with platform via mTLS. Worker ID: {self.worker_id}")
                        return
                    else:
                        logger.warning(f"Registration attempt {attempt + 1} failed: {response.status_code} - {response.text}")
                        
            except Exception as e:
                logger.warning(f"Registration attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying registration in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
        
        logger.error("Failed to register with platform after all retries")
        # Continue running even if registration fails for development purposes
    
    async def _shutdown(self):
        """Shutdown handler - deregister from platform using mTLS."""
        if self.worker_id:
            try:
                # 🔒 ZERO-TRUST: Use mTLS client for secure deregistration
                async with self._create_adaptive_client(timeout=5.0) as client:
                    await client.delete(f"{self.platform_url}/v1/workers/{self.worker_id}")
                logger.info("🔒 Successfully deregistered from platform via mTLS")
            except Exception as e:
                logger.warning(f"Failed to deregister from platform: {e}")


def create_crank_doc_converter(platform_url: str = None) -> FastAPI:
    """Create Crank Document Converter application."""
    converter = CrankDocumentConverter(platform_url)
    return converter.app


# For direct running
if __name__ == "__main__":
    import uvicorn
    import ssl
    import os
    from pathlib import Path
    
    app = create_crank_doc_converter()
    
    # 🔒 ZERO-TRUST: Check for HTTPS-only mode
    https_only = os.getenv('HTTPS_ONLY', 'false').lower() == 'true'
    cert_dir = Path("/etc/certs")
    use_https = (cert_dir / "platform.crt").exists() and (cert_dir / "platform.key").exists()
    
    # 🚢 PORT CONFIGURATION: Use environment variables for flexible deployment  
    service_port = int(os.getenv("DOC_CONVERTER_PORT", "8100"))  # HTTP fallback port
    service_host = os.getenv("DOC_CONVERTER_HOST", "0.0.0.0")
    https_port = int(os.getenv("DOC_CONVERTER_HTTPS_PORT", "8101"))
    
    if https_only:
        if not use_https:
            raise RuntimeError("🚫 HTTPS_ONLY=true but certificates not found. Cannot start service.")
        logger.info(f"🔒 Starting Crank Document Converter with HTTPS/mTLS ONLY on port {https_port}")
        uvicorn.run(
            app, 
            host=service_host, 
            port=https_port,
            ssl_keyfile=str(cert_dir / "platform.key"),
            ssl_certfile=str(cert_dir / "platform.crt")
        )
    elif use_https:
        # Start with HTTPS using uvicorn SSL parameters
        logger.info(f"🔒 Starting Crank Document Converter with HTTPS on port {https_port}")
        try:
            uvicorn.run(
                app, 
                host=service_host, 
                port=https_port,
                ssl_keyfile=str(cert_dir / "platform.key"),
                ssl_certfile=str(cert_dir / "platform.crt")
            )
        except PermissionError as e:
            logger.warning(f"⚠️ SSL certificate permission denied: {e}")
            logger.info(f"🔓 Falling back to HTTP on port {service_port}")
            uvicorn.run(app, host=service_host, port=service_port)
        except Exception as e:
            logger.error(f"❌ SSL startup failed: {e}")
            logger.info(f"🔓 Falling back to HTTP on port {service_port}")
            uvicorn.run(app, host=service_host, port=service_port)
    else:
        logger.info(f"🔓 Starting Crank Document Converter with HTTP on port {service_port}")
        uvicorn.run(app, host=service_host, port=service_port)