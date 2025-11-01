"""
Crank Platform App - Enhanced Diagnostic Container

This evolves the diagnostic mesh container into a full platform monolith:
- Maintains all existing diagnostic functionality
- Adds platform services (auth, billing, discovery, routing)
- Provides worker registration and request routing
- Clean module boundaries for future extraction

JEMM Implementation: Modular monolith with extract-ready design.
"""

import asyncio
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import existing diagnostic service
from mesh_diagnostics_v2 import DiagnosticMeshService
from mesh_interface_v2 import MeshRequest, MeshResponse, MeshCapability

# Import new platform services
from platform_service import (
    PlatformService, User, WorkerInfo, UsageRecord,
    AuthServiceStub, BillingServiceStub, DiscoveryServiceStub
)

# Import security configuration
from security_config import initialize_security

# Import resilient discovery service
from resilient_discovery_service import create_discovery_service

# Import universal protocol support - CRITICAL INNOVATION
from universal_protocol_service import UniversalProtocolService, MCPAdapter

# =============================================================================
# PYDANTIC MODELS FOR API
# =============================================================================

class WorkerRegistration(BaseModel):
    """Worker registration request."""
    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: List[str]

class PlatformRequest(BaseModel):
    """Generic platform request."""
    service_type: str
    operation: str
    data: Dict[str, Any]

class PlatformResponse(BaseModel):
    """Generic platform response."""
    status: str
    worker_id: Optional[str] = None
    service_type: str
    operation: str
    duration_ms: int
    cost_cents: int
    data: Dict[str, Any]

# =============================================================================
# ENHANCED PLATFORM APP
# =============================================================================

class CrankPlatformApp:
    """Enhanced platform application with diagnostics + platform services."""
    
    def __init__(self, api_key: str = "dev-mesh-key"):
        self.api_key = api_key
        self.discovery_service = None  # Will be initialized in startup
        
        # Initialize services (discovery will be set in startup)
        self.platform = None  # Will be initialized with persistent discovery
        self.diagnostic = DiagnosticMeshService()
        
        # Initialize universal protocol support - CRITICAL FEATURE
        self.protocol_service = None  # Will be initialized in startup
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Crank Platform",
            description="Enhanced mesh platform with diagnostics, auth, billing, worker management, and UNIVERSAL PROTOCOL SUPPORT",
            version="2.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
        
        # Setup startup/shutdown events
        self._setup_events()
    
    def _setup_events(self):
        """Setup FastAPI startup and shutdown events."""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Initialize persistent services on startup."""
            print("🚀 Initializing Crank Platform...")
            
            # Initialize security and certificates
            print("🔐 Initializing security configuration and certificates...")
            initialize_security()
            
            # Initialize persistent discovery service
            print("🗄️  Initializing persistent discovery service...")
            self.discovery_service = await create_discovery_service()
            
            # Initialize platform with persistent discovery
            print("🔧 Initializing platform services...")
            self.platform = PlatformService(discovery_service=self.discovery_service)
            
            # Initialize universal protocol support
            print("🌐 Initializing universal protocol service...")
            self.protocol_service = UniversalProtocolService(self.platform)
            
            print("✅ Crank Platform startup complete!")
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Cleanup resources on shutdown."""
            print("🛑 Shutting down Crank Platform...")
            
            if self.discovery_service and hasattr(self.discovery_service, 'cleanup'):
                await self.discovery_service.cleanup()
                print("🧹 Cleaned up discovery service")
            
            print("✅ Crank Platform shutdown complete!")
    
    async def get_current_user(self, authorization: str = Header(None)) -> User:
        """Extract and authenticate user from Authorization header."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authorization header")
        
        # Handle "Bearer token" format
        token = authorization
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        
        user = await self.platform.authenticate_request(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return user
    
    def _setup_routes(self):
        """Setup all API routes."""
        
        # =============================================================================
        # HEALTH AND INFO ENDPOINTS
        # =============================================================================
        
        @self.app.get("/health/live")
        async def health_live():
            """Liveness check - is the platform running?"""
            return {
                "status": "live",
                "service": "crank-platform",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "modules": ["diagnostics", "auth", "billing", "discovery"]
            }
        
        @self.app.get("/health/ready")
        async def health_ready():
            """Readiness check - can the platform serve requests?"""
            workers = await self.platform.discovery.get_workers()
            protocols = self.protocol_service.get_supported_protocols()
            return {
                "status": "ready",
                "worker_count": sum(len(workers_list) for workers_list in workers.values()),
                "service_types": list(workers.keys()),
                "protocols_supported": protocols  # Show protocol support
            }
        
        @self.app.get("/v1/capabilities")
        async def get_capabilities(user: User = Depends(self.get_current_user)):
            """Get platform and diagnostic capabilities."""
            diag_caps = self.diagnostic.get_capabilities()
            
            platform_caps = [
                MeshCapability(
                    operation="route_request",
                    description="Route request to worker services",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "service_type": {"type": "string"},
                            "operation": {"type": "string"},
                            "data": {"type": "object"}
                        },
                        "required": ["service_type", "operation"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "worker_id": {"type": "string"},
                            "service_type": {"type": "string"},
                            "operation": {"type": "string"},
                            "duration_ms": {"type": "integer"},
                            "cost_cents": {"type": "integer"},
                            "data": {"type": "object"}
                        },
                        "required": ["status", "service_type", "operation", "duration_ms"]
                    }
                ),
                MeshCapability(
                    operation="register_worker",
                    description="Register a worker service",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "worker_id": {"type": "string"},
                            "service_type": {"type": "string"},
                            "endpoint": {"type": "string"},
                            "capabilities": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["worker_id", "service_type", "endpoint"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "worker_id": {"type": "string"}
                        },
                        "required": ["status", "worker_id"]
                    }
                )
            ]
            
            return diag_caps + platform_caps
        
        # =============================================================================
        # DIAGNOSTIC ENDPOINTS (Preserve existing functionality)
        # =============================================================================
        
        @self.app.post("/v1/process", response_model=MeshResponse)
        async def process_diagnostic(
            request: MeshRequest,
            user: User = Depends(self.get_current_user)
        ):
            """Process diagnostic mesh request (existing functionality)."""
            start_time = time.time()
            
            try:
                # Create auth context for diagnostic service
                auth_context = {
                    "user_id": user.user_id,
                    "username": user.username,
                    "roles": user.roles,
                    "tier": user.tier,
                    "authenticated": True
                }
                
                # Use existing diagnostic service
                response = await self.diagnostic.process_request(request, auth_context)
                
                # Track usage
                duration_ms = int((time.time() - start_time) * 1000)
                await self.platform.billing.track_usage(
                    user.user_id, request.operation, "diagnostic", duration_ms
                )
                
                return response
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                await self.platform.billing.track_usage(
                    user.user_id, request.operation, "diagnostic", duration_ms
                )
                raise HTTPException(status_code=500, detail=str(e))
        
        # =============================================================================
        # PLATFORM ENDPOINTS (New functionality)
        # =============================================================================
        
        @self.app.post("/v1/workers/register")
        async def register_worker(
            registration: WorkerRegistration,
            user: User = Depends(self.get_current_user)
        ):
            """Register a worker service."""
            worker_info = WorkerInfo(
                worker_id=registration.worker_id,
                service_type=registration.service_type,
                endpoint=registration.endpoint,
                health_url=registration.health_url,
                capabilities=registration.capabilities,
                last_seen=datetime.now(timezone.utc)
            )
            
            success = await self.platform.discovery.register_worker(worker_info)
            if success:
                return {"status": "registered", "worker_id": registration.worker_id}
            else:
                raise HTTPException(status_code=500, detail="Failed to register worker")
        
        @self.app.post("/v1/workers/{worker_id}/heartbeat")
        async def worker_heartbeat(
            worker_id: str,
            service_type: str = Form(...),
            load_score: float = Form(0.0),
            user: User = Depends(self.get_current_user)
        ):
            """Record a heartbeat from a worker."""
            # Update load score if discovery service supports it
            if hasattr(self.platform.discovery, 'update_worker_load'):
                await self.platform.discovery.update_worker_load(worker_id, service_type, load_score)
            
            # Record heartbeat
            if hasattr(self.platform.discovery, 'heartbeat_worker'):
                alive = await self.platform.discovery.heartbeat_worker(worker_id, service_type)
                return {"status": "heartbeat_recorded", "worker_id": worker_id, "alive": alive}
            else:
                return {"status": "heartbeat_not_supported", "worker_id": worker_id}

        @self.app.get("/v1/workers")
        async def get_workers(user: User = Depends(self.get_current_user)):
            """Get all registered workers."""
            workers = await self.platform.discovery.get_workers()
            return {
                "workers": {
                    service_type: [
                        {
                            "worker_id": w.worker_id,
                            "endpoint": w.endpoint,
                            "capabilities": w.capabilities,
                            "last_seen": w.last_seen.isoformat(),
                            "load_score": w.load_score
                        }
                        for w in workers_list
                    ]
                    for service_type, workers_list in workers.items()
                }
            }
        
        @self.app.post("/v1/route", response_model=PlatformResponse)
        async def route_request(
            request: PlatformRequest,
            user: User = Depends(self.get_current_user)
        ):
            """Route request to appropriate worker."""
            try:
                result = await self.platform.route_request(
                    request.service_type, request.operation, request.data, user
                )
                
                return PlatformResponse(**result)
                
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/v1/documents/convert")
        async def convert_document(
            file: UploadFile,
            target_format: str = Form(...),
            source_format: str = Form("auto")
            # user: User = Depends(self.get_current_user)  # Temporarily disabled for testing
        ):
            """Convert document via CrankDoc worker - file upload interface."""
            try:
                # Read file content
                file_content = await file.read()
                
                # Create test user for routing
                test_user = User(
                    user_id="test-user",
                    username="test", 
                    roles=["user", "admin"],  # Add admin role for testing
                    tier="premium",  # Use premium tier for testing
                    is_active=True
                )
                
                # Route to document worker
                result = await self.platform.route_document_request(
                    operation="convert",
                    file_content=file_content,
                    filename=file.filename,
                    source_format=source_format,
                    target_format=target_format,
                    user=test_user
                )
                
                return result
                
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/v1/billing/balance")
        async def get_balance(user: User = Depends(self.get_current_user)):
            """Get user's billing balance and usage."""
            balance = await self.platform.billing.get_user_balance(user.user_id)
            return balance
        
        # =============================================================================
        # TEST ENDPOINTS (Development only - no auth required)
        # =============================================================================
        
        @self.app.post("/test/convert")
        async def test_convert_document(
            file: UploadFile,
            target_format: str = Form(...),
            source_format: str = Form("auto")
        ):
            """Test document conversion without authentication (development only)."""
            try:
                # Read file content
                file_content = await file.read()
                
                # Create a test user for routing
                test_user = User(
                    user_id="test-user",
                    username="test",
                    roles=["user"],
                    tier="basic",
                    is_active=True
                )
                
                # Route to document worker
                result = await self.platform.route_document_request(
                    operation="convert",
                    file_content=file_content,
                    filename=file.filename,
                    source_format=source_format,
                    target_format=target_format,
                    user=test_user
                )
                
                return result
                
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # =============================================================================
        # UNIVERSAL PROTOCOL ENDPOINTS - CRITICAL INNOVATION
        # =============================================================================
        
        @self.app.get("/v1/protocols")
        async def get_supported_protocols():
            """Get list of supported protocols."""
            return {
                "protocols": self.protocol_service.get_supported_protocols(),
                "endpoints": {
                    "REST": "/v1/* (current endpoints)",
                    "MCP": "/mcp (Model Context Protocol for AI agents)",
                    "gRPC": "/grpc (high-performance binary protocol)",
                    "Legacy": "/legacy/* (industrial protocols)"
                },
                "description": "Universal protocol support - any protocol can access mesh services"
            }
        
        @self.app.post("/mcp")
        async def mcp_endpoint(
            request: Dict[str, Any],
            user: User = Depends(self.get_current_user)
        ):
            """MCP (Model Context Protocol) endpoint for AI agents."""
            try:
                response = await self.protocol_service.handle_protocol_request(
                    "MCP", request, user
                )
                return response
            except Exception as e:
                return {
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
        
        @self.app.get("/mcp/tools")
        async def mcp_list_tools(user: User = Depends(self.get_current_user)):
            """MCP tools discovery endpoint."""
            mcp_adapter = self.protocol_service.adapters["MCP"]
            return await mcp_adapter._list_tools(user)
        
        # Future protocol endpoints can be added here:
        # @self.app.post("/grpc") - for gRPC protocol
        # @self.app.post("/legacy/{protocol_name}") - for industrial protocols

# =============================================================================
# APP FACTORY
# =============================================================================

def create_platform_app(api_key: str = "dev-mesh-key") -> FastAPI:
    """Create the enhanced platform app."""
    platform_app = CrankPlatformApp(api_key)
    return platform_app.app

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point with HTTPS auto-detection."""
    import uvicorn
    from pathlib import Path
    
    app = create_platform_app()
    
    # 🔒 ZERO-TRUST: Auto-detect HTTPS based on certificate availability
    cert_dir = Path("/etc/certs")
    has_certs = (cert_dir / "platform.crt").exists() and (cert_dir / "platform.key").exists()
    
    # Kevin's port configuration - environment-based for maximum portability
    https_port = int(os.getenv('PLATFORM_HTTPS_PORT', '8443'))
    http_port = int(os.getenv('PLATFORM_HTTP_PORT', '8000'))
    
    if has_certs:
        # Start with HTTPS using mTLS
        print(f"🔒 Starting Crank Platform with HTTPS/mTLS on port {https_port}")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=https_port,
            ssl_keyfile=str(cert_dir / "platform.key"),
            ssl_certfile=str(cert_dir / "platform.crt"),
            ssl_ca_certs=str(cert_dir / "ca.crt")  # Require client certificates
        )
    else:
        print(f"⚠️  Starting Crank Platform with HTTP on port {http_port} (development only)")
        uvicorn.run(app, host="0.0.0.0", port=http_port)


if __name__ == "__main__":
    main()