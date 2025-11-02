#!/usr/bin/env python3
"""
Crank Document Converter Service - REFACTORED with Worker Certificate Library

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

# Import worker certificate library
from worker_cert_pattern import WorkerCertificatePattern, create_worker_fastapi_with_certs

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
        'docx': ['docx'],
        'html': ['html'],
        'markdown': ['md'],
        'latex': ['tex'],
        'rst': ['rst'],
        'odt': ['odt'],
        'txt': ['txt']
    }
    
    LIBREOFFICE_FORMATS = {
        # LibreOffice supported formats
        'doc': ['doc'],
        'docx': ['docx'],
        'odt': ['odt'],
        'pdf': ['pdf'],
        'rtf': ['rtf'],
        'xls': ['xls'],
        'xlsx': ['xlsx'],
        'ods': ['ods'],
        'ppt': ['ppt'],
        'pptx': ['pptx'],
        'odp': ['odp']
    }
    
    def __init__(self):
        """Initialize the document converter."""
        self.temp_dir = Path(tempfile.gettempdir()) / "crank_converter"
        self.temp_dir.mkdir(exist_ok=True)
        
    def get_capabilities(self) -> List[Dict[str, Any]]:
        """Get supported conversion capabilities."""
        capabilities = []
        
        # Pandoc capabilities
        for input_format, extensions in self.PANDOC_FORMATS.items():
            for output_format in self.PANDOC_FORMATS.keys():
                if input_format != output_format:
                    capabilities.append({
                        "converter": "pandoc",
                        "from": input_format,
                        "to": output_format,
                        "extensions": extensions
                    })
        
        # LibreOffice capabilities
        for input_format, extensions in self.LIBREOFFICE_FORMATS.items():
            for output_format in self.LIBREOFFICE_FORMATS.keys():
                if input_format != output_format:
                    capabilities.append({
                        "converter": "libreoffice",
                        "from": input_format,
                        "to": output_format,
                        "extensions": extensions
                    })
        
        return capabilities
    
    def convert_document(self, input_data: bytes, input_format: str, 
                        output_format: str, filename: str = None) -> bytes:
        """Convert document from one format to another."""
        
        # Create unique temp files
        job_id = uuid4().hex[:8]
        input_file = self.temp_dir / f"{job_id}_input.{input_format}"
        output_file = self.temp_dir / f"{job_id}_output.{output_format}"
        
        try:
            # Write input data
            input_file.write_bytes(input_data)
            
            # Try pandoc first
            if self._can_convert_with_pandoc(input_format, output_format):
                success = self._convert_with_pandoc(input_file, output_file, input_format, output_format)
                if success and output_file.exists():
                    return output_file.read_bytes()
            
            # Try LibreOffice as fallback
            if self._can_convert_with_libreoffice(input_format, output_format):
                success = self._convert_with_libreoffice(input_file, output_file, input_format, output_format)
                if success and output_file.exists():
                    return output_file.read_bytes()
            
            raise RuntimeError(f"Conversion from {input_format} to {output_format} failed")
            
        finally:
            # Cleanup temp files
            for file in [input_file, output_file]:
                if file.exists():
                    file.unlink()
    
    def _can_convert_with_pandoc(self, input_format: str, output_format: str) -> bool:
        """Check if pandoc can handle this conversion."""
        return (input_format in self.PANDOC_FORMATS and 
                output_format in self.PANDOC_FORMATS)
    
    def _can_convert_with_libreoffice(self, input_format: str, output_format: str) -> bool:
        """Check if LibreOffice can handle this conversion."""
        return (input_format in self.LIBREOFFICE_FORMATS and 
                output_format in self.LIBREOFFICE_FORMATS)
    
    def _convert_with_pandoc(self, input_file: Path, output_file: Path, 
                           input_format: str, output_format: str) -> bool:
        """Convert using pandoc."""
        try:
            cmd = [
                "pandoc",
                str(input_file),
                f"--from={input_format}",
                f"--to={output_format}",
                f"--output={output_file}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
            
        except Exception as e:
            logger.warning(f"Pandoc conversion failed: {e}")
            return False
    
    def _convert_with_libreoffice(self, input_file: Path, output_file: Path,
                                input_format: str, output_format: str) -> bool:
        """Convert using LibreOffice."""
        try:
            # LibreOffice headless conversion
            cmd = [
                "libreoffice",
                "--headless",
                "--convert-to", output_format,
                "--outdir", str(output_file.parent),
                str(input_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.returncode == 0
            
        except Exception as e:
            logger.warning(f"LibreOffice conversion failed: {e}")
            return False


# Pydantic models
class ConversionRequest(BaseModel):
    """Document conversion request."""
    input_format: str
    output_format: str
    filename: Optional[str] = None


class ConversionResponse(BaseModel):
    """Document conversion response."""
    success: bool
    job_id: str
    input_format: str
    output_format: str
    filename: Optional[str] = None
    size_bytes: int
    duration_ms: int
    metadata: Dict[str, Any]


class WorkerRegistration(BaseModel):
    """Worker registration model."""
    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: List[str]


def setup_doc_converter_routes(app: FastAPI, worker_config: dict):
    """Set up document converter routes using worker config."""
    
    # Get components from worker config
    cert_store = worker_config["cert_store"]
    platform_url = worker_config["platform_url"]
    worker_url = worker_config["worker_url"]
    service_name = worker_config["service_name"]
    
    # Initialize document converter
    converter = RealDocumentConverter()
    
    # Initialize CrankDoc mesh service for fallback
    fallback_service = CrankDocMeshService()
    
    # Worker registration state
    worker_id = None
    
    def _create_adaptive_client(timeout: float = 10.0) -> httpx.AsyncClient:
        """Create HTTP client using pre-loaded certificates."""
        if cert_store and cert_store.ca_cert:
            # Create temporary CA certificate for httpx to use
            with tempfile.NamedTemporaryFile(mode='w', suffix='.crt', delete=False) as ca_file:
                ca_file.write(cert_store.ca_cert)
                ca_file.flush()
                
                # Configure httpx to trust our CA certificate
                return httpx.AsyncClient(
                    verify=ca_file.name,
                    timeout=timeout
                )
        else:
            # Fallback for development - disable verification
            logger.warning("⚠️ No CA certificate available, using insecure client")
            return httpx.AsyncClient(verify=False, timeout=timeout)
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint with security status."""
        capabilities = converter.get_capabilities()
        security_status = {
            "ssl_enabled": cert_store.platform_cert is not None if cert_store else False,
            "ca_cert_available": cert_store.ca_cert is not None if cert_store else False,
            "certificate_source": "Worker Certificate Library"
        }
        
        return {
            "status": "healthy",
            "service": service_name,
            "capabilities": ["document_conversion", "pandoc_conversion", "libreoffice_conversion"],
            "supported_conversions": len(capabilities),
            "converters": ["pandoc", "libreoffice"],
            "security": security_status,
            "timestamp": datetime.now().isoformat()
        }
    
    @app.post("/convert", response_model=ConversionResponse)
    async def convert_document(
        file: UploadFile,
        output_format: str = Form(...),
        input_format: str = Form(None)
    ):
        """Convert uploaded document to specified format."""
        start_time = datetime.now()
        job_id = f"doc_{uuid4().hex[:8]}"
        
        try:
            # Read file data
            file_data = await file.read()
            
            # Determine input format from filename or explicit parameter
            if not input_format:
                input_format = Path(file.filename).suffix.lstrip('.').lower()
            
            if not input_format:
                raise HTTPException(status_code=400, detail="Cannot determine input format")
            
            # Perform conversion
            result_data = converter.convert_document(
                input_data=file_data,
                input_format=input_format,
                output_format=output_format,
                filename=file.filename
            )
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return ConversionResponse(
                success=True,
                job_id=job_id,
                input_format=input_format,
                output_format=output_format,
                filename=file.filename,
                size_bytes=len(result_data),
                duration_ms=duration_ms,
                metadata={
                    "original_size": len(file_data),
                    "compression_ratio": len(result_data) / len(file_data),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Document conversion error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/capabilities")
    async def get_capabilities():
        """Get worker capabilities."""
        capabilities = converter.get_capabilities()
        return {
            "capabilities": capabilities,
            "total_conversions": len(capabilities),
            "converters": ["pandoc", "libreoffice"]
        }
    
    @app.post("/mesh", response_model=MeshResponse)
    async def handle_mesh_request(request: MeshRequest):
        """Handle mesh requests for fallback compatibility."""
        try:
            return await fallback_service.process_request(request)
        except Exception as e:
            logger.error(f"Mesh request error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _startup():
        """Startup handler - register with platform."""
        nonlocal worker_id
        
        logger.info("🏗️ Starting Crank Document Converter...")
        logger.info("🔐 Using certificates loaded synchronously at startup")
        
        # Prepare registration info
        worker_info = WorkerRegistration(
            worker_id=f"doc-converter-{uuid4().hex[:8]}",
            service_type="document_conversion",
            endpoint=worker_url,
            health_url=f"{worker_url}/health",
            capabilities=["document_conversion", "pandoc_conversion", "libreoffice_conversion"]
        )
        
        # Register with platform
        await _register_with_platform(worker_info)
        worker_id = worker_info.worker_id
        
        # Start heartbeat background task
        _start_heartbeat_task()
    
    async def _register_with_platform(worker_info: WorkerRegistration):
        """Register this worker with the platform using mTLS."""
        max_retries = 5
        retry_delay = 5  # seconds
        
        # Auth token for platform
        auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "dev-mesh-key")
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        for attempt in range(max_retries):
            try:
                # Use mTLS client for secure communication
                async with _create_adaptive_client() as client:
                    response = await client.post(
                        f"{platform_url}/v1/workers/register",
                        json=worker_info.model_dump(),
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"🔒 Successfully registered doc converter via mTLS. Worker ID: {worker_info.worker_id}")
                        return
                    else:
                        logger.error(f"Registration failed: {response.status_code} - {response.text}")
                        
            except Exception as e:
                logger.warning(f"Registration attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying registration in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
        
        raise RuntimeError(f"Failed to register with platform after {max_retries} attempts")
    
    def _start_heartbeat_task():
        """Start the background heartbeat task."""
        async def heartbeat_task():
            while True:
                try:
                    await asyncio.sleep(20)  # 20 second heartbeat interval
                    await _send_heartbeat()
                except asyncio.CancelledError:
                    logger.info("Heartbeat task cancelled")
                    break
                except Exception as e:
                    logger.warning(f"Heartbeat failed: {e}")
        
        asyncio.create_task(heartbeat_task())
        logger.info("🫀 Started heartbeat task with 20s interval")
    
    async def _send_heartbeat():
        """Send heartbeat to platform."""
        if worker_id:
            try:
                async with _create_adaptive_client(timeout=5.0) as client:
                    response = await client.post(
                        f"{platform_url}/v1/workers/{worker_id}/heartbeat",
                        data={
                            "service_type": "document_conversion",
                            "load_score": 0.4  # Simulated load
                        },
                        headers={"Authorization": f"Bearer {os.getenv('PLATFORM_AUTH_TOKEN', 'dev-mesh-key')}"}
                    )
                    # Heartbeat success is logged at debug level to reduce noise
            except Exception as e:
                logger.debug(f"Heartbeat failed: {e}")
    
    async def _shutdown():
        """Shutdown handler - deregister from platform using mTLS."""
        if worker_id:
            try:
                async with _create_adaptive_client(timeout=5.0) as client:
                    await client.delete(f"{platform_url}/v1/workers/{worker_id}")
                logger.info("🔒 Successfully deregistered doc converter via mTLS")
            except Exception as e:
                logger.warning(f"Failed to deregister from platform: {e}")
    
    # Register startup/shutdown handlers
    app.add_event_handler("startup", _startup)
    app.add_event_handler("shutdown", _shutdown)


def create_crank_doc_converter(cert_store=None):
    """Create the Crank Document Converter application with optional certificate store."""
    # This is kept for backward compatibility but now uses the worker library pattern
    worker_config = {
        "app": FastAPI(title="Crank Document Converter", version="1.0.0"),
        "cert_store": cert_store,
        "platform_url": os.getenv("PLATFORM_URL", "https://platform:8443"),
        "worker_url": os.getenv("WORKER_URL", "https://crank-doc-converter:8101"),
        "service_name": "crank-doc-converter"
    }
    
    setup_doc_converter_routes(worker_config["app"], worker_config)
    return worker_config["app"]


def main():
    """Main entry point using Worker Certificate Library."""
    
    # Step 1: Initialize certificates SYNCHRONOUSLY using library
    cert_pattern = WorkerCertificatePattern("crank-doc-converter")
    cert_store = cert_pattern.initialize_certificates()
    
    # Step 2: Create FastAPI with pre-loaded certificates using library
    worker_config = create_worker_fastapi_with_certs(
        title="Crank Document Converter",
        service_name="crank-doc-converter",
        platform_url=None,  # Use default from environment
        worker_url=None,    # Use default from environment
        cert_store=cert_store
    )
    
    # Step 3: Setup document converter routes
    setup_doc_converter_routes(worker_config["app"], worker_config)
    
    # Step 4: Start server with certificates using library
    https_port = int(os.getenv("DOC_CONVERTER_HTTPS_PORT", "8101"))
    cert_pattern.start_server(worker_config["app"], port=https_port)


# For direct running
if __name__ == "__main__":
    main()