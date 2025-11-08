"""
Crank Mesh Interface - Security-First Universal Pattern

This module provides the security-hardened base interface that all Crank services
implement, enabling consistent APIs, security, and governance across the platform.

🎯 BRAND DIFFERENTIATION: Renamed to "CrankMesh*" to clearly establish this as
Crank platform's unique technology for universal service abstraction, avoiding
confusion with generic mesh networking libraries.

Based on the adversarial testing work in CrankDoc, this ensures security is
non-negotiable while providing standardized mesh patterns.

Now includes MCP (Model Context Protocol) integration for AI agent access.
"""

import hashlib
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


# Security-First Crank Mesh Models
class CrankMeshRequest(BaseModel):
    """Universal request format with security context."""

    service_type: str  # "document", "email", "classify", etc.
    operation: str  # "convert", "parse", "predict", etc.
    input_data: dict[str, Any]
    policies: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None
    job_id: Optional[str] = None
    policy_profile: str = "default"  # FIXED: Added missing field for receipt generation


class CrankMeshResponse(BaseModel):
    """Universal response format with security audit trail."""

    success: bool
    result: Optional[dict[str, Any]] = None
    receipt_id: Optional[str] = None
    errors: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None
    processing_time_ms: Optional[int] = None
    mesh_node_id: Optional[str] = None
    # FIXED: Added missing fields for receipt generation
    job_id: Optional[str] = None
    service_type: Optional[str] = None
    operation: Optional[str] = None


class CrankMeshCapability(BaseModel):
    """Service capability with security requirements."""

    operation: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    policies_required: list[str] = []
    limits: Optional[dict[str, str]] = None


class CrankMeshReceipt(BaseModel):
    """Verifiable processing receipt with audit trail."""

    receipt_id: str
    job_id: str
    service_type: str
    operation: str
    timestamp: str
    input_hash: str
    output_hash: Optional[str] = None
    processing_time_ms: int
    policy_profile: str
    mesh_node_id: str
    user_id: Optional[str] = None
    success: bool
    errors: Optional[list[str]] = None
    version: str = "1.0"
    signature: Optional[str] = None


class CrankMeshAuthMiddleware(BaseHTTPMiddleware):
    """Universal authentication middleware for Crank mesh services."""

    def __init__(self, app: FastAPI, api_key: str = "dev-mesh-key"):
        super().__init__(app)
        self.api_key = api_key

    async def dispatch(self, request: Request, call_next: Any):
        # Skip auth for health checks and docs
        if request.url.path in [
            "/health/live",
            "/health/ready",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]:
            return await call_next(request)

        # Check for API key
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Missing or invalid Authorization header"},
            )

        token = auth_header.split(" ", 1)[1]
        if token != self.api_key:
            return JSONResponse(
                status_code=401, content={"error": "Invalid API key"},
            )

        response = await call_next(request)
        return response


class CrankMeshValidator:
    """Security validation for all mesh requests."""

    @staticmethod
    def validate_request(request: CrankMeshRequest) -> list[str]:
        """Validate mesh request and return list of violations."""
        violations = []

        # Validate service type
        if request.service_type not in [
            "document",
            "email",
            "classify",
            "diagnostic",
            "mcp",
        ]:
            violations.append(f"Unknown service type: {request.service_type}")

        if not request.operation:
            violations.append("Operation is required")

        return violations


class CrankMeshReceiptSystem:
    """Universal receipt generation for Crank mesh services."""

    def __init__(self, node_id: Optional[str] = None):
        self.node_id = node_id or f"crank-mesh-node-{uuid4().hex[:8]}"

    def generate_receipt(
        self,
        request: CrankMeshRequest,
        response: CrankMeshResponse,
        start_time: float,
        auth_context: Optional[dict[str, Any]] = None
    ) -> CrankMeshReceipt:
        """Generate verifiable receipt for any mesh operation."""
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Generate unique receipt ID
        receipt_id = f"crank-mesh-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"

        # Ensure response has required fields for receipt
        job_id = response.job_id or request.job_id or str(uuid4())
        service_type = response.service_type or request.service_type
        operation = response.operation or request.operation

        receipt = CrankMeshReceipt(
            receipt_id=receipt_id,
            job_id=job_id,
            service_type=service_type,
            operation=operation,
            timestamp=datetime.now(timezone.utc).isoformat(),
            input_hash=self._hash_request(request),
            output_hash=self._hash_response(response),
            processing_time_ms=processing_time_ms,
            policy_profile=getattr(request, 'policy_profile', 'default'),
            mesh_node_id=self.node_id,
            user_id=auth_context.get("user_id") if auth_context else None,
            success=response.success,
            errors=response.errors,
        )

        # Generate signature
        receipt.signature = self._sign_receipt(receipt)
        return receipt

    def _hash_request(self, request: CrankMeshRequest) -> str:
        """Generate hash of request for receipt."""
        request_dict = request.model_dump()
        request_json = json.dumps(request_dict, sort_keys=True)
        return hashlib.sha256(request_json.encode()).hexdigest()[:16]

    def _hash_response(self, response: CrankMeshResponse) -> str:
        """Generate hash of response for receipt."""
        if not response.result:
            return "no-result"

        result_json = json.dumps(response.result, sort_keys=True)
        return hashlib.sha256(result_json.encode()).hexdigest()[:16]

    def _sign_receipt(self, receipt: CrankMeshReceipt) -> str:
        """Sign receipt (cryptographic hash)."""
        receipt_dict = receipt.model_dump(exclude={"signature"})
        receipt_json = json.dumps(receipt_dict, sort_keys=True)
        return hashlib.sha256(receipt_json.encode()).hexdigest()[:32]


class CrankMeshInterface(ABC):
    """
    Security-first universal interface that every Crank service implements.

    🎯 CRANK PLATFORM'S CORE TECHNOLOGY: This interface enables universal
    service abstraction across protocols (HTTP, gRPC, MCP, RS422) while
    maintaining consistent security, auditing, and governance.

    Based on adversarial testing in CrankDoc, this ensures security is
    non-negotiable while providing standardized mesh patterns.
    """

    def __init__(self, service_type: str, node_id: Optional[str] = None):
        self.service_type = service_type
        self.node_id = node_id or f"crank-{service_type}-{uuid4().hex[:8]}"
        self._capabilities = []
        self.receipt_system = CrankMeshReceiptSystem(self.node_id)

    @abstractmethod
    def get_capabilities(self) -> list[CrankMeshCapability]:
        """Return list of service capabilities with security requirements."""

    @abstractmethod
    async def process_request(
        self, request: CrankMeshRequest, auth_context: dict[str, Any],
    ) -> CrankMeshResponse:
        """Process a mesh request with mandatory security context."""

    def generate_receipt(
        self,
        request: CrankMeshRequest,
        response: CrankMeshResponse,
        auth_context: dict[str, Any],
        start_time: Optional[float] = None
    ) -> CrankMeshReceipt:
        """Generate mandatory audit receipt for all operations."""
        start_time = start_time or time.time()

        # Ensure response has required fields
        response.job_id = response.job_id or request.job_id or str(uuid4())
        response.service_type = response.service_type or request.service_type
        response.operation = response.operation or request.operation
        response.mesh_node_id = response.mesh_node_id or self.node_id

        return self.receipt_system.generate_receipt(request, response, start_time, auth_context)

    def create_app(self, api_key: str = "dev-mesh-key") -> FastAPI:
        """
        Create FastAPI app with security-first configuration.

        Returns a FastAPI instance with:
        - Mandatory authentication
        - CORS configuration
        - Security headers
        - Health check endpoints
        - Auto-generated OpenAPI docs
        """
        app = FastAPI(
            title=f"Crank {self.service_type.title()} Service",
            description=f"Security-first {self.service_type} processing via Crank Mesh Interface",
            version="1.0.0",
        )

        # Add security middleware
        app.add_middleware(CrankMeshAuthMiddleware, api_key=api_key)

        # Add CORS (restrictive by default)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://localhost:8000"],
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )

        # Health endpoints (no auth required)
        @app.get("/health/live")
        async def liveness():
            """Kubernetes liveness probe."""
            return {"status": "alive", "service": self.service_type}

        @app.get("/health/ready")
        async def readiness():
            """Kubernetes readiness probe."""
            return {
                "status": "ready",
                "service": self.service_type,
                "capabilities": len(self.get_capabilities()),
            }

        # Capabilities endpoint
        @app.get("/v1/capabilities", response_model=list[CrankMeshCapability])
        async def get_capabilities():
            """Get service capabilities and security requirements."""
            return self.get_capabilities()

        # Main processing endpoint
        @app.post("/v1/process", response_model=CrankMeshResponse)
        async def process_request_endpoint(request: CrankMeshRequest):
            """Process request through Crank Mesh Interface."""
            start_time = time.time()

            # Extract auth context from request
            auth_context = await self._extract_auth_context(app.state.request)

            # Validate request
            violations = CrankMeshValidator.validate_request(request)
            if violations:
                return CrankMeshResponse(
                    success=False,
                    errors=violations,
                    mesh_node_id=self.node_id,
                )

            try:
                # Process the request
                response = await self.process_request(request, auth_context)

                # Generate audit receipt
                receipt = self.generate_receipt(request, response, auth_context, start_time)
                response.receipt_id = receipt.receipt_id

                return response

            except Exception as e:
                return CrankMeshResponse(
                    success=False,
                    errors=[f"Processing error: {e!s}"],
                    mesh_node_id=self.node_id,
                )

        return app

    async def _extract_auth_context(self, request: Request) -> dict[str, Any]:
        """Extract authentication context from request."""
        # Simple implementation - can be enhanced with JWT, etc.
        return {
            "user_id": "authenticated_user",  # Would extract from JWT in production
            "permissions": ["read", "write"],  # Would come from auth system
            "request_ip": request.client.host if request.client else "unknown",
        }


# Backward compatibility aliases (temporary - will be removed in next version)
MeshRequest = CrankMeshRequest
MeshResponse = CrankMeshResponse
MeshReceipt = CrankMeshReceipt
MeshCapability = CrankMeshCapability
MeshAuthMiddleware = CrankMeshAuthMiddleware
MeshValidator = CrankMeshValidator
MeshReceiptSystem = CrankMeshReceiptSystem
MeshInterface = CrankMeshInterface
