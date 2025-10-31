"""
Crank Platform Streaming Architecture

Demonstrates true streaming patterns for real-time data processing:
1. Server-Sent Events (SSE) for progressive results
2. WebSocket streams for bidirectional communication  
3. Async generators for streaming large datasets
4. Real-time email processing pipeline
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List, Optional
from uuid import uuid4
import email
import mailbox
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse
from sse_starlette import EventSourceResponse
import httpx

logger = logging.getLogger(__name__)

# ============================================================================
# STREAMING PATTERNS
# ============================================================================

class StreamingEmailProcessor:
    """Demonstrates real streaming email processing patterns."""
    
    def __init__(self):
        self.active_streams: Dict[str, Dict] = {}
        self.classifier_url = "https://localhost:8004"
        
    # Pattern 1: Server-Sent Events (SSE) for Progressive Processing
    async def stream_email_processing_sse(
        self, 
        mbox_file_path: str,
        request: Request
    ) -> EventSourceResponse:
        """
        Stream email processing results using Server-Sent Events.
        Perfect for showing progress on large email archives.
        """
        
        async def event_generator():
            stream_id = uuid4().hex[:8]
            processed_count = 0
            
            try:
                # Open mbox file for streaming
                mbox = mailbox.mbox(mbox_file_path)
                total_emails = len(mbox)
                
                # Send initial event
                yield {
                    "event": "stream_started",
                    "data": json.dumps({
                        "stream_id": stream_id,
                        "total_emails": total_emails,
                        "status": "processing"
                    })
                }
                
                # Process emails one by one, streaming results
                async for result in self._process_emails_streaming(mbox):
                    processed_count += 1
                    
                    # Send progress update
                    yield {
                        "event": "email_processed", 
                        "data": json.dumps({
                            "stream_id": stream_id,
                            "email_result": result,
                            "progress": {
                                "processed": processed_count,
                                "total": total_emails,
                                "percentage": (processed_count / total_emails) * 100
                            }
                        })
                    }
                    
                    # Check if client disconnected
                    if await request.is_disconnected():
                        logger.info(f"Client disconnected, stopping stream {stream_id}")
                        break
                        
                    # Small delay to prevent overwhelming client
                    await asyncio.sleep(0.1)
                
                # Send completion event
                yield {
                    "event": "stream_completed",
                    "data": json.dumps({
                        "stream_id": stream_id,
                        "total_processed": processed_count,
                        "status": "completed"
                    })
                }
                
            except Exception as e:
                # Send error event
                yield {
                    "event": "stream_error",
                    "data": json.dumps({
                        "stream_id": stream_id,
                        "error": str(e),
                        "status": "error"
                    })
                }
        
        return EventSourceResponse(event_generator())
    
    # Pattern 2: Async Generator for Streaming Large Datasets
    async def _process_emails_streaming(self, mbox: mailbox.mbox) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Async generator that yields email processing results one by one.
        This is true streaming - no buffering of results.
        """
        
        for message in mbox:
            try:
                # Extract email data
                email_data = {
                    "message_id": message.get("Message-ID", f"unknown-{uuid4().hex[:8]}"),
                    "subject": message.get("Subject", ""),
                    "from": message.get("From", ""),
                    "date": message.get("Date", ""),
                    "body": self._extract_body(message)
                }
                
                # Stream to ML classifier
                classification = await self._classify_email_streaming(email_data)
                
                # Yield result immediately (no buffering)
                yield {
                    **email_data,
                    "classification": classification,
                    "processed_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                # Yield error for this email but continue processing
                yield {
                    "error": str(e),
                    "message_id": message.get("Message-ID", "unknown"),
                    "processed_at": datetime.now().isoformat()
                }
    
    # Pattern 3: WebSocket for Bidirectional Streaming
    async def websocket_email_stream(self, websocket: WebSocket):
        """
        WebSocket handler for real-time bidirectional email processing.
        Client can send emails in real-time and get instant classifications.
        """
        await websocket.accept()
        connection_id = uuid4().hex[:8]
        
        logger.info(f"WebSocket connection established: {connection_id}")
        
        try:
            while True:
                # Receive data from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message["type"] == "email_classify":
                    # Real-time email classification
                    result = await self._handle_realtime_classification(message["email_content"])
                    
                    await websocket.send_text(json.dumps({
                        "type": "classification_result",
                        "connection_id": connection_id,
                        "result": result,
                        "timestamp": datetime.now().isoformat()
                    }))
                
                elif message["type"] == "stream_mbox":
                    # Stream process an mbox file
                    await self._stream_mbox_via_websocket(websocket, message["file_path"], connection_id)
                
                elif message["type"] == "ping":
                    # Keepalive
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "connection_id": connection_id,
                        "timestamp": datetime.now().isoformat()
                    }))
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error {connection_id}: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": str(e),
                "connection_id": connection_id
            }))
    
    # Pattern 4: Streaming JSON Response for Large Results
    async def stream_json_response(self, mbox_file_path: str) -> StreamingResponse:
        """
        Stream large JSON responses without loading everything into memory.
        Perfect for APIs that need to return large datasets.
        """
        
        async def json_streamer():
            # Start JSON array
            yield '{"emails": ['
            
            first_item = True
            mbox = mailbox.mbox(mbox_file_path)
            
            async for email_result in self._process_emails_streaming(mbox):
                # Add comma separator except for first item
                if not first_item:
                    yield ","
                else:
                    first_item = False
                
                # Stream each email result as JSON
                yield json.dumps(email_result)
            
            # Close JSON array and add metadata
            yield '], "metadata": {'
            yield f'"stream_completed": "{datetime.now().isoformat()}",'
            yield f'"total_processed": {len(mbox)}'
            yield '}}'
        
        return StreamingResponse(
            json_streamer(),
            media_type="application/json",
            headers={"X-Stream-Type": "json-streaming"}
        )
    
    # Helper Methods
    async def _classify_email_streaming(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify email via streaming to ML worker."""
        try:
            email_content = f"Subject: {email_data['subject']}\nFrom: {email_data['from']}\nBody: {email_data['body'][:500]}"
            
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    f"{self.classifier_url}/classify",
                    data={
                        "email_content": email_content,
                        "classification_types": "spam_detection,bill_detection,receipt_detection"
                    },
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Classification failed: {response.status_code}"}
                    
        except Exception as e:
            return {"error": f"Classification error: {str(e)}"}
    
    async def _handle_realtime_classification(self, email_content: str) -> Dict[str, Any]:
        """Handle real-time email classification for WebSocket."""
        start_time = datetime.now()
        
        classification = await self._classify_email_streaming({"body": email_content, "subject": "", "from": ""})
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "classification": classification,
            "processing_time_ms": processing_time,
            "real_time": True
        }
    
    async def _stream_mbox_via_websocket(self, websocket: WebSocket, file_path: str, connection_id: str):
        """Stream mbox processing results via WebSocket."""
        try:
            mbox = mailbox.mbox(file_path)
            processed_count = 0
            
            async for email_result in self._process_emails_streaming(mbox):
                processed_count += 1
                
                await websocket.send_text(json.dumps({
                    "type": "mbox_stream_result",
                    "connection_id": connection_id,
                    "email_result": email_result,
                    "processed_count": processed_count,
                    "timestamp": datetime.now().isoformat()
                }))
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.05)
                
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "mbox_stream_error",
                "connection_id": connection_id,
                "error": str(e)
            }))
    
    def _extract_body(self, message) -> str:
        """Extract body text from email message."""
        try:
            if message.is_multipart():
                body_parts = []
                for part in message.walk():
                    if part.get_content_type() == "text/plain":
                        body_parts.append(part.get_payload(decode=True).decode('utf-8', errors='ignore'))
                return ' '.join(body_parts)[:1000]  # Limit body size
            else:
                return message.get_payload(decode=True).decode('utf-8', errors='ignore')[:1000]
        except:
            return ""


# ============================================================================
# STREAMING SERVICE
# ============================================================================

class CrankStreamingService:
    """Crank service that demonstrates all streaming patterns."""
    
    def __init__(self):
        self.app = FastAPI(title="Crank Streaming Service", version="1.0.0")
        self.processor = StreamingEmailProcessor()
        self.setup_routes()
    
    def setup_routes(self):
        """Setup streaming endpoints."""
        
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "service": "crank-streaming",
                "capabilities": ["sse_streaming", "websocket_streaming", "json_streaming"],
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/stream/emails/sse/{file_path:path}")
        async def stream_emails_sse(file_path: str, request: Request):
            """
            Stream email processing via Server-Sent Events.
            
            Usage:
            curl -N http://localhost:8011/stream/emails/sse/path/to/emails.mbox
            
            Or in JavaScript:
            const eventSource = new EventSource('/stream/emails/sse/emails.mbox');
            eventSource.onmessage = (event) => console.log(JSON.parse(event.data));
            """
            return await self.processor.stream_email_processing_sse(file_path, request)
        
        @self.app.get("/stream/emails/json/{file_path:path}")
        async def stream_emails_json(file_path: str):
            """
            Stream large JSON responses without buffering.
            
            Usage:
            curl http://localhost:8011/stream/emails/json/path/to/emails.mbox
            """
            return await self.processor.stream_json_response(file_path)
        
        @self.app.websocket("/ws/emails")
        async def websocket_emails(websocket: WebSocket):
            """
            WebSocket endpoint for real-time email processing.
            
            Usage:
            ws = new WebSocket('ws://localhost:8011/ws/emails');
            ws.send(JSON.stringify({
                type: 'email_classify',
                email_content: 'Subject: Test Email\\nBody: Hello world'
            }));
            """
            await self.processor.websocket_email_stream(websocket)
        
        @self.app.post("/stream/classify/realtime")
        async def realtime_classify(email_content: str):
            """
            Real-time email classification endpoint.
            Faster than batch processing for single emails.
            """
            result = await self.processor._handle_realtime_classification(email_content)
            return result


# Create service instance
streaming_service = CrankStreamingService()
app = streaming_service.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)