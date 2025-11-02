#!/usr/bin/env python3
"""
Crank Streaming Service - REFACTORED with Worker Certificate Library

Demonstrates true streaming patterns for real-time data processing:
1. Server-Sent Events (SSE) for progressive results
2. WebSocket streams for bidirectional communication  
3. Async generators for streaming large datasets
4. Real-time email processing pipeline
"""

import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List, Optional
from uuid import uuid4
import email
import mailbox
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, WebSocket
from fastapi.responses import StreamingResponse
from sse_starlette import EventSourceResponse
from pydantic import BaseModel

# Import worker certificate library
from worker_cert_pattern import WorkerCertificatePattern, create_worker_fastapi_with_certs

logger = logging.getLogger(__name__)

# ============================================================================
# WORKER REGISTRATION MODELS
# ============================================================================

class WorkerRegistration(BaseModel):
    """Model for worker registration with platform."""
    worker_id: str
    service_type: str  
    endpoint: str
    health_url: str
    capabilities: List[str]

class StreamingRequest(BaseModel):
    """Request model for streaming operations."""
    operation: str
    parameters: Dict[str, Any] = {}
    chunk_size: int = 100
    delay_ms: int = 100

# ============================================================================
# STREAMING PATTERNS
# ============================================================================

class StreamingEmailProcessor:
    """Demonstrates real streaming email processing patterns."""
    
    def __init__(self):
        self.active_streams = {}
        
    async def stream_email_analysis(self, emails: List[Dict], chunk_size: int = 10, 
                                  delay_ms: int = 100) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream email analysis results progressively."""
        
        total_emails = len(emails)
        processed = 0
        
        # Process emails in chunks
        for i in range(0, total_emails, chunk_size):
            chunk = emails[i:i + chunk_size]
            chunk_results = []
            
            for email_data in chunk:
                # Simulate processing
                await asyncio.sleep(delay_ms / 1000.0)
                
                result = {
                    "email_id": email_data.get("id", f"email_{processed}"),
                    "subject": email_data.get("subject", "No Subject"),
                    "sentiment": "positive" if "thank" in email_data.get("subject", "").lower() else "neutral",
                    "priority": "high" if "urgent" in email_data.get("subject", "").lower() else "normal",
                    "processed_at": datetime.now().isoformat()
                }
                
                chunk_results.append(result)
                processed += 1
            
            # Yield chunk progress
            yield {
                "chunk": i // chunk_size + 1,
                "progress": processed / total_emails,
                "processed": processed,
                "total": total_emails,
                "results": chunk_results,
                "timestamp": datetime.now().isoformat()
            }
    
    async def stream_real_time_metrics(self, duration_seconds: int = 60) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream real-time system metrics."""
        
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < duration_seconds:
            # Generate mock metrics
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "emails_processed": uuid4().int % 1000,
                "cpu_usage": (uuid4().int % 100) / 100.0,
                "memory_usage": (uuid4().int % 80) / 100.0,
                "active_connections": uuid4().int % 50,
                "queue_size": uuid4().int % 200
            }
            
            yield metrics
            await asyncio.sleep(1)  # 1 second intervals
    
    async def stream_large_dataset(self, size: int = 10000, chunk_size: int = 100) -> AsyncGenerator[List[Dict], None]:
        """Stream large dataset in chunks."""
        
        for i in range(0, size, chunk_size):
            chunk = []
            for j in range(chunk_size):
                if i + j >= size:
                    break
                    
                record = {
                    "id": i + j,
                    "data": f"record_{i + j}",
                    "value": (i + j) * 1.5,
                    "timestamp": datetime.now().isoformat()
                }
                chunk.append(record)
            
            yield chunk
            await asyncio.sleep(0.1)  # Small delay to prevent overwhelming


def setup_streaming_routes(app: FastAPI, worker_config: dict):
    """Set up streaming service routes using worker config."""
    
    # Get components from worker config
    cert_store = worker_config["cert_store"]
    platform_url = worker_config["platform_url"]
    worker_url = worker_config["worker_url"]
    service_name = worker_config["service_name"]
    
    # Initialize streaming processor
    processor = StreamingEmailProcessor()
    
    # Worker registration state
    worker_id = None
    
    def _create_adaptive_client(timeout: float = 10.0) -> httpx.AsyncClient:
        """Create HTTP client using pre-loaded certificates."""
        if cert_store and cert_store.ca_cert:
            # Create temporary CA certificate for httpx to use
            with tempfile.NamedTemporaryFile(mode='w', suffix='.crt', delete=False) as ca_file:
                ca_file.write(cert_store.ca_cert)
                ca_file.flush()
                
                # Configure httpx to trust our CA certificate
                return httpx.AsyncClient(
                    verify=ca_file.name,
                    timeout=timeout
                )
        else:
            # Fallback for development - disable verification
            logger.warning("⚠️ No CA certificate available, using insecure client")
            return httpx.AsyncClient(verify=False, timeout=timeout)
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint with security status."""
        security_status = {
            "ssl_enabled": cert_store.platform_cert is not None if cert_store else False,
            "ca_cert_available": cert_store.ca_cert is not None if cert_store else False,
            "certificate_source": "Worker Certificate Library"
        }
        
        return {
            "status": "healthy",
            "service": service_name,
            "capabilities": ["sse_streaming", "websocket_streaming", "json_streaming", "realtime_processing"],
            "streaming_patterns": ["server_sent_events", "websockets", "async_generators"],
            "security": security_status,
            "timestamp": datetime.now().isoformat()
        }
    
    @app.get("/stream/emails")
    async def stream_email_analysis(
        count: int = 100,
        chunk_size: int = 10,
        delay_ms: int = 100
    ):
        """Stream email analysis results using Server-Sent Events."""
        
        # Generate mock email data
        emails = [
            {
                "id": f"email_{i}",
                "subject": f"Email {i} - {'Urgent' if i % 10 == 0 else 'Normal'} Message",
                "content": f"Content for email {i}"
            }
            for i in range(count)
        ]
        
        async def event_generator():
            async for chunk in processor.stream_email_analysis(emails, chunk_size, delay_ms):
                yield f"data: {json.dumps(chunk)}\n\n"
        
        return EventSourceResponse(event_generator())
    
    @app.get("/stream/metrics")
    async def stream_metrics(duration: int = 60):
        """Stream real-time metrics using Server-Sent Events."""
        
        async def event_generator():
            async for metrics in processor.stream_real_time_metrics(duration):
                yield f"data: {json.dumps(metrics)}\n\n"
        
        return EventSourceResponse(event_generator())
    
    @app.get("/stream/dataset")
    async def stream_large_dataset(size: int = 1000, chunk_size: int = 50):
        """Stream large dataset as JSON chunks."""
        
        async def json_generator():
            async for chunk in processor.stream_large_dataset(size, chunk_size):
                yield json.dumps(chunk) + "\n"
        
        return StreamingResponse(
            json_generator(),
            media_type="application/x-ndjson",
            headers={"X-Total-Size": str(size)}
        )
    
    @app.websocket("/ws/realtime")
    async def websocket_realtime(websocket: WebSocket):
        """WebSocket endpoint for bidirectional real-time communication."""
        await websocket.accept()
        
        stream_id = f"stream_{uuid4().hex[:8]}"
        processor.active_streams[stream_id] = websocket
        
        try:
            # Send welcome message
            await websocket.send_json({
                "type": "connection",
                "stream_id": stream_id,
                "message": "Connected to real-time stream",
                "timestamp": datetime.now().isoformat()
            })
            
            # Handle incoming messages and send responses
            while True:
                try:
                    data = await websocket.receive_json()
                    
                    if data.get("type") == "subscribe":
                        # Start streaming metrics
                        await websocket.send_json({
                            "type": "subscription",
                            "status": "active",
                            "stream_id": stream_id
                        })
                        
                        # Stream metrics
                        async for metrics in processor.stream_real_time_metrics(30):
                            await websocket.send_json({
                                "type": "metrics",
                                "data": metrics,
                                "stream_id": stream_id
                            })
                    
                    elif data.get("type") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        })
                        
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            if stream_id in processor.active_streams:
                del processor.active_streams[stream_id]
    
    @app.post("/stream/process")
    async def start_streaming_process(request: StreamingRequest):
        """Start a streaming process based on request parameters."""
        
        if request.operation == "email_analysis":
            # Mock email data
            emails = [{"id": f"email_{i}", "subject": f"Subject {i}"} for i in range(100)]
            
            # Return streaming URL
            return {
                "status": "started",
                "operation": request.operation,
                "stream_url": f"/stream/emails?count=100&chunk_size={request.chunk_size}&delay_ms={request.delay_ms}",
                "estimated_duration": "10-30 seconds"
            }
        
        elif request.operation == "metrics":
            return {
                "status": "started", 
                "operation": request.operation,
                "stream_url": "/stream/metrics?duration=60",
                "estimated_duration": "60 seconds"
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {request.operation}")
    
    async def _startup():
        """Startup handler - register with platform."""
        nonlocal worker_id
        
        logger.info("🌊 Starting Crank Streaming Service...")
        logger.info("🔐 Using certificates loaded synchronously at startup")
        
        # Prepare registration info
        worker_info = WorkerRegistration(
            worker_id=f"streaming-{uuid4().hex[:8]}",
            service_type="streaming",
            endpoint=worker_url,
            health_url=f"{worker_url}/health",
            capabilities=["sse_streaming", "websocket_streaming", "json_streaming", "realtime_processing"]
        )
        
        # Register with platform
        await _register_with_platform(worker_info)
        worker_id = worker_info.worker_id
        
        # Start heartbeat background task
        _start_heartbeat_task()
    
    async def _register_with_platform(worker_info: WorkerRegistration):
        """Register this worker with the platform using mTLS."""
        max_retries = 5
        retry_delay = 5  # seconds
        
        # Auth token for platform
        auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "dev-mesh-key")
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        for attempt in range(max_retries):
            try:
                # Use mTLS client for secure communication
                async with _create_adaptive_client() as client:
                    response = await client.post(
                        f"{platform_url}/v1/workers/register",
                        json=worker_info.model_dump(),
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"🔒 Successfully registered streaming service via mTLS. Worker ID: {worker_info.worker_id}")
                        return
                    else:
                        logger.error(f"Registration failed: {response.status_code} - {response.text}")
                        
            except Exception as e:
                logger.warning(f"Registration attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying registration in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
        
        raise RuntimeError(f"Failed to register with platform after {max_retries} attempts")
    
    def _start_heartbeat_task():
        """Start the background heartbeat task."""
        async def heartbeat_task():
            while True:
                try:
                    await asyncio.sleep(20)  # 20 second heartbeat interval
                    await _send_heartbeat()
                except asyncio.CancelledError:
                    logger.info("Heartbeat task cancelled")
                    break
                except Exception as e:
                    logger.warning(f"Heartbeat failed: {e}")
        
        asyncio.create_task(heartbeat_task())
        logger.info("🫀 Started heartbeat task with 20s interval")
    
    async def _send_heartbeat():
        """Send heartbeat to platform."""
        if worker_id:
            try:
                async with _create_adaptive_client(timeout=5.0) as client:
                    response = await client.post(
                        f"{platform_url}/v1/workers/{worker_id}/heartbeat",
                        data={
                            "service_type": "streaming",
                            "load_score": len(processor.active_streams) * 0.1  # Load based on active streams
                        },
                        headers={"Authorization": f"Bearer {os.getenv('PLATFORM_AUTH_TOKEN', 'dev-mesh-key')}"}
                    )
                    # Heartbeat success is logged at debug level to reduce noise
            except Exception as e:
                logger.debug(f"Heartbeat failed: {e}")
    
    async def _shutdown():
        """Shutdown handler - deregister from platform using mTLS."""
        if worker_id:
            try:
                async with _create_adaptive_client(timeout=5.0) as client:
                    await client.delete(f"{platform_url}/v1/workers/{worker_id}")
                logger.info("🔒 Successfully deregistered streaming service via mTLS")
            except Exception as e:
                logger.warning(f"Failed to deregister from platform: {e}")
    
    # Register startup/shutdown handlers
    app.add_event_handler("startup", _startup)
    app.add_event_handler("shutdown", _shutdown)


def create_crank_streaming_service(cert_store=None):
    """Create the Crank Streaming Service application with optional certificate store."""
    # This is kept for backward compatibility but now uses the worker library pattern
    worker_config = {
        "app": FastAPI(title="Crank Streaming Service", version="1.0.0"),
        "cert_store": cert_store,
        "platform_url": os.getenv("PLATFORM_URL", "https://platform:8443"),
        "worker_url": os.getenv("WORKER_URL", "https://crank-streaming:8501"),
        "service_name": "crank-streaming"
    }
    
    setup_streaming_routes(worker_config["app"], worker_config)
    return worker_config["app"]


def main():
    """Main entry point using Worker Certificate Library."""
    
    # Step 1: Initialize certificates SYNCHRONOUSLY using library
    cert_pattern = WorkerCertificatePattern("crank-streaming")
    cert_store = cert_pattern.initialize_certificates()
    
    # Step 2: Create FastAPI with pre-loaded certificates using library
    worker_config = create_worker_fastapi_with_certs(
        title="Crank Streaming Service",
        service_name="crank-streaming",
        platform_url=None,  # Use default from environment
        worker_url=None,    # Use default from environment
        cert_store=cert_store
    )
    
    # Step 3: Setup streaming service routes
    setup_streaming_routes(worker_config["app"], worker_config)
    
    # Step 4: Start server with certificates using library
    https_port = int(os.getenv("STREAMING_HTTPS_PORT", "8501"))
    cert_pattern.start_server(worker_config["app"], port=https_port)


# For direct running
if __name__ == "__main__":
    main()