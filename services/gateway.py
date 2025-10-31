"""
Crank Platform Gateway - Unified service gateway for all mesh services

This provides a single entry point that can route requests to different
mesh services based on the service_type parameter.
"""

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx

from .mesh_interface import MeshRequest, MeshResponse, MeshCapability


class CrankPlatformGateway:
    """Unified gateway for all Crank mesh services."""
    
    def __init__(self):
        self.app = FastAPI(
            title="Crank Platform Gateway",
            description="Unified gateway for all Crank mesh services",
            version="1.0.0"
        )
        
        # Service registry - maps service types to their endpoints
        self.services = {
            "document": "http://localhost:8000",  # CrankDoc service
            "email": "http://localhost:8001",     # CrankEmail service
        }
        
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_middleware(self):
        """Setup middleware for the gateway."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://localhost:8080"],
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
        )
    
    def _setup_routes(self):
        """Setup gateway routes."""
        
        @self.app.post("/v1/process", response_model=MeshResponse)
        async def process_request(
            service_type: str = Form(...),
            operation: str = Form(...),
            job_id: Optional[str] = Form(None),
            policy_profile: str = Form("default"),
            parameters: str = Form("{}"),  # JSON string
            file: Optional[UploadFile] = File(None)
        ) -> MeshResponse:
            """Route processing requests to appropriate service."""
            
            # Validate service type
            if service_type not in self.services:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown service type: {service_type}. Available: {list(self.services.keys())}"
                )
            
            # Parse parameters JSON
            try:
                import json
                params = json.loads(parameters) if parameters != "{}" else {}
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid parameters JSON"
                )
            
            # Create mesh request
            mesh_request = MeshRequest(
                job_id=job_id,
                service_type=service_type,
                operation=operation,
                parameters=params,
                policy_profile=policy_profile
            )
            
            # Route to appropriate service
            service_url = self.services[service_type]
            return await self._forward_request(service_url, mesh_request, file)
        
        @self.app.get("/v1/capabilities")
        async def get_all_capabilities():
            """Get capabilities from all registered services."""
            all_capabilities = {}
            
            for service_type, service_url in self.services.items():
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{service_url}/v1/capabilities")
                        if response.status_code == 200:
                            all_capabilities[service_type] = response.json()
                        else:
                            all_capabilities[service_type] = {"error": "Service unavailable"}
                except Exception as e:
                    all_capabilities[service_type] = {"error": str(e)}
            
            return {
                "gateway_version": "1.0.0",
                "available_services": list(self.services.keys()),
                "service_capabilities": all_capabilities
            }
        
        @self.app.get("/v1/capabilities/{service_type}")
        async def get_service_capabilities(service_type: str):
            """Get capabilities for a specific service."""
            if service_type not in self.services:
                raise HTTPException(
                    status_code=404,
                    detail=f"Service type not found: {service_type}"
                )
            
            service_url = self.services[service_type]
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{service_url}/v1/capabilities")
                    if response.status_code == 200:
                        return response.json()
                    else:
                        raise HTTPException(
                            status_code=503,
                            detail=f"Service {service_type} is unavailable"
                        )
            except Exception as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to connect to {service_type} service: {str(e)}"
                )
        
        @self.app.get("/v1/receipts/{job_id}")
        async def get_receipt(job_id: str, service_type: Optional[str] = None):
            """Get processing receipt for a job."""
            if service_type:
                # Try specific service
                if service_type not in self.services:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Service type not found: {service_type}"
                    )
                
                service_url = self.services[service_type]
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{service_url}/v1/receipts/{job_id}")
                        if response.status_code == 200:
                            return response.json()
                        elif response.status_code == 404:
                            raise HTTPException(status_code=404, detail="Receipt not found")
                        else:
                            raise HTTPException(status_code=503, detail="Service unavailable")
                except Exception as e:
                    raise HTTPException(status_code=503, detail=str(e))
            else:
                # Try all services
                for svc_type, service_url in self.services.items():
                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.get(f"{service_url}/v1/receipts/{job_id}")
                            if response.status_code == 200:
                                return response.json()
                    except:
                        continue
                
                raise HTTPException(status_code=404, detail="Receipt not found in any service")
        
        @self.app.get("/health/live")
        async def health_live():
            """Gateway health check."""
            return {
                "status": "alive",
                "gateway": "crank-platform",
                "services": list(self.services.keys())
            }
        
        @self.app.get("/health/ready")
        async def health_ready():
            """Check if gateway and all services are ready."""
            service_health = {}
            all_ready = True
            
            for service_type, service_url in self.services.items():
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(f"{service_url}/health/ready")
                        if response.status_code == 200:
                            service_health[service_type] = "ready"
                        else:
                            service_health[service_type] = "not_ready"
                            all_ready = False
                except Exception as e:
                    service_health[service_type] = f"error: {str(e)}"
                    all_ready = False
            
            status_code = 200 if all_ready else 503
            return JSONResponse(
                content={
                    "ready": all_ready,
                    "gateway": "ready",
                    "services": service_health
                },
                status_code=status_code
            )
        
        @self.app.get("/")
        async def root():
            """Gateway information."""
            return {
                "name": "Crank Platform Gateway",
                "version": "1.0.0",
                "description": "Unified gateway for all Crank mesh services",
                "available_services": list(self.services.keys()),
                "endpoints": {
                    "process": "/v1/process",
                    "capabilities": "/v1/capabilities",
                    "receipts": "/v1/receipts/{job_id}",
                    "health": "/health/ready"
                }
            }
    
    async def _forward_request(self, service_url: str, request: MeshRequest, 
                             file: Optional[UploadFile]) -> MeshResponse:
        """Forward request to the appropriate service."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Prepare the request
                data = {
                    "service_type": request.service_type,
                    "operation": request.operation,
                    "job_id": request.job_id,
                    "policy_profile": request.policy_profile,
                    "parameters": request.parameters
                }
                
                files = {}
                if file:
                    file_content = await file.read()
                    await file.seek(0)  # Reset file pointer
                    files["file"] = (file.filename, file_content, file.content_type)
                
                # Make request to service
                response = await client.post(
                    f"{service_url}/v1/process",
                    json=data if not files else None,
                    data=data if files else None,
                    files=files if files else None
                )
                
                if response.status_code == 200:
                    return MeshResponse(**response.json())
                else:
                    return MeshResponse(
                        job_id=request.job_id or "unknown",
                        service_type=request.service_type,
                        operation=request.operation,
                        status="failed",
                        result={"error": f"Service error: {response.text}"}
                    )
                    
        except Exception as e:
            return MeshResponse(
                job_id=request.job_id or "unknown",
                service_type=request.service_type,
                operation=request.operation,
                status="failed",
                result={"error": f"Gateway error: {str(e)}"}
            )


# Create the gateway app
def create_gateway() -> FastAPI:
    """Create the Crank Platform Gateway."""
    gateway = CrankPlatformGateway()
    return gateway.app


# Module-level app for uvicorn
app = create_gateway()


# For running directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)