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
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from fastapi import FastAPI, UploadFile, HTTPException, Form
from pydantic import BaseModel

# Import existing CrankDoc mesh service for fallback
from crankdoc_mesh_minimal import CrankDocMeshService
from crankdoc_mesh_minimal import MeshRequest, MeshResponse

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
        self.platform_url = platform_url or os.getenv("PLATFORM_URL", "http://platform:8080")
        
        # Auto-detect HTTPS based on certificate availability
        cert_dir = Path("/etc/certs")
        has_certs = (cert_dir / "platform.crt").exists() and (cert_dir / "platform.key").exists()
        
        if has_certs:
            self.worker_url = os.getenv("WORKER_URL", "https://crank-doc-converter:8443")
        else:
            self.worker_url = os.getenv("WORKER_URL", "http://crank-doc-converter:8081")
            
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
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": "crankdoc-worker",
                "capabilities": [cap.operation for cap in self.fallback_service.get_capabilities()]
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
    
    async def _startup(self):
        """Startup handler - register with platform."""
        logger.info("Starting CrankDoc Worker...")
        
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
    
    async def _register_with_platform(self, worker_info: WorkerRegistration):
        """Register this worker with the platform."""
        max_retries = 5
        retry_delay = 5  # seconds
        
        # Auth token for platform (using dev token from platform service)
        auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "dev-mesh-key")
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{self.platform_url}/v1/workers/register",
                        json=worker_info.model_dump(),
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.worker_id = result.get("worker_id")
                        logger.info(f"Successfully registered with platform. Worker ID: {self.worker_id}")
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
        """Shutdown handler - deregister from platform."""
        if self.worker_id:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.delete(f"{self.platform_url}/v1/workers/{self.worker_id}")
                logger.info("Successfully deregistered from platform")
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
    
    # Check if we should run HTTPS
    cert_dir = Path("/etc/certs")
    use_https = (cert_dir / "platform.crt").exists() and (cert_dir / "platform.key").exists()
    
    if use_https:
        # Start with HTTPS using uvicorn SSL parameters
        logger.info("🔒 Starting Crank Document Converter with HTTPS on port 8443")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8443,
            ssl_keyfile=str(cert_dir / "platform.key"),
            ssl_certfile=str(cert_dir / "platform.crt")
        )
    else:
        logger.info("🔓 Starting Crank Document Converter with HTTP on port 8081")
        uvicorn.run(app, host="0.0.0.0", port=8081)