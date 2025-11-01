"""
Crank Email Parser Service

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
    "transaction",
    "total",
    "amount due"
]

class EmailParseRequest(BaseModel):
    """Request model for email parsing operations."""
    keywords: Optional[List[str]] = None
    snippet_length: int = 200
    max_messages: Optional[int] = None
    output_format: str = "jsonl"

class EmailParseResponse(BaseModel):
    """Response model for email parsing operations."""
    job_id: str
    status: str
    message_count: int
    receipt_count: int
    processing_time_ms: float
    messages: List[Dict[str, Any]]
    summary: Dict[str, Any]

class CrankEmailParserService:
    """Email parser service implementing crank-platform mesh interface."""
    
    def __init__(self):
        self.app = FastAPI(title="Crank Email Parser", version="1.0.0")
        self.service_id = f"email-parser-{uuid4().hex[:8]}"
        # Configure platform integration
        self.platform_url = os.getenv("PLATFORM_URL", "https://localhost:8000")
        self.setup_routes()
        
    def setup_routes(self):
        """Setup FastAPI routes for the service."""
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "service": "crank-email-parser",
                "service_id": self.service_id,
                "capabilities": ["mbox_parsing", "eml_parsing", "bulk_processing"]
            }
        
        @self.app.post("/parse/mbox", response_model=EmailParseResponse)
        async def parse_mbox_file(
            file: UploadFile = File(...),
            request_data: str = Form(...)
        ):
            """Parse mbox email archive."""
            try:
                parse_request = EmailParseRequest.parse_raw(request_data)
                return await self._parse_mbox(file, parse_request)
            except Exception as e:
                logger.error(f"Error parsing mbox: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/parse/eml", response_model=EmailParseResponse)
        async def parse_eml_file(
            file: UploadFile = File(...),
            request_data: str = Form(...)
        ):
            """Parse single EML file."""
            try:
                parse_request = EmailParseRequest.parse_raw(request_data)
                return await self._parse_eml(file, parse_request)
            except Exception as e:
                logger.error(f"Error parsing EML: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/analyze/archive")
        async def analyze_email_archive(
            file: UploadFile = File(...),
            request_data: str = Form(...)
        ):
            """Analyze email archive patterns and statistics."""
            try:
                parse_request = EmailParseRequest.parse_raw(request_data)
                return await self._analyze_archive(file, parse_request)
            except Exception as e:
                logger.error(f"Error analyzing archive: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

    async def _parse_mbox(self, file: UploadFile, request: EmailParseRequest) -> EmailParseResponse:
        """Parse mbox file using streaming parser."""
        start_time = datetime.now()
        job_id = f"mbox-{uuid4().hex[:8]}"
        
        # Read file content
        content = await file.read()
        
        # Create temporary file for mailbox parsing
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(content)
            temp_file.flush()
            
            # Use the streaming parser logic
            messages = list(self._iter_parsed_messages(
                temp_file.name,
                keywords=request.keywords or DEFAULT_KEYWORDS,
                body_snippet_chars=request.snippet_length,
                max_messages=request.max_messages
            ))
        
        # Calculate metrics
        receipt_count = sum(1 for msg in messages if msg.get('is_receipt', False))
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Generate summary
        summary = self._generate_summary(messages)
        
        return EmailParseResponse(
            job_id=job_id,
            status="completed",
            message_count=len(messages),
            receipt_count=receipt_count,
            processing_time_ms=processing_time_ms,
            messages=messages,
            summary=summary
        )

    async def _parse_eml(self, file: UploadFile, request: EmailParseRequest) -> EmailParseResponse:
        """Parse single EML file."""
        start_time = datetime.now()
        job_id = f"eml-{uuid4().hex[:8]}"
        
        # Read and parse EML
        content = await file.read()
        message = email.message_from_bytes(content, policy=policy.default)
        
        # Convert to our format
        parsed_message = self._message_to_record(
            message,
            keyword_list=request.keywords or DEFAULT_KEYWORDS,
            lowered_keywords=[(kw or "").lower() for kw in (request.keywords or DEFAULT_KEYWORDS)],
            body_snippet_chars=request.snippet_length
        )
        
        messages = [parsed_message]
        receipt_count = 1 if parsed_message.get('is_receipt', False) else 0
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return EmailParseResponse(
            job_id=job_id,
            status="completed", 
            message_count=1,
            receipt_count=receipt_count,
            processing_time_ms=processing_time_ms,
            messages=messages,
            summary=self._generate_summary(messages)
        )

    async def _analyze_archive(self, file: UploadFile, request: EmailParseRequest) -> Dict[str, Any]:
        """Analyze email archive for patterns and statistics."""
        # First parse the archive
        parse_response = await self._parse_mbox(file, request)
        messages = parse_response.messages
        
        # Perform analysis
        analysis = {
            "total_messages": len(messages),
            "receipt_ratio": parse_response.receipt_count / len(messages) if messages else 0,
            "date_range": self._get_date_range(messages),
            "top_senders": self._get_top_senders(messages, limit=10),
            "subject_keywords": self._analyze_subject_keywords(messages),
            "size_distribution": self._analyze_message_sizes(messages),
            "temporal_distribution": self._analyze_temporal_patterns(messages)
        }
        
        return {
            "job_id": parse_response.job_id,
            "status": "completed",
            "analysis": analysis,
            "processing_time_ms": parse_response.processing_time_ms
        }

    def _iter_parsed_messages(
        self,
        mbox_path: str,
        *,
        keywords: List[str],
        body_snippet_chars: int = 200,
        max_messages: Optional[int] = None
    ) -> Iterator[dict]:
        """Yield parsed message records from an mbox file."""
        keyword_list = list(keywords)
        lowered_keywords = [kw.lower() for kw in keyword_list]

        mbox = mailbox.mbox(str(mbox_path))
        try:
            for i, message in enumerate(mbox):
                if max_messages and i >= max_messages:
                    break
                    
                yield self._message_to_record(
                    message,
                    keyword_list=keyword_list,
                    lowered_keywords=lowered_keywords,
                    body_snippet_chars=body_snippet_chars,
                )
        finally:
            mbox.close()

    def _message_to_record(
        self,
        message,
        *,
        keyword_list: List[str],
        lowered_keywords: List[str],
        body_snippet_chars: int,
    ) -> dict:
        """Convert email message to structured record."""
        header_from = str(message.get("From") or "").strip()
        header_subject = str(message.get("Subject") or "").strip()
        header_date = str(message.get("Date") or "").strip()
        message_id = str(message.get("Message-ID") or "").strip() or None

        body_text = self._get_body_text(message)
        snippet = self._build_snippet(body_text, body_snippet_chars)

        searchable_text = " ".join(part for part in (header_subject, body_text) if part).lower()

        matched_keywords = [
            keyword_list[idx]
            for idx, lowered in enumerate(lowered_keywords)
            if lowered in searchable_text
        ]

        return {
            "message_id": message_id,
            "from": header_from,
            "date": header_date,
            "subject": header_subject,
            "body_snippet": snippet,
            "is_receipt": bool(matched_keywords),
            "matched_keywords": matched_keywords,
            "body_length": len(body_text),
            "parsed_at": datetime.now().isoformat()
        }

    def _get_body_text(self, message) -> str:
        """Extract plaintext body from message."""
        if message.is_multipart():
            parts = []
            for part in message.walk():
                if part.get_content_type() != "text/plain":
                    continue
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                if isinstance(payload, (bytes, bytearray)):
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        parts.append(bytes(payload).decode(charset, errors="replace"))
                    except LookupError:
                        parts.append(bytes(payload).decode("utf-8", errors="replace"))
                    continue
                if isinstance(payload, str):
                    parts.append(payload)
            return "\n".join(parts).strip()

        payload = message.get_payload(decode=True)
        if payload is None:
            payload = message.get_payload()

        if isinstance(payload, (bytes, bytearray)):
            charset = message.get_content_charset() or "utf-8"
            try:
                return bytes(payload).decode(charset, errors="replace").strip()
            except LookupError:
                return bytes(payload).decode("utf-8", errors="replace").strip()

        if isinstance(payload, str):
            return payload.strip()

        return ""

    def _build_snippet(self, body_text: str, max_chars: int) -> str:
        """Build a snippet from body text."""
        if len(body_text) <= max_chars:
            return body_text
        return body_text[:max_chars].rsplit(" ", 1)[0] + "..."

    def _generate_summary(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics from parsed messages."""
        if not messages:
            return {}
        
        return {
            "date_range": self._get_date_range(messages),
            "top_senders": self._get_top_senders(messages, limit=5),
            "receipt_percentage": (sum(1 for m in messages if m.get('is_receipt', False)) / len(messages)) * 100,
            "average_body_length": sum(m.get('body_length', 0) for m in messages) / len(messages),
            "most_common_keywords": self._get_common_keywords(messages)
        }

    def _get_date_range(self, messages: List[Dict[str, Any]]) -> Dict[str, str]:
        """Get date range from messages."""
        dates = [m.get('date', '') for m in messages if m.get('date')]
        if not dates:
            return {"earliest": None, "latest": None}
        
        # Simple date extraction (could be improved with proper parsing)
        return {
            "earliest": min(dates) if dates else None,
            "latest": max(dates) if dates else None,
            "total_span_days": "unknown"  # Would need proper date parsing
        }

    def _get_top_senders(self, messages: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """Get top senders by message count."""
        sender_counts = {}
        for msg in messages:
            sender = msg.get('from', 'Unknown')
            sender_counts[sender] = sender_counts.get(sender, 0) + 1
        
        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"sender": sender, "count": count} for sender, count in top_senders]

    def _get_common_keywords(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get most common matched keywords."""
        keyword_counts = {}
        for msg in messages:
            for keyword in msg.get('matched_keywords', []):
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [{"keyword": keyword, "count": count} for keyword, count in top_keywords]

    def _analyze_subject_keywords(self, messages: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze common words in email subjects."""
        word_counts = {}
        for msg in messages:
            subject = msg.get('subject', '').lower()
            words = subject.split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        # Return top 10 words
        return dict(sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10])

    def _analyze_message_sizes(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze message size distribution."""
        sizes = [msg.get('body_length', 0) for msg in messages]
        if not sizes:
            return {}
        
        return {
            "min_size": min(sizes),
            "max_size": max(sizes),
            "average_size": sum(sizes) / len(sizes),
            "total_size": sum(sizes)
        }

    def _analyze_temporal_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal patterns in messages."""
        # This is a simplified analysis - could be enhanced with proper date parsing
        return {
            "analysis_note": "Temporal analysis requires enhanced date parsing",
            "message_count_by_period": "not_implemented"
        }

    async def register_with_platform(self):
        """Register this service with the crank platform."""
        registration_data = {
            "service_id": self.service_id,
            "service_type": "email-parser",
            "service_name": "Crank Email Parser",
            "version": "1.0.0",
            "capabilities": [
                "mbox_parsing",
                "eml_parsing", 
                "bulk_processing",
                "archive_analysis"
            ],
            "endpoints": {
                "health": "/health",
                "parse_mbox": "/parse/mbox",
                "parse_eml": "/parse/eml",
                "analyze": "/analyze/archive"
            },
            "status": "active"
        }

        try:
            # Get SSL context for mTLS
            ssl_context = self._get_ssl_context()
            
            # Get auth token for platform
            auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "dev-mesh-key")
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_token}"
            }
            
            async with httpx.AsyncClient(verify=ssl_context) as client:
                response = await client.post(
                    f"{self.platform_url}/v1/workers/register",
                    json=registration_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully registered email parser service: {self.service_id}")
                    return response.json()
                else:
                    logger.error(f"Failed to register service: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error registering with platform: {str(e)}")
            return None

    def _get_ssl_context(self):
        """Get SSL context for mTLS communication."""
        import ssl
        
        context = ssl.create_default_context()
        
        # Load client certificate for mTLS
        cert_path = os.getenv("CLIENT_CERT_PATH", "/certs/client.crt")
        key_path = os.getenv("CLIENT_KEY_PATH", "/certs/client.key")
        ca_path = os.getenv("CA_CERT_PATH", "/certs/ca.crt")
        
        if os.path.exists(cert_path) and os.path.exists(key_path):
            context.load_cert_chain(cert_path, key_path)
            logger.info("Loaded client certificates for mTLS")
        
        if os.path.exists(ca_path):
            context.load_verify_locations(ca_path)
            logger.info("Loaded CA certificate")
        else:
            # For development, allow self-signed certificates
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
        return context

# Create service instance
email_parser_service = CrankEmailParserService()
app = email_parser_service.app

# Startup event
@app.on_event("startup")
async def startup_event():
    """Register with platform on startup."""
    logger.info("Starting Crank Email Parser Service...")
    
    # Wait a bit for the platform to be ready
    await asyncio.sleep(5)
    
    # Register with platform
    registration_result = await email_parser_service.register_with_platform()
    if registration_result:
        logger.info("Email parser service registered successfully")
    else:
        logger.warning("Failed to register with platform - running in standalone mode")

if __name__ == "__main__":
    import uvicorn
    
    # Configure for mTLS
    ssl_keyfile = os.getenv("SSL_KEYFILE", "/certs/server.key")
    ssl_certfile = os.getenv("SSL_CERTFILE", "/certs/server.crt")
    ssl_ca_certs = os.getenv("SSL_CA_CERTS", "/certs/ca.crt")
    
    # Run with or without SSL based on certificate availability
    # 🚢 PORT CONFIGURATION: Use environment variables for flexible deployment
    service_port = int(os.getenv("EMAIL_PARSER_PORT", "8300"))  # New default: 8300
    service_host = os.getenv("EMAIL_PARSER_HOST", "0.0.0.0")
    https_port = int(os.getenv("EMAIL_PARSER_HTTPS_PORT", "8443"))
    
    if os.path.exists(ssl_certfile) and os.path.exists(ssl_keyfile):
        logger.info(f"Starting with mTLS enabled on port {https_port}")
        uvicorn.run(
            app,
            host=service_host,
            port=https_port,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            ssl_ca_certs=ssl_ca_certs if os.path.exists(ssl_ca_certs) else None,
            ssl_cert_reqs=2  # CERT_REQUIRED for mTLS
        )
    else:
        logger.info(f"Starting without SSL on port {service_port} (development mode)")
        uvicorn.run(app, host=service_host, port=service_port)