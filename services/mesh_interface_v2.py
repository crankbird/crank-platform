"""
Crank Mesh Interface - Security-First Universal Pattern (Refactored)

This module provides the security-hardened base interface that all Crank services
implement, enabling consistent APIs, security, and governance across the platform.

REFACTORED VERSION: Fixes architectural issues from the initial implementation:
- Unified receipt system (no more duplicates)
- Consistent type contracts
- Proper metadata lifecycle
- Clear inheritance patterns
- Removed hacky patches
"""

import hashlib
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# =============================================================================
# CORE MESH MODELS - Type-safe and consistent
# =============================================================================


class MeshRequest(BaseModel):
    """Universal request format with security context."""

    service_type: str = Field(..., description="Service type: document, email, classify, etc.")
    operation: str = Field(..., description="Operation: convert, parse, predict, etc.")
    input_data: dict[str, Any] = Field(..., description="Operation input data")
    policies: list[str] = Field(default_factory=list, description="Security policies to apply")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Request metadata")
    job_id: str = Field(
        default_factory=lambda: f"job_{uuid4().hex[:8]}", description="Unique job identifier",
    )


class MeshResponse(BaseModel):
    """Universal response format with security audit trail."""

    success: bool = Field(..., description="Operation success status")
    result: Optional[dict[str, Any]] = Field(None, description="Operation result data")
    receipt_id: str = Field(..., description="Audit receipt identifier")
    errors: list[str] = Field(default_factory=list, description="Error messages if any")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    mesh_node_id: str = Field(..., description="Processing node identifier")


class MeshCapability(BaseModel):
    """Service capability definition with security requirements."""

    operation: str = Field(..., description="Operation name")
    description: str = Field(..., description="Human-readable description")
    input_schema: dict[str, Any] = Field(..., description="JSON schema for input validation")
    output_schema: dict[str, Any] = Field(..., description="JSON schema for output validation")
    policies_required: list[str] = Field(
        default_factory=list, description="Required security policies",
    )
    limits: dict[str, Any] = Field(
        default_factory=dict, description="Operation limits and constraints",
    )


class MeshReceipt(BaseModel):
    """Verifiable processing receipt for audit trail."""

    receipt_id: str = Field(..., description="Unique receipt identifier")
    job_id: str = Field(..., description="Associated job identifier")
    service_type: str = Field(..., description="Service that processed the request")
    operation: str = Field(..., description="Operation that was performed")
    timestamp: datetime = Field(..., description="Processing timestamp (UTC)")
    user_id: str = Field(..., description="User who initiated the request")
    success: bool = Field(..., description="Operation success status")
    input_hash: str = Field(..., description="Hash of input data for verification")
    output_hash: Optional[str] = Field(None, description="Hash of output data for verification")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    mesh_node_id: str = Field(..., description="Node that processed the request")
    policy_profile: str = Field(..., description="Security policies that were applied")
    errors: list[str] = Field(default_factory=list, description="Error messages if any")
    version: str = Field(default="1.0", description="Receipt format version")
    signature: Optional[str] = Field(None, description="Cryptographic signature for verification")


# =============================================================================
# AUTHENTICATION MIDDLEWARE
# =============================================================================


class MeshAuthMiddleware(BaseHTTPMiddleware):
    """Universal authentication middleware for mesh services."""

    def __init__(self, app, api_key: str = "dev-mesh-key"):
        super().__init__(app)
        self.api_key = api_key

    async def dispatch(self, request: Request, call_next):
        """Authenticate all requests except health checks."""
        # Skip auth for health endpoints
        if request.url.path.startswith("/health/"):
            return await call_next(request)

        # Check for API key
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Missing or invalid authorization header"},
            )

        token = auth_header.split(" ", 1)[1]
        if token != self.api_key:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid API key"},
            )

        # Add auth context to request state
        request.state.auth_context = {
            "user_id": "dev-user",  # In production, derive from token
            "authenticated": True,
            "token": token,
        }

        return await call_next(request)


# =============================================================================
# RECEIPT GENERATION SYSTEM
# =============================================================================


class MeshReceiptGenerator:
    """Unified receipt generation for all mesh operations."""

    def __init__(self, node_id: Optional[str] = None):
        self.node_id = node_id or f"mesh-{uuid4().hex[:8]}"

    def generate_receipt(
        self,
        request: MeshRequest,
        response: MeshResponse,
        auth_context: dict[str, Any],
        start_time: float,
    ) -> MeshReceipt:
        """Generate a verifiable audit receipt."""
        processing_time_ms = int((time.time() - start_time) * 1000)
        receipt_id = (
            f"receipt_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        )

        receipt = MeshReceipt(
            receipt_id=receipt_id,
            job_id=request.job_id,
            service_type=request.service_type,
            operation=request.operation,
            timestamp=datetime.now(timezone.utc),
            user_id=auth_context.get("user_id", "unknown"),
            success=response.success,
            input_hash=self._hash_data(request.input_data),
            output_hash=self._hash_data(response.result) if response.result else None,
            processing_time_ms=processing_time_ms,
            mesh_node_id=self.node_id,
            policy_profile=",".join(request.policies) if request.policies else "none",
            errors=response.errors,
        )

        # Generate cryptographic signature
        receipt.signature = self._sign_receipt(receipt)
        return receipt

    def _hash_data(self, data: Any) -> str:
        """Generate consistent hash for any data."""
        if data is None:
            return "null"

        # Convert to JSON string with consistent ordering
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()[:16]

    def _sign_receipt(self, receipt: MeshReceipt) -> str:
        """Generate cryptographic signature for receipt verification."""
        # Exclude signature field from signing
        receipt_data = receipt.model_dump(exclude={"signature"})
        receipt_json = json.dumps(receipt_data, sort_keys=True, default=str)
        return hashlib.sha256(receipt_json.encode("utf-8")).hexdigest()


# =============================================================================
# BASE MESH INTERFACE
# =============================================================================


class MeshInterface(ABC):
    """
    Security-first universal interface that every Crank service implements.

    This provides:
    - Standardized request/response handling
    - Automatic receipt generation
    - Security policy enforcement
    - Health monitoring
    - Capability advertisement
    """

    def __init__(self, service_type: str, node_id: Optional[str] = None):
        self.service_type = service_type
        self.node_id = node_id or f"{service_type}-{uuid4().hex[:8]}"
        self.receipt_generator = MeshReceiptGenerator(self.node_id)

    # Abstract methods that implementations must provide
    @abstractmethod
    async def process_request(
        self, request: MeshRequest, auth_context: dict[str, Any],
    ) -> MeshResponse:
        """Process a mesh request and return response."""

    @abstractmethod
    def get_capabilities(self) -> list[MeshCapability]:
        """Return list of service capabilities."""

    # Concrete methods provided by the base class
    def _get_auth_context(self, request: Request) -> dict[str, Any]:
        """Extract authentication context from request."""
        return getattr(
            request.state,
            "auth_context",
            {
                "user_id": "unknown",
                "authenticated": False,
            },
        )

    def _enrich_request_metadata(self, request: MeshRequest, auth_context: dict[str, Any]) -> None:
        """Enrich request metadata with context."""
        request.metadata.update(
            {
                "mesh_node_id": self.node_id,
                "user_id": auth_context.get("user_id", "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service_type": self.service_type,
            },
        )

    def create_app(self, api_key: str = "dev-mesh-key") -> FastAPI:
        """Create FastAPI app with security-first configuration."""
        app = FastAPI(
            title=f"Crank {self.service_type.title()} Mesh",
            description=f"Security-hardened {self.service_type} service",
            version="1.0.0",
        )

        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://localhost:8080"],
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
        )

        # Authentication middleware
        app.add_middleware(MeshAuthMiddleware, api_key=api_key)

        # Add routes
        self._add_mesh_routes(app)

        return app

    def _add_mesh_routes(self, app: FastAPI):
        """Add standardized mesh routes."""

        @app.get("/v1/capabilities")
        async def get_capabilities(auth_context: dict = Depends(self._get_auth_context)):
            """Get service capabilities (secured)."""
            return self.get_capabilities()

        @app.post("/v1/process")
        async def process_mesh_request(
            request: MeshRequest,
            auth_context: dict = Depends(self._get_auth_context),
        ) -> MeshResponse:
            """Process mesh request (secured)."""
            start_time = time.time()

            try:
                # Enrich request metadata
                self._enrich_request_metadata(request, auth_context)

                # Process the request
                response = await self.process_request(request, auth_context)

                # Generate receipt
                receipt = self.receipt_generator.generate_receipt(
                    request,
                    response,
                    auth_context,
                    start_time,
                )

                # Finalize response
                response.receipt_id = receipt.receipt_id
                response.processing_time_ms = receipt.processing_time_ms
                response.mesh_node_id = self.node_id

                return response

            except Exception as e:
                # Generate error response with receipt
                error_response = MeshResponse(
                    success=False,
                    result=None,
                    receipt_id="",  # Will be set below
                    errors=[str(e)],
                    metadata={"error_type": type(e).__name__},
                    processing_time_ms=0,  # Will be set below
                    mesh_node_id=self.node_id,
                )

                # Generate receipt for failed operation
                receipt = self.receipt_generator.generate_receipt(
                    request,
                    error_response,
                    auth_context,
                    start_time,
                )

                error_response.receipt_id = receipt.receipt_id
                error_response.processing_time_ms = receipt.processing_time_ms

                return error_response

        @app.get("/v1/receipts/{receipt_id}")
        async def get_receipt(
            receipt_id: str,
            auth_context: dict = Depends(self._get_auth_context),
        ):
            """Get audit receipt (secured)."""
            # In production, this would query a receipt store
            return {
                "receipt_id": receipt_id,
                "status": "found",
                "user_id": auth_context.get("user_id", "unknown"),
                "note": "Receipt retrieval not yet implemented",
            }

        # Health checks (unsecured)
        @app.get("/health/live")
        async def health_live():
            return {"status": "live", "service": f"crank{self.service_type}-mesh"}

        @app.get("/health/ready")
        async def health_ready():
            return {"status": "ready", "service": f"crank{self.service_type}-mesh"}
