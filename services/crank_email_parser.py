"""Crank Email Parser Service - Refactored to use WorkerApplication.

Bulk email parsing service that integrates the parse-email-archive functionality
with the crank-platform mesh architecture. Provides high-performance streaming
parsing of email archives (mbox, eml) with mTLS security.
"""

import email
import logging
import mailbox
import os
import tempfile
from collections.abc import Iterator
from datetime import datetime, timezone
from email import policy
from typing import Any, Optional
from uuid import uuid4

import httpx
from fastapi import File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from crank.capabilities.schema import EMAIL_PARSING, CapabilityDefinition
from crank.worker_runtime import WorkerApplication

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI dependency defaults - create at module level to avoid evaluation in defaults
_DEFAULT_FILE_UPLOAD = File(...)

# Default keywords for receipt detection
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


class EmailParser:
    """Pure email parsing logic without infrastructure concerns."""

    def parse_mbox(self, file_content: bytes, request: EmailParseRequest) -> EmailParseResponse:
        """Parse mbox file using streaming parser."""
        start_time = datetime.now(timezone.utc)
        job_id = f"mbox-{uuid4().hex[:8]}"

        # Create temporary file for mailbox parsing
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(file_content)
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
        processing_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

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

    def parse_eml(self, file_content: bytes, request: EmailParseRequest) -> EmailParseResponse:
        """Parse single EML file."""
        start_time = datetime.now(timezone.utc)
        job_id = f"eml-{uuid4().hex[:8]}"

        # Read and parse EML
        message = email.message_from_bytes(file_content, policy=policy.default)  # type: ignore[arg-type]

        # Convert to our format
        parsed_message = self._message_to_record(
            message,
            keyword_list=request.keywords or DEFAULT_KEYWORDS,
            lowered_keywords=[(kw or "").lower() for kw in (request.keywords or DEFAULT_KEYWORDS)],
            body_snippet_chars=request.snippet_length,
        )

        messages = [parsed_message]
        receipt_count = 1 if parsed_message.get("is_receipt", False) else 0
        processing_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        return EmailParseResponse(
            job_id=job_id,
            status="completed",
            message_count=1,
            receipt_count=receipt_count,
            processing_time_ms=processing_time_ms,
            messages=messages,
            summary=self._generate_summary(messages),
        )

    def analyze_archive(
        self,
        file_content: bytes,
        request: EmailParseRequest,
    ) -> dict[str, Any]:
        """Analyze email archive for patterns and statistics."""
        # First parse the archive
        parse_response = self.parse_mbox(file_content, request)
        messages = parse_response.messages

        # Perform analysis
        analysis: dict[str, Any] = {
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
    ) -> Iterator[dict[str, Any]]:
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
        message: Any,  # Can be EmailMessage or mboxMessage
        *,
        keyword_list: list[str],
        lowered_keywords: list[str],
        body_snippet_chars: int,
    ) -> dict[str, Any]:
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
            "parsed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _get_body_text(self, message: Any) -> str:
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
                        parts.append(bytes(payload).decode(charset, errors="replace"))  # pyright: ignore[reportUnknownMemberType]
                    except LookupError:
                        parts.append(bytes(payload).decode("utf-8", errors="replace"))  # pyright: ignore[reportUnknownMemberType]
                    continue
                if isinstance(payload, str):
                    parts.append(payload)  # pyright: ignore[reportUnknownMemberType]
            return "\n".join(parts).strip()  # pyright: ignore[reportUnknownArgumentType]

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

    def _get_date_range(self, messages: list[dict[str, Any]]) -> dict[str, Optional[str]]:
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
        self,
        messages: list[dict[str, Any]],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Get top senders by message count."""
        sender_counts: dict[str, int] = {}
        for msg in messages:
            sender = msg.get("from", "Unknown")
            sender_counts[sender] = sender_counts.get(sender, 0) + 1

        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"sender": sender, "count": count} for sender, count in top_senders]

    def _get_common_keywords(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Get most common matched keywords."""
        keyword_counts: dict[str, int] = {}
        for msg in messages:
            for keyword in msg.get("matched_keywords", []):
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [{"keyword": keyword, "count": count} for keyword, count in top_keywords]

    def _analyze_subject_keywords(self, messages: list[dict[str, Any]]) -> dict[str, int]:
        """Analyze common words in email subjects."""
        word_counts: dict[str, int] = {}
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


class EmailParserWorker(WorkerApplication):
    """Email parser worker using WorkerApplication infrastructure.

    Provides email parsing capabilities:
    - Mbox archive parsing
    - EML file parsing
    - Archive analysis and statistics

    All infrastructure (registration, heartbeat, health checks, certificates)
    is handled by the WorkerApplication base class.
    """

    def __init__(self) -> None:
        """Initialize email parser worker."""
        super().__init__(
            service_name="crank-email-parser",
            https_port=int(os.getenv("EMAIL_PARSER_HTTPS_PORT", "8301")),
        )
        self.parser = EmailParser()

        # Controller registration
        self.controller_url = os.getenv("CONTROLLER_URL")
        self.registered_with_controller = False

        if self.controller_url:
            logger.info("Controller URL configured: %s", self.controller_url)
        else:
            logger.info("No controller URL - running standalone")

    async def on_startup(self) -> None:
        """Register with controller on startup (if configured)."""
        await super().on_startup()

        if self.controller_url:
            await self._register_with_controller()

    async def _register_with_controller(self) -> None:
        """Send registration request to controller."""
        try:
            capabilities = [
                {
                    "name": cap.id,
                    "verb": "parse",
                    "version": f"{cap.version.major}.{cap.version.minor}.{cap.version.patch}",
                    "input_schema": cap.contract.input_schema,
                    "output_schema": cap.contract.output_schema,
                }
                for cap in self.get_capabilities()
            ]

            registration_payload = {
                "worker_id": self.worker_id,
                "worker_url": self.worker_url,
                "capabilities": capabilities,
            }

            logger.info("Registering with controller at %s", self.controller_url)
            ssl_config = self.cert_manager.get_ssl_context()

            async with httpx.AsyncClient(
                cert=(ssl_config["ssl_certfile"], ssl_config["ssl_keyfile"]),
                verify=ssl_config["ssl_ca_certs"],
            ) as client:
                response = await client.post(
                    f"{self.controller_url}/register",
                    json=registration_payload,
                    timeout=10.0,
                )
                response.raise_for_status()
                result = response.json()
                self.registered_with_controller = True
                logger.info(
                    "✅ Registered with controller: %s capabilities",
                    result.get("capabilities_registered", 0)
                )
        except Exception as e:
            logger.error(
                "❌ Failed to register with controller: %s (continuing anyway)",
                str(e)
            )

    def get_capabilities(self) -> list[CapabilityDefinition]:
        """Return worker capabilities."""
        return [EMAIL_PARSING]

    def setup_routes(self) -> None:
        """Setup FastAPI routes for email parsing endpoints.

        IMPORTANT: Use explicit binding pattern self.app.METHOD("/path")(handler)
        instead of @self.app.METHOD decorators to avoid Pylance "not accessed" warnings.

        Pattern documented in:
        - src/crank/worker_runtime/base.py (lines 11-13, 187-192)
        - .vscode/AGENT_CONTEXT.md (FastAPI Route Handler Pattern section)
        """

        async def parse_mbox_file(
            file: UploadFile = _DEFAULT_FILE_UPLOAD,
            request_data: str = Form(...),
        ) -> EmailParseResponse:
            """Parse mbox email archive."""
            try:
                parse_request = EmailParseRequest.model_validate_json(request_data)
                content = await file.read()
                return self.parser.parse_mbox(content, parse_request)
            except Exception as e:
                logger.exception(f"Error parsing mbox: {e!s}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        async def parse_eml_file(
            file: UploadFile = _DEFAULT_FILE_UPLOAD,
            request_data: str = Form(...),
        ) -> EmailParseResponse:
            """Parse single EML file."""
            try:
                parse_request = EmailParseRequest.model_validate_json(request_data)
                content = await file.read()
                return self.parser.parse_eml(content, parse_request)
            except Exception as e:
                logger.exception(f"Error parsing EML: {e!s}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        async def analyze_email_archive(
            file: UploadFile = _DEFAULT_FILE_UPLOAD,
            request_data: str = Form(...),
        ) -> dict[str, Any]:
            """Analyze email archive patterns and statistics."""
            try:
                parse_request = EmailParseRequest.model_validate_json(request_data)
                content = await file.read()
                return self.parser.analyze_archive(content, parse_request)
            except Exception as e:
                logger.exception(f"Error analyzing archive: {e!s}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        # Explicit binding pattern
        self.app.post("/parse/mbox", response_model=EmailParseResponse)(parse_mbox_file)
        self.app.post("/parse/eml", response_model=EmailParseResponse)(parse_eml_file)
        self.app.post("/analyze/archive")(analyze_email_archive)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


# Create worker instance
worker = EmailParserWorker()
app = worker.app


def main() -> None:
    """Main entry point - creates and runs email parser worker."""
    worker = EmailParserWorker()
    worker.run()


if __name__ == "__main__":
    main()
