"""
Crank Platform Streaming Service - Simplified Pattern

HTTPS-only streaming service with WebSocket and SSE capabilities.
Following proven working pattern from email-classifier, email-parser, and doc-converter.
"""

import asyncio
import json
import logging
import os
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional

import httpx
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

# Initialize logging FIRST - before any imports that might need logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================================================
# WORKER REGISTRATION MODEL
# ============================================================================


class WorkerRegistration(BaseModel):
    """Worker registration model."""

    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: list[str]


# ============================================================================
# STREAMING MODELS
# ============================================================================


class StreamingRequest(BaseModel):
    """Request model for streaming operations."""

    content: str
    stream_type: str = "text"
    chunk_size: int = 100


class StreamingStatus(BaseModel):
    """Status model for streaming operations."""

    status: str
    stream_id: str
    timestamp: str
    chunks_sent: int


# ============================================================================
# STREAMING SERVICE
# ============================================================================


class CrankStreamingService:
    """Streaming service with WebSocket and SSE capabilities."""

    def __init__(self) -> None:
        self.worker_id = f"streaming-{uuid.uuid4().hex[:8]}"
        self.active_connections: list[WebSocket] = []
        self.active_streams: dict[str, dict[str, Any]] = {}
        self.heartbeat_task: Optional[asyncio.Task[None]] = None

    async def text_stream_generator(
        self,
        content: str,
        chunk_size: int = 100,
    ) -> AsyncGenerator[str, None]:
        """Generate text chunks for streaming."""
        words = content.split()
        chunks = [words[i : i + chunk_size] for i in range(0, len(words), chunk_size)]

        for i, chunk in enumerate(chunks):
            chunk_text = " ".join(chunk)
            result: dict[str, Any] = {
                "chunk_id": i,
                "content": chunk_text,
                "is_last": i == len(chunks) - 1,
                "timestamp": datetime.now().isoformat(),
            }
            yield f"data: {json.dumps(result)}\n\n"
            await asyncio.sleep(0.1)  # Simulate processing time

    async def connect_websocket(self, websocket: WebSocket) -> None:
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected. Active connections: {len(self.active_connections)}")

    async def disconnect_websocket(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast_to_websockets(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected WebSockets."""
        if not self.active_connections:
            return

        disconnected: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected websockets
        for conn in disconnected:
            await self.disconnect_websocket(conn)

    async def initialize_and_register(self) -> None:
        """Initialize service and register with platform - follows email classifier pattern."""
        logger.info("🚀 Starting streaming service initialization...")

        # Set up worker URL for platform registration
        https_port = int(os.getenv("STREAMING_HTTPS_PORT", "8500"))
        service_name = os.getenv("STREAMING_SERVICE_NAME", "crank-streaming-dev")
        self.worker_url = f"https://{service_name}:{https_port}"

        logger.info("🔒 Using certificates loaded synchronously at startup")

        # Prepare registration info
        worker_info = WorkerRegistration(
            worker_id=self.worker_id,
            service_type="streaming_analytics",
            endpoint=self.worker_url,
            health_url=f"{self.worker_url}/health",
            capabilities=[
                "real_time_processing",
                "websocket_streaming",
                "event_processing",
                "sse_streaming",
                "json_streaming",
            ],
        )

        # Register with platform
        await self._register_with_platform(worker_info)

        # Start heartbeat background task
        self._start_heartbeat_task()

    def _create_adaptive_client(self, timeout: float = 30.0) -> httpx.AsyncClient:
        """Create HTTP client with proper SSL configuration - matches email classifier pattern."""
        # For development, disable SSL verification but maintain connection stability
        return httpx.AsyncClient(
            verify=False,
            timeout=timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

    def _start_heartbeat_task(self) -> None:
        """Start the background heartbeat task."""
        import asyncio

        async def heartbeat_loop() -> None:
            await asyncio.sleep(5)  # Initial delay
            while True:
                try:
                    await self._send_heartbeat()
                    await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                except Exception:
                    logger.exception("💔 Heartbeat failed: {e}")
                    await asyncio.sleep(5)  # Shorter retry interval on failure

        # Start heartbeat task and store reference to prevent garbage collection
        self.heartbeat_task = asyncio.create_task(heartbeat_loop())

    async def _register_with_platform(self, worker_info: WorkerRegistration) -> None:
        """Register this worker with the platform - follows email classifier pattern."""
        platform_url = os.getenv("PLATFORM_URL", "https://crank-platform-dev:8443")
        auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "local-dev-key")

        registration_url = f"{platform_url}/v1/workers/register"
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

        # Retry registration with exponential backoff
        max_retries = 5
        for attempt in range(max_retries):
            try:
                async with self._create_adaptive_client() as client:
                    response = await client.post(
                        registration_url,
                        json=worker_info.model_dump(),
                        headers=headers,
                    )

                    if response.status_code == 200:
                        logger.info(
                            f"✅ Successfully registered with platform: {worker_info.worker_id}",
                        )
                        return
                    logger.warning(
                        f"⚠️  Registration attempt {attempt + 1} failed: {response.status_code} - {response.text}",
                    )

            except Exception:
                logger.warning("⚠️  Registration attempt {attempt + 1} failed: {e}")

            # Exponential backoff
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                logger.info("⏳ Retrying registration in {wait_time} seconds...")
                await asyncio.sleep(wait_time)

        logger.error("❌ Failed to register with platform after {max_retries} attempts")

    async def _send_heartbeat(self) -> None:
        """Send heartbeat to platform - follows email classifier pattern."""
        platform_url = os.getenv("PLATFORM_URL", "https://crank-platform-dev:8443")
        auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "local-dev-key")

        heartbeat_url = f"{platform_url}/v1/workers/{self.worker_id}/heartbeat"
        headers = {
            "Authorization": f"Bearer {auth_token}",
        }

        # Use form data format as expected by platform - matches email classifier pattern
        form_data = {
            "service_type": "streaming_analytics",
            "load_score": "0.0",
        }

        try:
            async with self._create_adaptive_client(timeout=10.0) as client:
                response = await client.post(heartbeat_url, data=form_data, headers=headers)
                if response.status_code == 200:
                    logger.debug("💓 Heartbeat sent successfully")
                else:
                    logger.warning("⚠️  Heartbeat failed: {response.status_code}")
        except Exception:
            logger.warning("⚠️  Heartbeat failed: {e}")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Create service instance
streaming_service = CrankStreamingService()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    # Startup
    logger.info(
        f"🌊 Crank Streaming Service starting up - Worker ID: {streaming_service.worker_id}",
    )
    # Initialize and register with platform
    await streaming_service.initialize_and_register()

    yield

    # Shutdown
    logger.info("🌊 Crank Streaming Service shutting down")


# Create FastAPI app
app = FastAPI(
    title="Crank Streaming Service",
    description="HTTPS-only streaming service with WebSocket and SSE capabilities",
    version="2.0.0",
    lifespan=lifespan,
)


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "crank-streaming",
        "worker_id": streaming_service.worker_id,
        "capabilities": [
            "real_time_processing",
            "websocket_streaming",
            "event_processing",
            "sse_streaming",
            "json_streaming",
        ],
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(streaming_service.active_connections),
        "active_streams": len(streaming_service.active_streams),
        "security": {
            "ssl_enabled": True,
            "ca_cert_available": os.path.exists("/etc/certs/ca.crt"),
        },
    }


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint."""
    return {
        "service": "crank-streaming",
        "version": "2.0.0",
        "worker_id": streaming_service.worker_id,
        "capabilities": ["text-streaming", "websocket", "sse"],
        "endpoints": {
            "health": "/health",
            "stream_text": "/stream/text",
            "websocket": "/ws",
            "sse": "/events",
        },
    }


# ============================================================================
# STREAMING ENDPOINTS
# ============================================================================


@app.get("/capabilities")
async def get_stream_info() -> dict[str, Any]:
    """Get streaming endpoint information - expected by smoke test."""
    return {
        "status": "ready",
        "service": "streaming",
        "endpoints": {
            "text_stream": "/stream/text",
            "websocket": "/ws",
            "events": "/events",
        },
        "capabilities": ["text_streaming", "websocket", "sse"],
        "message": "Use POST /stream/text for text streaming",
    }


@app.post("/stream/text")
async def stream_text(request: StreamingRequest) -> EventSourceResponse:
    """Stream text content using Server-Sent Events."""
    stream_id = f"stream-{uuid.uuid4().hex[:8]}"

    streaming_service.active_streams[stream_id] = {
        "type": "text",
        "started": datetime.now().isoformat(),
        "content_length": len(request.content),
    }

    logger.info("Starting text stream {stream_id} for {len(request.content)} characters")

    try:
        return EventSourceResponse(
            streaming_service.text_stream_generator(request.content, request.chunk_size),
        )
    finally:
        # Clean up stream record
        streaming_service.active_streams.pop(stream_id, None)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for bidirectional streaming."""
    await streaming_service.connect_websocket(websocket)

    try:
        # Send welcome message
        await websocket.send_text(
            json.dumps(
                {
                    "type": "welcome",
                    "worker_id": streaming_service.worker_id,
                    "timestamp": datetime.now().isoformat(),
                },
            ),
        )

        while True:
            # Wait for client message
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                logger.info("WebSocket received: {message.get('type', 'unknown')}")

                # Echo back with processing info
                response: dict[str, Any] = {
                    "type": "response",
                    "original": message,
                    "processed_at": datetime.now().isoformat(),
                    "worker_id": streaming_service.worker_id,
                }
                await websocket.send_text(json.dumps(response))

                # Broadcast to other connections
                broadcast_msg = {
                    "type": "broadcast",
                    "message": f"User sent: {message.get('content', 'No content')}",
                    "timestamp": datetime.now().isoformat(),
                }
                await streaming_service.broadcast_to_websockets(broadcast_msg)

            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "message": "Invalid JSON format",
                        },
                    ),
                )

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    finally:
        await streaming_service.disconnect_websocket(websocket)


@app.get("/events")
async def server_sent_events(request: Request) -> EventSourceResponse:
    """Server-Sent Events endpoint for real-time updates."""

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate periodic events."""
        event_count = 0
        while True:
            # Check if client is still connected
            if await request.is_disconnected():
                break

            event_count += 1
            event_data: dict[str, Any] = {
                "event_id": event_count,
                "timestamp": datetime.now().isoformat(),
                "worker_id": streaming_service.worker_id,
                "active_connections": len(streaming_service.active_connections),
                "message": f"Periodic update #{event_count}",
            }

            yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(5)  # Send event every 5 seconds

    return EventSourceResponse(event_generator())


@app.get("/status")
async def get_status() -> dict[str, Any]:
    """Get streaming service status."""
    return {
        "worker_id": streaming_service.worker_id,
        "active_connections": len(streaming_service.active_connections),
        "active_streams": len(streaming_service.active_streams),
        "stream_details": streaming_service.active_streams,
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# MAIN FUNCTION - FOLLOWING PROVEN PATTERN
# ============================================================================


def main() -> None:
    """Main function following proven certificate initialization pattern."""
    try:
        # SYNCHRONOUS certificate initialization - PROVEN PATTERN
        logger.info("🔐 Initializing certificates using SECURE CSR pattern...")

        from crank_platform.security import init_certificates

        # Synchronous initialization - this is the PROVEN pattern
        asyncio.run(init_certificates())

        # Verify certificates are available
        cert_path = "/etc/certs/platform.crt"
        key_path = "/etc/certs/platform.key"
        ca_path = "/etc/certs/ca.crt"

        if not all(os.path.exists(p) for p in [cert_path, key_path, ca_path]):
            raise RuntimeError("🚫 Required certificates not found after initialization")

        logger.info("✅ Certificate initialization successful")

        # Start HTTPS-only server - PROVEN PATTERN
        https_port = int(os.getenv("STREAMING_HTTPS_PORT", "8500"))
        service_host = os.getenv("STREAMING_HOST", "0.0.0.0")

        logger.info("🌊 Starting Crank Streaming Service on HTTPS port {https_port}")

        uvicorn.run(
            "crank_streaming_simple:app",
            host=service_host,
            port=https_port,
            ssl_keyfile=key_path,
            ssl_certfile=cert_path,
            ssl_ca_certs=ca_path,
            reload=False,
            log_level="info",
        )

    except Exception as e:
        logger.exception("🚫 Failed to initialize certificates with CA service: {e}")
        raise RuntimeError(f"🚫 Failed to initialize certificates with CA service: {e}") from e


if __name__ == "__main__":
    main()
