"""
Crank Controller - Node-Local Worker Supervisor

The controller is the privileged supervisor process on each Crank node.
It manages worker registration, capability-based routing, and mesh coordination.

Core Responsibilities:
- Worker registration and health tracking
- Capability-based routing (verb:name → worker endpoint)
- Mesh coordination (share state with peer controllers)
- Certificate signing for workers (via CA)
- Trust enforcement (future: CAP policy)

Architecture:
- One controller per node
- Workers register capabilities on startup
- Controller routes requests to appropriate workers
- Mesh shares capability state across nodes (future)
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from crank.controller.capability_registry import CapabilityRegistry, CapabilitySchema
from crank.security import CertificateManager

logger = logging.getLogger(__name__)


# --- Request/Response Models ---


class RegisterRequest(BaseModel):
    """Worker registration request."""

    worker_id: str = Field(description="Unique worker identifier")
    worker_url: str = Field(description="Worker HTTPS endpoint")
    capabilities: list[dict[str, Any]] = Field(
        description="List of capabilities worker provides"
    )


class RegisterResponse(BaseModel):
    """Worker registration response."""

    status: str = Field(description="Registration status")
    worker_id: str = Field(description="Registered worker ID")
    capabilities_registered: int = Field(description="Number of capabilities registered")


class HeartbeatRequest(BaseModel):
    """Worker heartbeat request."""

    worker_id: str = Field(description="Worker identifier")


class HeartbeatResponse(BaseModel):
    """Worker heartbeat response."""

    status: str = Field(description="Heartbeat status")
    acknowledged: bool = Field(description="Whether heartbeat was acknowledged")


class RouteRequest(BaseModel):
    """Capability routing request."""

    verb: str = Field(description="Capability verb (e.g., 'invoke', 'query')")
    capability: str = Field(description="Capability name (e.g., 'email.classify')")
    slo_constraints: Optional[dict[str, Any]] = Field(
        default=None,
        description="SLO requirements (future: SLO-aware routing)"
    )
    requester_identity: Optional[str] = Field(
        default=None,
        description="Requester SPIFFE ID (future: CAP policy)"
    )
    budget_tokens: Optional[float] = Field(
        default=None,
        description="Budget tokens (future: economic routing)"
    )


class RouteResponse(BaseModel):
    """Capability routing response."""

    worker_id: str = Field(description="Selected worker ID")
    worker_url: str = Field(description="Worker endpoint URL")
    capability: str = Field(description="Matched capability")


class CapabilitiesResponse(BaseModel):
    """List of all registered capabilities."""

    capabilities: dict[str, dict[str, int]] = Field(
        description="Capability -> {workers, healthy_workers} mapping"
    )


class WorkersResponse(BaseModel):
    """List of all registered workers."""

    workers: list[dict[str, Any]] = Field(description="Worker details with health status")


# --- Controller Service ---


class ControllerService:
    """Controller service managing workers and capabilities.

    This is a standalone FastAPI service (not a worker) that uses
    crank.security for TLS/mTLS but has its own lifecycle.
    """

    def __init__(self, https_port: int = 9000):
        """Initialize controller.

        Args:
            https_port: HTTPS port for controller API (default: 9000)
        """
        self.https_port = https_port
        self.service_name = "crank-controller"

        # Initialize capability registry
        state_file = Path(os.getenv("CONTROLLER_STATE_FILE", "state/controller/registry.jsonl"))
        heartbeat_timeout = int(os.getenv("CONTROLLER_HEARTBEAT_TIMEOUT", "120"))
        self.registry = CapabilityRegistry(
            state_file=state_file,
            heartbeat_timeout=heartbeat_timeout,
        )

        # Initialize certificate manager for SSL
        self.cert_manager = CertificateManager(
            worker_id="crank-controller",  # Fixed ID for controller
        )

        # Create FastAPI app with lifespan for cleanup
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Controller lifespan: startup and shutdown hooks."""
            logger.info("🚀 Controller starting on port %d", self.https_port)
            # Startup: registry already initialized
            yield
            # Shutdown: registry auto-persists on each operation
            logger.info("🛑 Controller shutting down")

        self.app = FastAPI(
            title="Crank Controller",
            description="Node-local worker supervisor and capability router",
            version="0.1.0",
            lifespan=lifespan,
        )

        # Register routes
        self._register_routes()

        logger.info("Controller initialized with state file: %s", state_file)

    # --- Route Registration ---

    def _register_routes(self) -> None:
        """Register controller API endpoints."""

        # Health check endpoint
        @self.app.get("/health")
        async def health_check() -> JSONResponse:
            """Controller health check."""
            return JSONResponse(
                content={"status": "healthy", "service": self.service_name},
                status_code=200,
            )

        # Worker registration endpoint
        async def register_worker(request: RegisterRequest) -> JSONResponse:
            """Register worker with capabilities."""
            try:
                # Convert dict capabilities to CapabilitySchema
                capabilities = [
                    CapabilitySchema(**cap) for cap in request.capabilities
                ]

                # Register in capability registry
                self.registry.register(
                    worker_id=request.worker_id,
                    worker_url=request.worker_url,
                    capabilities=capabilities,
                )

                response = RegisterResponse(
                    status="registered",
                    worker_id=request.worker_id,
                    capabilities_registered=len(capabilities),
                )

                logger.info(
                    "Worker registered: %s with %d capabilities",
                    request.worker_id,
                    len(capabilities),
                )

                return JSONResponse(
                    content=response.model_dump(),
                    status_code=200,
                )

            except Exception as e:
                logger.error("Worker registration failed: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e

        self.app.post("/register")(register_worker)

        # Worker heartbeat endpoint
        async def heartbeat_worker(request: HeartbeatRequest) -> JSONResponse:
            """Update worker heartbeat timestamp."""
            try:
                acknowledged = self.registry.heartbeat(request.worker_id)

                response = HeartbeatResponse(
                    status="ok" if acknowledged else "unknown_worker",
                    acknowledged=acknowledged,
                )

                return JSONResponse(
                    content=response.model_dump(),
                    status_code=200 if acknowledged else 404,
                )

            except Exception as e:
                logger.error("Heartbeat processing failed: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e

        self.app.post("/heartbeat")(heartbeat_worker)

        # Worker deregistration endpoint
        async def deregister_worker(worker_id: str) -> JSONResponse:
            """Deregister worker (graceful shutdown)."""
            try:
                self.registry.deregister(worker_id)

                logger.info("Worker deregistered: %s", worker_id)

                return JSONResponse(
                    content={"status": "deregistered", "worker_id": worker_id},
                    status_code=200,
                )

            except Exception as e:
                logger.error("Worker deregistration failed: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e

        self.app.delete("/deregister/{worker_id}")(deregister_worker)

        # Capability routing endpoint
        async def route_capability(request: RouteRequest) -> JSONResponse:
            """Route capability request to appropriate worker."""
            try:
                worker = self.registry.route(
                    verb=request.verb,
                    capability=request.capability,
                    slo_constraints=request.slo_constraints,
                    requester_identity=request.requester_identity,
                    budget_tokens=request.budget_tokens,
                )

                if not worker:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No worker available for {request.verb}:{request.capability}",
                    )

                response = RouteResponse(
                    worker_id=worker.worker_id,
                    worker_url=worker.worker_url,
                    capability=f"{request.verb}:{request.capability}",
                )

                return JSONResponse(
                    content=response.model_dump(),
                    status_code=200,
                )

            except HTTPException:
                raise
            except Exception as e:
                logger.error("Routing failed: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e

        self.app.post("/route")(route_capability)

        # Introspection endpoints
        async def get_capabilities() -> JSONResponse:
            """Get all registered capabilities."""
            try:
                capabilities = self.registry.get_all_capabilities()

                response = CapabilitiesResponse(capabilities=capabilities)

                return JSONResponse(
                    content=response.model_dump(),
                    status_code=200,
                )

            except Exception as e:
                logger.error("Failed to get capabilities: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e

        self.app.get("/capabilities")(get_capabilities)

        async def get_workers() -> JSONResponse:
            """Get all registered workers."""
            try:
                workers = self.registry.get_all_workers()

                response = WorkersResponse(workers=workers)

                return JSONResponse(
                    content=response.model_dump(),
                    status_code=200,
                )

            except Exception as e:
                logger.error("Failed to get workers: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e

        self.app.get("/workers")(get_workers)

    # --- Run Method ---

    def run(self, host: str = "0.0.0.0", log_level: str = "info") -> None:
        """Run the controller service with HTTPS.

        Args:
            host: Host to bind to (default: 0.0.0.0)
            log_level: Uvicorn log level (default: info)
        """
        import uvicorn

        # Get SSL configuration from cert manager
        ssl_config = self.cert_manager.get_ssl_context()

        logger.info(
            "🚀 Starting controller %s on https://%s:%d",
            self.service_name,
            host,
            self.https_port,
        )

        # Run with uvicorn and mTLS
        uvicorn.run(
            self.app,
            host=host,
            port=self.https_port,
            log_level=log_level,
            ssl_certfile=ssl_config["ssl_certfile"],
            ssl_keyfile=ssl_config["ssl_keyfile"],
            ssl_ca_certs=ssl_config["ssl_ca_certs"],
        )


# --- Main Entry Point ---


def main() -> None:
    """Start the controller service."""
    port = int(os.getenv("CONTROLLER_HTTPS_PORT", "9000"))
    controller = ControllerService(https_port=port)
    controller.run()


if __name__ == "__main__":
    main()
