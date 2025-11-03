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
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List, Optional
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sse_starlette import EventSourceResponse
from pydantic import BaseModel

# Initialize logging FIRST - before any imports that might need logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

    def __init__(self):
        self.worker_id = f"streaming-{uuid.uuid4().hex[:8]}"
        self.active_connections: List[WebSocket] = []
        self.active_streams: Dict[str, Dict] = {}
        
    async def text_stream_generator(self, content: str, chunk_size: int = 100) -> AsyncGenerator[str, None]:
        """Generate text chunks for streaming."""
        words = content.split()
        chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            chunk_text = " ".join(chunk)
            result = {
                "chunk_id": i,
                "content": chunk_text,
                "is_last": i == len(chunks) - 1,
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(result)}\n\n"
            await asyncio.sleep(0.1)  # Simulate processing time

    async def connect_websocket(self, websocket: WebSocket):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Active connections: {len(self.active_connections)}")

    async def disconnect_websocket(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast_to_websockets(self, message: dict):
        """Broadcast message to all connected WebSockets."""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        # Clean up disconnected websockets
        for conn in disconnected:
            await self.disconnect_websocket(conn)

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Create service instance
streaming_service = CrankStreamingService()

# Create FastAPI app
app = FastAPI(
    title="Crank Streaming Service",
    description="HTTPS-only streaming service with WebSocket and SSE capabilities",
    version="2.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    logger.info(f"🌊 Crank Streaming Service starting up - Worker ID: {streaming_service.worker_id}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("🌊 Crank Streaming Service shutting down")

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "crank-streaming",
        "worker_id": streaming_service.worker_id,
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(streaming_service.active_connections),
        "active_streams": len(streaming_service.active_streams),
        "security": {
            "ssl_enabled": True,
            "ca_cert_available": os.path.exists("/etc/certs/ca.crt")
        }
    }

@app.get("/")
async def root():
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
            "sse": "/events"
        }
    }

# ============================================================================
# STREAMING ENDPOINTS
# ============================================================================

@app.post("/stream/text")
async def stream_text(request: StreamingRequest):
    """Stream text content using Server-Sent Events."""
    stream_id = f"stream-{uuid.uuid4().hex[:8]}"
    
    streaming_service.active_streams[stream_id] = {
        "type": "text",
        "started": datetime.now().isoformat(),
        "content_length": len(request.content)
    }
    
    logger.info(f"Starting text stream {stream_id} for {len(request.content)} characters")
    
    try:
        return EventSourceResponse(
            streaming_service.text_stream_generator(request.content, request.chunk_size)
        )
    finally:
        # Clean up stream record
        streaming_service.active_streams.pop(stream_id, None)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for bidirectional streaming."""
    await streaming_service.connect_websocket(websocket)
    
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "worker_id": streaming_service.worker_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        while True:
            # Wait for client message
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                logger.info(f"WebSocket received: {message.get('type', 'unknown')}")
                
                # Echo back with processing info
                response = {
                    "type": "response",
                    "original": message,
                    "processed_at": datetime.now().isoformat(),
                    "worker_id": streaming_service.worker_id
                }
                await websocket.send_text(json.dumps(response))
                
                # Broadcast to other connections
                broadcast_msg = {
                    "type": "broadcast",
                    "message": f"User sent: {message.get('content', 'No content')}",
                    "timestamp": datetime.now().isoformat()
                }
                await streaming_service.broadcast_to_websockets(broadcast_msg)
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    finally:
        await streaming_service.disconnect_websocket(websocket)

@app.get("/events")
async def server_sent_events(request: Request):
    """Server-Sent Events endpoint for real-time updates."""
    async def event_generator():
        """Generate periodic events."""
        event_count = 0
        while True:
            # Check if client is still connected
            if await request.is_disconnected():
                break
                
            event_count += 1
            event_data = {
                "event_id": event_count,
                "timestamp": datetime.now().isoformat(),
                "worker_id": streaming_service.worker_id,
                "active_connections": len(streaming_service.active_connections),
                "message": f"Periodic update #{event_count}"
            }
            
            yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(5)  # Send event every 5 seconds
    
    return EventSourceResponse(event_generator())

@app.get("/status")
async def get_status():
    """Get streaming service status."""
    return {
        "worker_id": streaming_service.worker_id,
        "active_connections": len(streaming_service.active_connections),
        "active_streams": len(streaming_service.active_streams),
        "stream_details": streaming_service.active_streams,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# MAIN FUNCTION - FOLLOWING PROVEN PATTERN
# ============================================================================

def main():
    """Main function following proven certificate initialization pattern."""
    import uvicorn
    
    try:
        # SYNCHRONOUS certificate initialization - PROVEN PATTERN
        logger.info("🔐 Initializing certificates using SECURE CSR pattern...")
        import sys
        sys.path.append('/app/scripts')
        import asyncio
        from crank_cert_initialize import main as init_certificates, cert_store
        
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
        
        logger.info(f"🌊 Starting Crank Streaming Service on HTTPS port {https_port}")
        
        uvicorn.run(
            "crank_streaming_simple:app",
            host=service_host,
            port=https_port,
            ssl_keyfile=key_path,
            ssl_certfile=cert_path,
            ssl_ca_certs=ca_path,
            reload=False,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"🚫 Failed to initialize certificates with CA service: {e}")
        raise RuntimeError(f"🚫 Failed to initialize certificates with CA service: {e}")

if __name__ == "__main__":
    main()