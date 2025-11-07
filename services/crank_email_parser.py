"""
Crank Email Parser Service

Bulk email parsing service that integrates the parse-email-archive functionality
with the crank-platform mesh architecture. Provides high-performance streaming
parsing of email archives (mbox, eml) with mTLS security.
"""

import asyncio
import email
import logging
import mailbox
import os
import tempfile
from collections.abc import Iterator
from datetime import datetime
from email import policy
from typing import Any, Optional
from uuid import uuid4

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

# Import security configuration and models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Worker registration model
class WorkerRegistration(BaseModel):
    """Model for worker registration with platform."""

    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: list[str]


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
    "amount due",
]


class EmailParseRequest(BaseModel):
    """Request model for email parsing operations."""

    keywords: Optional[list[str]] = None
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
    messages: list[dict[str, Any]]
    summary: dict[str, Any]


class CrankEmailParserService:
    """Email parser service implementing crank-platform mesh interface."""

    def __init__(self):
        self.app = FastAPI(title="Crank Email Parser", version="1.0.0")

        # Worker registration configuration
        self.worker_id = f"email-parser-{uuid4().hex[:8]}"
        self.platform_url = os.getenv("PLATFORM_URL", "https://platform:8443")
        self.worker_url = (
            f"https://crank-email-parser:{os.getenv('EMAIL_PARSER_HTTPS_PORT', '8301')}"
        )
        self.platform_auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "dev-mesh-key")
        self.heartbeat_task = None

        # Legacy service_id for compatibility
        self.service_id = self.worker_id

        self.setup_routes()
        self.setup_startup()

    def setup_routes(self):
        """Setup FastAPI routes for the service."""

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "service": "crank-email-parser",
                "service_id": self.service_id,
                "capabilities": [
                    "mbox_parsing",
                    "eml_parsing",
                    "attachment_extraction",
                    "bulk_processing",
                ],
            }

        @self.app.get("/parse")
        async def parse_info():
            """Get information about available parsing endpoints."""
            return {
                "service": "crank-email-parser",
                "available_endpoints": {
                    "/parse/mbox": {
                        "method": "POST",
                        "description": "Parse mbox email archive files",
                        "accepts": ["multipart/form-data"],
                        "file_types": [".mbox"],
                    },
                    "/parse/eml": {
                        "method": "POST",
                        "description": "Parse single EML email files",
                        "accepts": ["multipart/form-data"],
                        "file_types": [".eml"],
                    },
                },
                "analysis_endpoints": {
                    "/analyze/archive": {
                        "method": "POST",
                        "description": "Analyze email archive patterns and statistics",
                        "accepts": ["multipart/form-data"],
                    },
                },
                "capabilities": [
                    "mbox_parsing",
                    "eml_parsing",
                    "attachment_extraction",
                    "bulk_processing",
                ],
            }

        @self.app.post("/parse/mbox", response_model=EmailParseResponse)
        async def parse_mbox_file(
            file: UploadFile = File(...),
            request_data: str = Form(...),
        ):
            """Parse mbox email archive."""
            try:
                parse_request = EmailParseRequest.parse_raw(request_data)
                return await self._parse_mbox(file, parse_request)
            except Exception as e:
                logger.exception("Error parsing mbox: {e!s}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/parse/eml", response_model=EmailParseResponse)
        async def parse_eml_file(
            file: UploadFile = File(...),
            request_data: str = Form(...),
        ):
            """Parse single EML file."""
            try:
                parse_request = EmailParseRequest.parse_raw(request_data)
                return await self._parse_eml(file, parse_request)
            except Exception as e:
                logger.exception("Error parsing EML: {e!s}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/analyze/archive")
        async def analyze_email_archive(
            file: UploadFile = File(...),
            request_data: str = Form(...),
        ):
            """Analyze email archive patterns and statistics."""
            try:
                parse_request = EmailParseRequest.parse_raw(request_data)
                return await self._analyze_archive(file, parse_request)
            except Exception as e:
                logger.exception("Error analyzing archive: {e!s}")
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
            messages = list(
                self._iter_parsed_messages(
                    temp_file.name,
                    keywords=request.keywords or DEFAULT_KEYWORDS,
                    body_snippet_chars=request.snippet_length,
                    max_messages=request.max_messages,
                ),
            )

        # Calculate metrics
        receipt_count = sum(1 for msg in messages if msg.get("is_receipt", False))
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
            summary=summary,
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
            body_snippet_chars=request.snippet_length,
        )

        messages = [parsed_message]
        receipt_count = 1 if parsed_message.get("is_receipt", False) else 0
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        return EmailParseResponse(
            job_id=job_id,
            status="completed",
            message_count=1,
            receipt_count=receipt_count,
            processing_time_ms=processing_time_ms,
            messages=messages,
            summary=self._generate_summary(messages),
        )

    async def _analyze_archive(
        self, file: UploadFile, request: EmailParseRequest,
    ) -> dict[str, Any]:
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
            "temporal_distribution": self._analyze_temporal_patterns(messages),
        }

        return {
            "job_id": parse_response.job_id,
            "status": "completed",
            "analysis": analysis,
            "processing_time_ms": parse_response.processing_time_ms,
        }

    def _iter_parsed_messages(
        self,
        mbox_path: str,
        *,
        keywords: list[str],
        body_snippet_chars: int = 200,
        max_messages: Optional[int] = None,
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
        keyword_list: list[str],
        lowered_keywords: list[str],
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
            "parsed_at": datetime.now().isoformat(),
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

    def _generate_summary(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate summary statistics from parsed messages."""
        if not messages:
            return {}

        return {
            "date_range": self._get_date_range(messages),
            "top_senders": self._get_top_senders(messages, limit=5),
            "receipt_percentage": (
                sum(1 for m in messages if m.get("is_receipt", False)) / len(messages)
            )
            * 100,
            "average_body_length": sum(m.get("body_length", 0) for m in messages) / len(messages),
            "most_common_keywords": self._get_common_keywords(messages),
        }

    def _get_date_range(self, messages: list[dict[str, Any]]) -> dict[str, str]:
        """Get date range from messages."""
        dates = [m.get("date", "") for m in messages if m.get("date")]
        if not dates:
            return {"earliest": None, "latest": None}

        # Simple date extraction (could be improved with proper parsing)
        return {
            "earliest": min(dates) if dates else None,
            "latest": max(dates) if dates else None,
            "total_span_days": "unknown",  # Would need proper date parsing
        }

    def _get_top_senders(
        self, messages: list[dict[str, Any]], limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Get top senders by message count."""
        sender_counts = {}
        for msg in messages:
            sender = msg.get("from", "Unknown")
            sender_counts[sender] = sender_counts.get(sender, 0) + 1

        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"sender": sender, "count": count} for sender, count in top_senders]

    def _get_common_keywords(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Get most common matched keywords."""
        keyword_counts = {}
        for msg in messages:
            for keyword in msg.get("matched_keywords", []):
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [{"keyword": keyword, "count": count} for keyword, count in top_keywords]

    def _analyze_subject_keywords(self, messages: list[dict[str, Any]]) -> dict[str, int]:
        """Analyze common words in email subjects."""
        word_counts = {}
        for msg in messages:
            subject = msg.get("subject", "").lower()
            words = subject.split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    word_counts[word] = word_counts.get(word, 0) + 1

        # Return top 10 words
        return dict(sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10])

    def _analyze_message_sizes(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze message size distribution."""
        sizes = [msg.get("body_length", 0) for msg in messages]
        if not sizes:
            return {}

        return {
            "min_size": min(sizes),
            "max_size": max(sizes),
            "average_size": sum(sizes) / len(sizes),
            "total_size": sum(sizes),
        }

    def _analyze_temporal_patterns(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze temporal patterns in messages."""
        # This is a simplified analysis - could be enhanced with proper date parsing
        return {
            "analysis_note": "Temporal analysis requires enhanced date parsing",
            "message_count_by_period": "not_implemented",
        }

    class _SecureHTTPClientManager:
        """Context manager for creating HTTP client with CA certificate verification."""

        def __init__(self, ca_service_url="https://cert-authority:9090"):
            self.ca_service_url = ca_service_url
            self.ca_cert_file = None
            self.client = None

        async def __aenter__(self):
            import ssl

            try:
                # Import the CA client to get fresh CA certificate
                import sys

                sys.path.append("/app/scripts")
                from crank_cert_initialize import CertificateAuthorityClient

                # Get CA certificate directly from the Certificate Authority Service
                ca_client = CertificateAuthorityClient(self.ca_service_url)
                ca_cert = await ca_client.get_ca_certificate()

                if ca_cert:
                    # Create SSL context with CA certificate
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False  # For development environment
                    ssl_context.verify_mode = ssl.CERT_REQUIRED

                    # Load CA certificate directly into SSL context
                    ssl_context.load_verify_locations(cadata=ca_cert)

                    # Configure httpx to use the SSL context
                    self.client = httpx.AsyncClient(
                        verify=ssl_context,
                        timeout=10.0,
                    )
                    logger.info("🔒 Created secure HTTP client with CA certificate verification")
                    return self.client
                # Fallback for development - disable verification
                logger.warning("⚠️ No CA certificate available, using insecure client")
                self.client = httpx.AsyncClient(verify=False, timeout=10.0)
                return self.client
            except Exception:
                logger.warning("Failed to access CA certificate: {e}, using insecure client")
                self.client = httpx.AsyncClient(verify=False, timeout=10.0)
                return self.client

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if self.client:
                await self.client.aclose()

    def _create_adaptive_client(self):
        """Create HTTP client context manager with CA certificate verification."""
        return self._SecureHTTPClientManager()

    def setup_startup(self):
        """Setup startup and shutdown events."""

        @self.app.on_event("startup")
        async def startup_event():
            """Initialize security and register with platform."""
            logger.info("📧 Starting Crank Email Parser Service...")

            # Certificate initialization handled in main() - just register
            await self._register_with_platform()

            logger.info("✅ Crank Email Parser Service startup complete!")

        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Cleanup on shutdown."""
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    logger.info("Heartbeat task cancelled")

    async def _register_with_platform(self):
        """Register this worker with the platform using mTLS."""
        worker_info = WorkerRegistration(
            worker_id=self.worker_id,
            service_type="email_parsing",
            endpoint=self.worker_url,
            health_url=f"{self.worker_url}/health",
            capabilities=[
                "mbox_parsing",
                "eml_parsing",
                "attachment_extraction",
                "bulk_processing",
                "archive_analysis",
            ],
        )

        # Try to register with retries
        max_retries = 5
        for attempt in range(max_retries):
            try:
                async with self._create_adaptive_client() as client:
                    response = await client.post(
                        f"{self.platform_url}/v1/workers/register",
                        json=worker_info.dict(),
                        headers={"Authorization": f"Bearer {self.platform_auth_token}"},
                    )
                    response.raise_for_status()
                    logger.info(
                        f"🔒 Successfully registered email parser service via mTLS. Worker ID: {self.worker_id}",
                    )

                    # Start heartbeat task
                    self._start_heartbeat_task()
                    return
            except Exception:
                logger.warning("Registration attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)

        logger.error("Failed to register with platform after all retries")

    def _start_heartbeat_task(self):
        """Start the background heartbeat task."""

        async def heartbeat_loop():
            while True:
                try:
                    await asyncio.sleep(int(os.getenv("WORKER_HEARTBEAT_INTERVAL", "20")))
                    await self._send_heartbeat()
                except asyncio.CancelledError:
                    logger.info("Heartbeat task cancelled")
                    break
                except Exception:
                    logger.exception("Heartbeat error: {e}")

        self.heartbeat_task = asyncio.create_task(heartbeat_loop())
        os.getenv("WORKER_HEARTBEAT_INTERVAL", "20")
        logger.info("🫀 Started heartbeat task with {heartbeat_interval}s interval")

    async def _send_heartbeat(self):
        """Send heartbeat to platform."""
        try:
            async with self._create_adaptive_client() as client:
                response = await client.post(
                    f"{self.platform_url}/v1/workers/{self.worker_id}/heartbeat",
                    data={
                        "service_type": "email_parsing",
                        "load_score": 0.3,  # Medium load for parsing service
                    },
                    headers={"Authorization": f"Bearer {self.platform_auth_token}"},
                )
                response.raise_for_status()
        except Exception:
            logger.warning("Heartbeat failed: {e}")


# Create service instance
email_parser_service = CrankEmailParserService()
app = email_parser_service.app


def main():
    """Main entry point with clean certificate initialization."""
    import uvicorn

    # Initialize certificates using SECURE CSR pattern
    https_only = os.getenv("HTTPS_ONLY", "true").lower() == "true"
    ca_service_url = os.getenv("CA_SERVICE_URL")

    if https_only and ca_service_url:
        logger.info("🔐 Initializing certificates using SECURE CSR pattern...")
        try:
            # Run secure certificate initialization in the same process
            import sys

            sys.path.append("/app/scripts")
            import asyncio

            from crank_cert_initialize import cert_store
            from crank_cert_initialize import main as init_certificates

            # Run secure certificate initialization
            asyncio.run(init_certificates())

            # Check if certificates were loaded
            if cert_store.platform_cert is None:
                raise RuntimeError(
                    "🚫 Certificate initialization completed but no certificates in memory",
                )

            logger.info("✅ Certificates loaded successfully using SECURE CSR pattern")
            logger.info("🔒 SECURITY: Private keys generated locally and never transmitted")

        except Exception:
            logger.exception("❌ Failed to initialize certificates with CA service: {e}")
            sys.exit(1)
    else:
        logger.error("🚫 HTTPS_ONLY environment requires Certificate Authority Service")
        sys.exit(1)

    # Start server with in-memory certificates
    service_port = int(os.getenv("EMAIL_PARSER_HTTPS_PORT", "8301"))
    service_host = os.getenv("EMAIL_PARSER_HOST", "0.0.0.0")

    logger.info("� Starting Crank Email Parser with HTTPS/mTLS ONLY on port {service_port}")
    logger.info("🔐 Using in-memory certificates from Certificate Authority Service")

    # Create SSL context from in-memory certificates (SECURE CSR pattern)
    try:
        cert_store.get_ssl_context()

        logger.info("🔒 Using certificates obtained via SECURE CSR pattern")

        # Get the temporary certificate file paths for uvicorn
        cert_file = cert_store._temp_cert_file
        key_file = cert_store._temp_key_file

        uvicorn.run(
            app,
            host=service_host,
            port=service_port,
            ssl_keyfile=key_file,
            ssl_certfile=cert_file,
        )
    except Exception:
        logger.exception("❌ Failed to start with certificates: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
