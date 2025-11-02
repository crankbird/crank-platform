#!/usr/bin/env python3
"""
Crank Email Parser Service - REFACTORED with Worker Certificate Library

Bulk email parsing service that integrates the parse-email-archive functionality
with the crank-platform mesh architecture. Provides high-performance streaming
parsing of email archives (mbox, eml) with mTLS security.
"""

import asyncio
import json
import logging
import os
import tempfile
import mailbox
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterator
from uuid import uuid4
from datetime import datetime
import email
from email import policy
import io

import httpx
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from pydantic import BaseModel

# Import worker certificate library
from worker_cert_pattern import WorkerCertificatePattern, create_worker_fastapi_with_certs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the existing parse_mbox functionality
DEFAULT_KEYWORDS = [
    "receipt",
    "invoice", 
    "order confirmation",
    "payment confirmation",
    "statement",
    "bill",
    "purchase",
    "payment",
    "subscription",
    "delivery",
    "shipping",
    "refund"
]

# Pydantic models
class EmailParseRequest(BaseModel):
    """Request model for email parsing."""
    keywords: Optional[List[str]] = None
    snippet_length: int = 200
    max_messages: Optional[int] = None
    include_body: bool = True
    filter_receipts_only: bool = False

class EmailParseResponse(BaseModel):
    """Response model for email parsing."""
    job_id: str
    status: str
    message_count: int
    receipt_count: int
    processing_time_ms: float
    messages: List[Dict[str, Any]]
    summary: Dict[str, Any]

class WorkerRegistration(BaseModel):
    """Worker registration model."""
    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: List[str]


class EmailParseEngine:
    """Core email parsing engine extracted from parse-email-archive."""
    
    def __init__(self):
        """Initialize the parsing engine."""
        self.temp_dir = Path(tempfile.gettempdir()) / "crank_email_parser"
        self.temp_dir.mkdir(exist_ok=True)
    
    def parse_mbox_stream(self, file_path: str, keywords: List[str], 
                         snippet_length: int = 200, max_messages: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """Stream parse mbox file."""
        lowered_keywords = [kw.lower() for kw in keywords]
        
        try:
            mbox = mailbox.mbox(file_path)
            count = 0
            
            for message in mbox:
                if max_messages and count >= max_messages:
                    break
                    
                try:
                    parsed = self._message_to_record(message, keywords, lowered_keywords, snippet_length)
                    yield parsed
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to parse message {count}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to open mbox file: {e}")
            raise
    
    def parse_eml(self, content: bytes, keywords: List[str], snippet_length: int = 200) -> Dict[str, Any]:
        """Parse single EML message."""
        lowered_keywords = [kw.lower() for kw in keywords]
        message = email.message_from_bytes(content, policy=policy.default)
        return self._message_to_record(message, keywords, lowered_keywords, snippet_length)
    
    def _message_to_record(self, message, keyword_list: List[str], 
                          lowered_keywords: List[str], body_snippet_chars: int) -> Dict[str, Any]:
        """Convert email message to structured record."""
        
        # Extract basic fields
        subject = message.get('Subject', '') or ''
        from_addr = message.get('From', '') or ''
        to_addr = message.get('To', '') or ''
        date_str = message.get('Date', '') or ''
        message_id = message.get('Message-ID', '') or ''
        
        # Extract body
        body = self._extract_body(message)
        body_snippet = body[:body_snippet_chars] if body else ''
        
        # Check for receipts/keywords
        search_text = f"{subject} {body}".lower()
        is_receipt = any(keyword in search_text for keyword in lowered_keywords)
        matched_keywords = [kw for kw in keyword_list if kw.lower() in search_text]
        
        return {
            'message_id': message_id,
            'subject': subject,
            'from': from_addr,
            'to': to_addr,
            'date': date_str,
            'body_snippet': body_snippet,
            'body_length': len(body) if body else 0,
            'is_receipt': is_receipt,
            'matched_keywords': matched_keywords,
            'timestamp': datetime.now().isoformat()
        }
    
    def _extract_body(self, message) -> str:
        """Extract plain text body from email message."""
        try:
            if message.is_multipart():
                for part in message.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            return payload.decode('utf-8', errors='ignore')
            else:
                payload = message.get_payload(decode=True)
                if payload:
                    return payload.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"Failed to extract body: {e}")
        
        return ""
    
    def generate_summary(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate parsing summary."""
        if not messages:
            return {"total": 0, "receipts": 0, "keywords": {}}
        
        receipt_count = sum(1 for msg in messages if msg.get('is_receipt', False))
        
        # Count keyword occurrences
        keyword_counts = {}
        for msg in messages:
            for keyword in msg.get('matched_keywords', []):
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        return {
            "total": len(messages),
            "receipts": receipt_count,
            "receipt_percentage": (receipt_count / len(messages)) * 100,
            "keywords": keyword_counts,
            "avg_body_length": sum(msg.get('body_length', 0) for msg in messages) / len(messages)
        }


def setup_email_parser_routes(app: FastAPI, worker_config: dict):
    """Set up email parser routes using worker config."""
    
    # Get components from worker config
    cert_store = worker_config["cert_store"]
    platform_url = worker_config["platform_url"]
    worker_url = worker_config["worker_url"]
    service_name = worker_config["service_name"]
    
    # Initialize email parser engine
    parser_engine = EmailParseEngine()
    
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
            "capabilities": ["mbox_parsing", "eml_parsing", "bulk_processing", "receipt_detection"],
            "supported_formats": ["mbox", "eml"],
            "security": security_status,
            "timestamp": datetime.now().isoformat()
        }
    
    @app.post("/parse/mbox", response_model=EmailParseResponse)
    async def parse_mbox_file(
        file: UploadFile = File(...),
        request_data: str = Form(...)
    ):
        """Parse mbox email archive."""
        start_time = datetime.now()
        job_id = f"mbox-{uuid4().hex[:8]}"
        
        try:
            parse_request = EmailParseRequest.parse_raw(request_data)
            
            # Read uploaded file content
            content = await file.read()
            
            # Create temporary file for mailbox parsing
            with tempfile.NamedTemporaryFile() as temp_file:
                temp_file.write(content)
                temp_file.flush()
                
                # Use the streaming parser logic
                messages = list(parser_engine.parse_mbox_stream(
                    temp_file.name,
                    keywords=parse_request.keywords or DEFAULT_KEYWORDS,
                    snippet_length=parse_request.snippet_length,
                    max_messages=parse_request.max_messages
                ))
            
            # Filter receipts only if requested
            if parse_request.filter_receipts_only:
                messages = [msg for msg in messages if msg.get('is_receipt', False)]
            
            # Calculate metrics
            receipt_count = sum(1 for msg in messages if msg.get('is_receipt', False))
            processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Generate summary
            summary = parser_engine.generate_summary(messages)
            
            return EmailParseResponse(
                job_id=job_id,
                status="completed",
                message_count=len(messages),
                receipt_count=receipt_count,
                processing_time_ms=processing_time_ms,
                messages=messages,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error parsing mbox: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/parse/eml", response_model=EmailParseResponse)
    async def parse_eml_file(
        file: UploadFile = File(...),
        request_data: str = Form(...)
    ):
        """Parse single EML file."""
        start_time = datetime.now()
        job_id = f"eml-{uuid4().hex[:8]}"
        
        try:
            parse_request = EmailParseRequest.parse_raw(request_data)
            
            # Read and parse EML
            content = await file.read()
            parsed_message = parser_engine.parse_eml(
                content,
                keywords=parse_request.keywords or DEFAULT_KEYWORDS,
                snippet_length=parse_request.snippet_length
            )
            
            messages = [parsed_message]
            receipt_count = 1 if parsed_message.get('is_receipt', False) else 0
            processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            summary = parser_engine.generate_summary(messages)
            
            return EmailParseResponse(
                job_id=job_id,
                status="completed",
                message_count=1,
                receipt_count=receipt_count,
                processing_time_ms=processing_time_ms,
                messages=messages,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error parsing EML: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/capabilities")
    async def get_capabilities():
        """Get parser capabilities."""
        return {
            "supported_formats": ["mbox", "eml"],
            "features": [
                "bulk_mbox_parsing",
                "individual_eml_parsing", 
                "receipt_detection",
                "keyword_matching",
                "streaming_processing",
                "body_snippet_extraction"
            ],
            "default_keywords": DEFAULT_KEYWORDS,
            "max_snippet_length": 1000
        }
    
    async def _startup():
        """Startup handler - register with platform."""
        nonlocal worker_id
        
        logger.info("📧 Starting Crank Email Parser...")
        logger.info("🔐 Using certificates loaded synchronously at startup")
        
        # Prepare registration info
        worker_info = WorkerRegistration(
            worker_id=f"email-parser-{uuid4().hex[:8]}",
            service_type="email_parsing",
            endpoint=worker_url,
            health_url=f"{worker_url}/health",
            capabilities=["mbox_parsing", "eml_parsing", "bulk_processing", "receipt_detection"]
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
                        logger.info(f"🔒 Successfully registered email parser via mTLS. Worker ID: {worker_info.worker_id}")
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
                            "service_type": "email_parsing",
                            "load_score": 0.3  # Simulated load
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
                logger.info("🔒 Successfully deregistered email parser via mTLS")
            except Exception as e:
                logger.warning(f"Failed to deregister from platform: {e}")
    
    # Register startup/shutdown handlers
    app.add_event_handler("startup", _startup)
    app.add_event_handler("shutdown", _shutdown)


def create_crank_email_parser(cert_store=None):
    """Create the Crank Email Parser application with optional certificate store."""
    # This is kept for backward compatibility but now uses the worker library pattern
    worker_config = {
        "app": FastAPI(title="Crank Email Parser", version="1.0.0"),
        "cert_store": cert_store,
        "platform_url": os.getenv("PLATFORM_URL", "https://platform:8443"),
        "worker_url": os.getenv("WORKER_URL", "https://crank-email-parser:8301"),
        "service_name": "crank-email-parser"
    }
    
    setup_email_parser_routes(worker_config["app"], worker_config)
    return worker_config["app"]


def main():
    """Main entry point using Worker Certificate Library."""
    
    # Step 1: Initialize certificates SYNCHRONOUSLY using library
    cert_pattern = WorkerCertificatePattern("crank-email-parser")
    cert_store = cert_pattern.initialize_certificates()
    
    # Step 2: Create FastAPI with pre-loaded certificates using library
    worker_config = create_worker_fastapi_with_certs(
        title="Crank Email Parser",
        service_name="crank-email-parser",
        platform_url=None,  # Use default from environment
        worker_url=None,    # Use default from environment
        cert_store=cert_store
    )
    
    # Step 3: Setup email parser routes
    setup_email_parser_routes(worker_config["app"], worker_config)
    
    # Step 4: Start server with certificates using library
    https_port = int(os.getenv("EMAIL_PARSER_HTTPS_PORT", "8301"))
    cert_pattern.start_server(worker_config["app"], port=https_port)


# For direct running
if __name__ == "__main__":
    main()