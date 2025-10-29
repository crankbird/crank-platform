"""
Crank Mesh Interface - Security-First Universal Pattern

This module provides the security-hardened base interface that all Crank services 
implement, enabling consistent APIs, security, and governance across the platform.

Based on the adversarial testing work in CrankDoc, this ensures security is 
non-negotiable while providing standardized mesh patterns.

Now includes MCP (Model Context Protocol) integration for AI agent access.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from dataclasses import dataclass
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


# Security-First Mesh Models
class MeshRequest(BaseModel):
    """Universal request format with security context."""
    service_type: str  # "document", "email", "classify", etc.
    operation: str     # "convert", "parse", "predict", etc.
    input_data: Dict[str, Any]
    policies: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = None


class MeshResponse(BaseModel):
    """Universal response format with security audit trail."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    receipt_id: Optional[str] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[int] = None
    mesh_node_id: Optional[str] = None


class MeshCapability(BaseModel):
    """Service capability with security requirements."""
    operation: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    policies_required: List[str] = []
    limits: Optional[Dict[str, str]] = None


@dataclass
class MeshReceipt:
    """Security audit receipt for all mesh operations."""
    receipt_id: str
    timestamp: datetime
    service_type: str
    operation: str
    user_id: str
    success: bool
    input_hash: str
    output_hash: Optional[str] = None
    errors: Optional[List[str]] = None
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


class MeshInterface(ABC):
    """
    Security-first universal interface that every Crank service implements.
    
    Based on adversarial testing in CrankDoc, this ensures security is 
    non-negotiable while providing standardized mesh patterns.
    """
    
    def __init__(self, service_type: str, node_id: str = None):
        self.service_type = service_type
        self.node_id = node_id or f"{service_type}-{uuid4().hex[:8]}"
        self._capabilities = []
    
    @abstractmethod
    def get_capabilities(self) -> List[MeshCapability]:
        """Return list of service capabilities with security requirements."""
        pass
    
    @abstractmethod
    async def process_request(self, request: MeshRequest, auth_context: Dict[str, Any]) -> MeshResponse:
        """Process a mesh request with mandatory security context."""
        pass
    
    def generate_receipt(self, request: MeshRequest, response: MeshResponse, auth_context: Dict[str, Any]) -> MeshReceipt:
        """Generate mandatory audit receipt for all operations."""
        return MeshReceipt(
            receipt_id=f"mesh_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(request.input_data))%10000:04d}",
            timestamp=datetime.now(),
            service_type=self.service_type,
            operation=request.operation,
            user_id=auth_context.get("user_id", "unknown"),
            success=response.success,
            input_hash=str(hash(json.dumps(request.input_data, sort_keys=True))),
            output_hash=str(hash(json.dumps(response.result, sort_keys=True))) if response.result else None,
            errors=response.errors
        )
    
    def create_app(self, api_key: str = "dev-mesh-key") -> FastAPI:
        """
        Create FastAPI app with security-first configuration.
        
        This mirrors the proven security patterns from CrankDoc.
        """
        app = FastAPI(
            title=f"Crank{self.service_type.title()} Mesh Service",
            description=f"Security-hardened {self.service_type} processing service",
            version="1.0.0"
        )
        
        # Security-first CORS configuration (no wildcards)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://localhost:8080"],
            allow_credentials=True,
            allow_methods=["GET", "POST"],  # Only required methods
            allow_headers=["Authorization", "Content-Type"],  # Only required headers
        )
        
        # Mandatory authentication middleware
        app.add_middleware(MeshAuthMiddleware, api_key=api_key)
        
        # Standard mesh routes with security
        self._add_mesh_routes(app)
        
        return app
    
    def _add_mesh_routes(self, app: FastAPI):
        """Add standardized mesh routes with security."""
        
        @app.get("/v1/capabilities")
        async def get_capabilities(auth_context: dict = Depends(self._get_auth_context)):
            """Get service capabilities (secured)."""
            return self.get_capabilities()
        
        @app.post("/v1/process")
        async def process_mesh_request(
            request: MeshRequest,
            auth_context: dict = Depends(self._get_auth_context)
        ):
            """Process mesh request (secured)."""
            start_time = time.time()
            
            try:
                response = await self.process_request(request, auth_context)
                response.processing_time_ms = int((time.time() - start_time) * 1000)
                response.mesh_node_id = self.node_id
                
                # Generate audit receipt
                receipt = self.generate_receipt(request, response, auth_context)
                response.receipt_id = receipt.receipt_id
                
                return response
                
            except Exception as e:
                return MeshResponse(
                    success=False,
                    errors=[str(e)],
                    metadata={"user_id": auth_context.get("user_id", "unknown")},
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    mesh_node_id=self.node_id
                )
        
        @app.get("/v1/receipts/{receipt_id}")
        async def get_receipt(
            receipt_id: str,
            auth_context: dict = Depends(self._get_auth_context)
        ):
            """Get audit receipt (secured)."""
            return {
                "receipt_id": receipt_id,
                "status": "found",
                "user_id": auth_context.get("user_id", "unknown")
            }
        
        # Health checks (unsecured, like proven in CrankDoc)
        @app.get("/health/live")
        async def health_live():
            return {"status": "live", "service": f"crank{self.service_type}-mesh"}
        
        @app.get("/health/ready") 
        async def health_ready():
            return {"status": "ready", "service": f"crank{self.service_type}-mesh"}
        
        @app.get("/health/startup")
        async def health_startup():
            return {"status": "started", "service": f"crank{self.service_type}-mesh"}
            
        # MCP endpoint for agent integration
        @app.post("/mcp")
        async def mcp_endpoint(message: dict):
            """Handle MCP protocol messages for agent integration."""
            try:
                # Import here to avoid circular imports
                from mcp_interface import MCPMeshAdapter
                
                # Create adapter and register this service
                adapter = MCPMeshAdapter()
                adapter.server.register_mesh_service(self)
                
                # Handle the MCP message
                return await adapter.handle_mcp_message(message)
                
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -1,
                        "message": f"MCP handling error: {str(e)}"
                    }
                }
        
        @app.get("/mcp/tools")
        async def mcp_tools():
            """List available MCP tools for this service."""
            try:
                from mcp_interface import MCPMeshServer
                
                server = MCPMeshServer()
                server.register_mesh_service(self)
                
                return {
                    "tools": server.list_tools(),
                    "server_info": server.get_mcp_server_info()
                }
                
            except Exception as e:
                return {"error": f"Failed to list MCP tools: {str(e)}"}
    
    def _get_auth_context(self, request: Request) -> dict:
        """Extract authentication context from request."""
        # This would integrate with the proven auth patterns from CrankDoc
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]
            user_id = f"user_{hash(api_key) % 10000}"
            return {
                "authenticated": True,
                "api_key": api_key,
                "user_id": user_id
            }
        return {
            "authenticated": False,
            "api_key": "",
            "user_id": "anonymous"
        }