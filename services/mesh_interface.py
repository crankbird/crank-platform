"""
Crank Mesh Interface - Universal service pattern for The Mesh

This module provides the base interface that all Crank services implement,
enabling consistent APIs, security, and governance across the platform.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
import hashlib
import json
import time

from fastapi import FastAPI, HTTPException, UploadFile, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import httpx


class MeshRequest(BaseModel):
    """Universal request format for any mesh service."""
    job_id: Optional[str] = None
    service_type: str  # "document", "email", "classify", etc.
    operation: str     # "convert", "parse", "predict", etc.
    parameters: Dict[str, Any] = {}
    policy_profile: str = "default"


class MeshResponse(BaseModel):
    """Universal response format for any mesh service."""
    job_id: str
    service_type: str
    operation: str
    status: str  # "accepted", "processing", "completed", "failed"
    result: Optional[Dict[str, Any]] = None
    receipt_hash: Optional[str] = None
    processing_time_ms: Optional[int] = None
    mesh_node_id: Optional[str] = None


class MeshCapabilities(BaseModel):
    """Service capability description."""
    service_type: str
    operations: List[str]
    supported_formats: Dict[str, List[str]]
    limits: Dict[str, str]
    health_status: str = "ready"


class MeshReceipt(BaseModel):
    """Verifiable processing receipt."""
    job_id: str
    service_type: str
    operation: str
    timestamp: str
    input_hash: str
    output_hash: Optional[str] = None
    processing_time_ms: int
    policy_profile: str
    mesh_node_id: str
    version: str = "1.0"
    signature: Optional[str] = None


class MeshAuthMiddleware(BaseHTTPMiddleware):
    """Universal authentication middleware for mesh services."""
    
    def __init__(self, app, api_key: str = "dev-mesh-key"):
        super().__init__(app)
        self.api_key = api_key
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for health checks and docs
        if request.url.path in ["/health/live", "/health/ready", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Check for API key
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Missing or invalid Authorization header"}
            )
        
        token = auth_header[7:]  # Remove "Bearer "
        if token != self.api_key:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid mesh authentication token"}
            )
        
        response = await call_next(request)
        return response


class MeshPolicyEngine:
    """Universal policy enforcement for mesh services."""
    
    def __init__(self, opa_url: str = "http://localhost:8181"):
        self.opa_url = opa_url
    
    async def evaluate_request(self, request: MeshRequest, user_context: dict) -> bool:
        """Evaluate if request is allowed by policy."""
        # For now, implement simple allow-all policy
        # TODO: Integrate with OPA for real policy evaluation
        return True
    
    def get_policy_violations(self, request: MeshRequest) -> List[str]:
        """Get list of policy violations for a request."""
        violations = []
        
        # Example policy checks
        if request.service_type not in ["document", "email", "classify"]:
            violations.append(f"Unknown service type: {request.service_type}")
        
        if not request.operation:
            violations.append("Operation is required")
        
        return violations


class MeshReceiptSystem:
    """Universal receipt generation for mesh services."""
    
    def __init__(self, node_id: str = None):
        self.node_id = node_id or f"mesh-node-{uuid4().hex[:8]}"
    
    def generate_receipt(self, request: MeshRequest, response: MeshResponse, 
                        start_time: float) -> MeshReceipt:
        """Generate verifiable receipt for any mesh operation."""
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        receipt = MeshReceipt(
            job_id=response.job_id,
            service_type=response.service_type,
            operation=response.operation,
            timestamp=datetime.utcnow().isoformat(),
            input_hash=self._hash_request(request),
            output_hash=self._hash_response(response),
            processing_time_ms=processing_time_ms,
            policy_profile=request.policy_profile,
            mesh_node_id=self.node_id
        )
        
        # Generate signature (simple hash for now)
        receipt.signature = self._sign_receipt(receipt)
        return receipt
    
    def _hash_request(self, request: MeshRequest) -> str:
        """Generate hash of request for receipt."""
        request_dict = request.model_dump()
        request_json = json.dumps(request_dict, sort_keys=True)
        return hashlib.sha256(request_json.encode()).hexdigest()[:16]
    
    def _hash_response(self, response: MeshResponse) -> str:
        """Generate hash of response for receipt."""
        if not response.result:
            return "no-result"
        
        result_json = json.dumps(response.result, sort_keys=True)
        return hashlib.sha256(result_json.encode()).hexdigest()[:16]
    
    def _sign_receipt(self, receipt: MeshReceipt) -> str:
        """Sign receipt (simple hash for now)."""
        receipt_dict = receipt.model_dump(exclude={"signature"})
        receipt_json = json.dumps(receipt_dict, sort_keys=True)
        return hashlib.sha256(receipt_json.encode()).hexdigest()[:32]


class MeshInterface:
    """Universal interface that every Crank service implements."""
    
    def __init__(self, service_type: str, node_id: str = None):
        self.service_type = service_type
        self.node_id = node_id or f"{service_type}-{uuid4().hex[:8]}"
        
        # Initialize components
        self.policy_engine = MeshPolicyEngine()
        self.receipt_system = MeshReceiptSystem(self.node_id)
        
        # Create FastAPI app
        self.app = FastAPI(
            title=f"Crank{service_type.title()} Mesh Service",
            description=f"Mesh-enabled {service_type} processing service",
            version="1.0.0"
        )
        
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_middleware(self):
        """Setup standard middleware for all mesh services."""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://localhost:8080"],
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
        )
        
        # Authentication middleware
        self.app.add_middleware(MeshAuthMiddleware)
    
    def _setup_routes(self):
        """Setup standard routes every mesh service provides."""
        
        @self.app.post("/v1/process", response_model=MeshResponse)
        async def process_request(
            request: MeshRequest,
            file: Optional[UploadFile] = None
        ) -> MeshResponse:
            start_time = time.time()
            
            # Validate request
            violations = self.policy_engine.get_policy_violations(request)
            if violations:
                raise HTTPException(
                    status_code=400,
                    detail=f"Policy violations: {', '.join(violations)}"
                )
            
            # Generate job ID if not provided
            job_id = request.job_id or str(uuid4())
            request.job_id = job_id
            
            try:
                # Process the request
                response = await self.handle_request(request, file)
                response.job_id = job_id
                response.service_type = self.service_type
                response.mesh_node_id = self.node_id
                response.processing_time_ms = int((time.time() - start_time) * 1000)
                
                # Generate receipt
                receipt = self.receipt_system.generate_receipt(request, response, start_time)
                response.receipt_hash = receipt.signature
                
                return response
                
            except Exception as e:
                return MeshResponse(
                    job_id=job_id,
                    service_type=self.service_type,
                    operation=request.operation,
                    status="failed",
                    result={"error": str(e)},
                    mesh_node_id=self.node_id,
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
        
        @self.app.get("/v1/capabilities", response_model=MeshCapabilities)
        async def get_capabilities():
            return await self.get_service_capabilities()
        
        @self.app.get("/v1/receipts/{job_id}", response_model=MeshReceipt)
        async def get_receipt(job_id: str):
            receipt = await self.get_processing_receipt(job_id)
            if not receipt:
                raise HTTPException(status_code=404, detail="Receipt not found")
            return receipt
        
        @self.app.get("/health/live")
        async def health_live():
            return {
                "status": "alive", 
                "service": self.service_type,
                "node_id": self.node_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.get("/health/ready")
        async def health_ready():
            readiness = await self.check_readiness()
            status_code = 200 if readiness.get("ready", False) else 503
            return JSONResponse(content=readiness, status_code=status_code)
    
    # Abstract methods each service implements
    async def handle_request(self, request: MeshRequest, file: Optional[UploadFile]) -> MeshResponse:
        """Handle the actual service request. Must be implemented by each service."""
        raise NotImplementedError(f"Service {self.service_type} must implement handle_request")
    
    async def get_service_capabilities(self) -> MeshCapabilities:
        """Return service capabilities. Must be implemented by each service."""
        raise NotImplementedError(f"Service {self.service_type} must implement get_service_capabilities")
    
    async def get_processing_receipt(self, job_id: str) -> Optional[MeshReceipt]:
        """Get processing receipt for a job. Must be implemented by each service."""
        raise NotImplementedError(f"Service {self.service_type} must implement get_processing_receipt")
    
    async def check_readiness(self) -> Dict[str, Any]:
        """Check if service is ready to handle requests. Must be implemented by each service."""
        raise NotImplementedError(f"Service {self.service_type} must implement check_readiness")


# Utility function for creating mesh services
def create_mesh_service(service_type: str, implementation_class) -> FastAPI:
    """Create a mesh service with the given implementation."""
    service = implementation_class(service_type)
    return service.app