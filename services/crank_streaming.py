"""Crank Streaming Service - Refactored to use WorkerApplication."""

import asyncio
import json
import logging
import os
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from fastapi import Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from crank.capabilities.schema import STREAMING_CLASSIFICATION, CapabilityDefinition
from crank.worker_runtime import WorkerApplication

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# REQUEST/RESPONSE MODELS
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
# STREAMING WORKER - BUSINESS LOGIC ONLY
# ============================================================================


class StreamingWorker(WorkerApplication):
    """Streaming worker with WebSocket and SSE capabilities.

    This worker provides real-time streaming capabilities including:
    - Server-Sent Events (SSE) for text streaming
    - WebSocket connections for bidirectional communication
    - Event broadcasting to multiple clients

    All infrastructure (registration, heartbeat, health checks, certificates)
    is handled by the WorkerApplication base class.
    """

    def __init__(self) -> None:
        """Initialize streaming worker."""
        super().__init__(
            service_name="crank-streaming",
            https_port=int(os.getenv("STREAMING_HTTPS_PORT", "8500")),
        )

        # Business-specific state
        self.active_connections: list[WebSocket] = []
        self.active_streams: dict[str, dict[str, Any]] = {}

    def get_capabilities(self) -> list[CapabilityDefinition]:
        """Return worker capabilities."""
        return [STREAMING_CLASSIFICATION]

    def setup_routes(self) -> None:
        """Set up streaming-specific routes.
        
        IMPORTANT: Use explicit binding pattern self.app.METHOD("/path")(handler)
        instead of @self.app.METHOD decorators to avoid Pylance "not accessed" warnings.
        This gives the language server a concrete reference to the handler function.
        
        Pattern documented in:
        - src/crank/worker_runtime/base.py (lines 11-13, 187-192)
        - .vscode/AGENT_CONTEXT.md (FastAPI Route Handler Pattern section)
        """

        # Text streaming endpoint - SSE for chunked text delivery
        async def stream_text(request: StreamingRequest) -> EventSourceResponse:
            """Stream text content using Server-Sent Events."""
            stream_id = f"stream-{os.urandom(4).hex()}"

            self.active_streams[stream_id] = {
                "type": "text",
                "started": datetime.now().isoformat(),
                "content_length": len(request.content),
            }

            logger.info(f"Starting text stream {stream_id} for {len(request.content)} characters")

            try:
                return EventSourceResponse(
                    self.text_stream_generator(request.content, request.chunk_size),
                )
            finally:
                self.active_streams.pop(stream_id, None)

        # Explicit binding pattern - no decorator
        self.app.post("/stream/text")(stream_text)

        # WebSocket endpoint - bidirectional streaming
        async def websocket_endpoint(websocket: WebSocket) -> None:
            """WebSocket endpoint for bidirectional streaming."""
            await self.connect_websocket(websocket)

            try:
                # Send welcome message
                await websocket.send_text(
                    json.dumps({
                        "type": "welcome",
                        "worker_id": self.worker_id,
                        "timestamp": datetime.now().isoformat(),
                    }),
                )

                while True:
                    # Wait for client message
                    data = await websocket.receive_text()

                    try:
                        message = json.loads(data)
                        logger.info(f"WebSocket received: {message.get('type', 'unknown')}")

                        # Echo back with processing info
                        response: dict[str, Any] = {
                            "type": "response",
                            "original": message,
                            "processed_at": datetime.now().isoformat(),
                            "worker_id": self.worker_id,
                        }
                        await websocket.send_text(json.dumps(response))

                        # Broadcast to other connections
                        broadcast_msg = {
                            "type": "broadcast",
                            "message": f"User sent: {message.get('content', 'No content')}",
                            "timestamp": datetime.now().isoformat(),
                        }
                        await self.broadcast_to_websockets(broadcast_msg)

                    except json.JSONDecodeError:
                        await websocket.send_text(
                            json.dumps({
                                "type": "error",
                                "message": "Invalid JSON format",
                            }),
                        )

            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
            finally:
                await self.disconnect_websocket(websocket)

        # Explicit binding pattern
        self.app.websocket("/ws")(websocket_endpoint)

        # Server-Sent Events endpoint - periodic updates
        async def server_sent_events(request: Request) -> EventSourceResponse:
            """Server-Sent Events endpoint for real-time updates."""

            async def event_generator() -> AsyncGenerator[str, None]:
                """Generate periodic events."""
                event_count = 0
                while True:
                    if await request.is_disconnected():
                        break

                    event_count += 1
                    event_data: dict[str, Any] = {
                        "event_id": event_count,
                        "timestamp": datetime.now().isoformat(),
                        "worker_id": self.worker_id,
                        "active_connections": len(self.active_connections),
                        "message": f"Periodic update #{event_count}",
                    }

                    yield f"data: {json.dumps(event_data)}\n\n"
                    await asyncio.sleep(5)

            return EventSourceResponse(event_generator())

        # Explicit binding pattern
        self.app.get("/events")(server_sent_events)

        # Status endpoint - worker state information
        async def get_status() -> dict[str, Any]:
            """Get streaming service status."""
            return {
                "worker_id": self.worker_id,
                "active_connections": len(self.active_connections),
                "active_streams": len(self.active_streams),
                "stream_details": self.active_streams,
                "timestamp": datetime.now().isoformat(),
            }

        # Explicit binding pattern
        self.app.get("/status")(get_status)

        # Capabilities endpoint - required by smoke tests
        async def get_stream_info() -> dict[str, Any]:
            """Get streaming endpoint information."""
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

        # Explicit binding pattern
        self.app.get("/capabilities")(get_stream_info)

        # Root endpoint - service information
        async def root() -> dict[str, Any]:
            """Root endpoint."""
            return {
                "service": "crank-streaming",
                "version": "2.0.0",
                "worker_id": self.worker_id,
                "capabilities": ["text-streaming", "websocket", "sse"],
                "endpoints": {
                    "health": "/health",
                    "stream_text": "/stream/text",
                    "websocket": "/ws",
                    "sse": "/events",
                },
            }

        # Explicit binding pattern
        self.app.get("/")(root)

    # ========================================================================
    # BUSINESS LOGIC - STREAMING METHODS
    # ========================================================================

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
            await asyncio.sleep(0.1)

    async def connect_websocket(self, websocket: WebSocket) -> None:
        """Accept and track WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    async def disconnect_websocket(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection from tracking."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast_to_websockets(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected WebSocket clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            await self.disconnect_websocket(connection)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    """Main entry point - creates and runs streaming worker."""
    worker = StreamingWorker()
    worker.run()


if __name__ == "__main__":
    main()
