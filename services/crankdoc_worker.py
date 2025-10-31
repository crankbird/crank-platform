"""
CrankDoc Worker Service

Independent worker service that registers with the platform and provides
document processing capabilities. Part of the platform + worker architecture.
"""

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from uuid import uuid4

import httpx
from fastapi import FastAPI, UploadFile, HTTPException, Form
from pydantic import BaseModel

# Import existing CrankDoc mesh service for business logic
from crankdoc_mesh_minimal import CrankDocMeshService
from crankdoc_mesh_minimal import MeshRequest, MeshResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerRegistration(BaseModel):
    """Worker registration request matching platform expectations."""
    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: List[str]


class CrankDocWorker:
    """CrankDoc Worker Service that registers with platform."""
    
    def __init__(self, platform_url: str = None):
        self.app = FastAPI(title="CrankDoc Worker", version="1.0.0")
        self.platform_url = platform_url or os.getenv("PLATFORM_URL", "http://platform:8080")
        self.worker_url = os.getenv("WORKER_URL", "http://crankdoc-worker:8081")
        self.worker_id = None
        
        # Initialize CrankDoc business logic
        self.crankdoc_service = CrankDocMeshService()
        
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
                "capabilities": [cap.operation for cap in self.crankdoc_service.get_capabilities()]
            }
        
        @self.app.post("/convert")
        async def convert_document(
            file: UploadFile,
            source_format: str = Form("auto"),
            target_format: str = Form(...),
            options: Optional[Dict[str, Any]] = None
        ):
            """Convert document between formats."""
            try:
                # Read file content
                content = await file.read()
                
                # Create mesh request
                request_data = {
                    "file": content,
                    "source_format": source_format,
                    "target_format": target_format,
                    "options": options or {}
                }
                
                mesh_request = MeshRequest(
                    operation="convert",
                    data=request_data,
                    metadata={"filename": file.filename}
                )
                
                # Process with CrankDoc service
                response = await self.crankdoc_service.process(mesh_request)
                
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
            capabilities = self.crankdoc_service.get_capabilities()
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
        capabilities = self.crankdoc_service.get_capabilities()
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


def create_crankdoc_worker(platform_url: str = None) -> FastAPI:
    """Create CrankDoc worker application."""
    worker = CrankDocWorker(platform_url)
    return worker.app


# For direct running
if __name__ == "__main__":
    import uvicorn
    app = create_crankdoc_worker()
    uvicorn.run(app, host="0.0.0.0", port=8081)