"""Crank Document Converter Service - Refactored to use WorkerApplication.

Document conversion service providing format transformation using Pandoc.
Supports PDF, DOCX, TXT, HTML, Markdown, and more.
"""

import base64
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from fastapi import File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from crank.capabilities.schema import DOCUMENT_CONVERSION, CapabilityDefinition
from crank.worker_runtime import WorkerApplication

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI dependency defaults - create at module level to avoid evaluation in defaults
_DEFAULT_FILE_UPLOAD = File(...)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class ConversionResponse(BaseModel):
    """Model for document conversion responses."""

    conversion_id: str
    status: str
    output_format: str
    message: str


# ============================================================================
# DOCUMENT CONVERSION ENGINE - BUSINESS LOGIC
# ============================================================================


class DocumentConverter:
    """Pure document conversion logic using Pandoc.

    This is the core business logic - pure conversion functionality with no infrastructure.
    Handles format detection and Pandoc-based conversion.
    """

    def detect_format(self, content: bytes, filename: Optional[str] = None) -> str:
        """Detect document format from content and filename."""
        if filename:
            ext = Path(filename).suffix.lower()
            format_map = {
                ".md": "markdown",
                ".txt": "plain",
                ".html": "html",
                ".htm": "html",
                ".pdf": "pdf",
                ".docx": "docx",
                ".doc": "doc",
                ".odt": "odt",
                ".rtf": "rtf",
            }
            if ext in format_map:
                return format_map[ext]

        # Try to detect from content
        content_str = content[:1024].decode("utf-8", errors="ignore").lower()

        if content_str.startswith("<!doctype html") or "<html" in content_str:
            return "html"
        if content_str.startswith("#") or "**" in content_str:
            return "markdown"
        return "plain"

    def convert_document(
        self,
        input_content: bytes,
        input_format: str,
        output_format: str,
        options: Optional[dict[str, Any]] = None,
    ) -> bytes:
        """Convert document using pandoc."""
        options = options or {}

        with tempfile.NamedTemporaryFile(suffix=f".{input_format}", delete=False) as input_file:
            input_file.write(input_content)
            input_file.flush()

            with tempfile.NamedTemporaryFile(
                suffix=f".{output_format}",
                delete=False,
            ) as output_file:
                try:
                    # Build pandoc command
                    cmd = [
                        "pandoc",
                        "-f",
                        input_format,
                        "-t",
                        output_format,
                        "-o",
                        output_file.name,
                        input_file.name,
                    ]

                    # Add common options
                    if output_format == "pdf":
                        cmd.extend(["--pdf-engine=xelatex"])

                    # Run conversion
                    result = subprocess.run(
                        cmd,
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    if result.returncode != 0:
                        raise Exception(f"Pandoc error: {result.stderr}")

                    # Read converted content
                    with open(output_file.name, "rb") as f:
                        return f.read()

                finally:
                    # Cleanup temp files
                    try:
                        os.unlink(input_file.name)
                        os.unlink(output_file.name)
                    except Exception:
                        pass


# ============================================================================
# WORKER APPLICATION
# ============================================================================


class DocumentConverterWorker(WorkerApplication):
    """Document conversion worker using Pandoc.

    Provides document format conversion:
    - PDF, DOCX, HTML, Markdown, Plain text, ODT, RTF
    - Format auto-detection
    - Pandoc integration

    All infrastructure (registration, heartbeat, health checks, certificates)
    is handled by the WorkerApplication base class.
    """

    def __init__(self) -> None:
        """Initialize document converter worker."""
        super().__init__(
            service_name="crank-doc-converter",
            https_port=int(os.getenv("DOC_CONVERTER_HTTPS_PORT", "8100")),
        )

        # Initialize conversion engine (business logic)
        self.converter = DocumentConverter()

    def get_capabilities(self) -> list[CapabilityDefinition]:
        """Return worker capabilities."""
        return [DOCUMENT_CONVERSION]

    def setup_routes(self) -> None:
        """Set up document conversion routes.

        IMPORTANT: Use explicit binding pattern self.app.METHOD("/path")(handler)
        instead of @self.app.METHOD decorators to avoid Pylance "not accessed" warnings.

        Pattern documented in:
        - src/crank/worker_runtime/base.py (lines 11-13, 187-192)
        - .vscode/AGENT_CONTEXT.md (FastAPI Route Handler Pattern section)
        """

        # Conversion endpoint - accepts Form data with file upload
        async def convert_document_endpoint(
            file: UploadFile = _DEFAULT_FILE_UPLOAD,
            output_format: str = Form(...),
            input_format: Optional[str] = Form(None),
        ) -> dict[str, Any]:
            """Convert uploaded document to specified format."""
            try:
                # Read file content
                content = await file.read()

                # Detect input format if not specified
                if not input_format:
                    input_format = self.converter.detect_format(content, file.filename)

                logger.info(f"Converting {file.filename} from {input_format} to {output_format}")

                # Perform conversion
                converted_content = self.converter.convert_document(
                    content, input_format, output_format
                )

                conversion_id = str(uuid4())

                # For now, return base64 encoded content
                encoded_content = base64.b64encode(converted_content).decode("utf-8")

                return ConversionResponse(
                    conversion_id=conversion_id,
                    status="completed",
                    output_format=output_format,
                    message=f"Successfully converted {file.filename} to {output_format}",
                ).model_dump() | {"content": encoded_content}

            except Exception as e:
                logger.exception(f"Conversion failed: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        # Supported formats endpoint
        async def supported_formats() -> dict[str, list[str]]:
            """Get supported input and output formats."""
            return {
                "input_formats": [
                    "markdown",
                    "html",
                    "docx",
                    "odt",
                    "rtf",
                    "plain",
                    "pdf",
                ],
                "output_formats": [
                    "markdown",
                    "html",
                    "docx",
                    "odt",
                    "rtf",
                    "plain",
                    "pdf",
                ],
            }

        # Explicit binding pattern
        self.app.post("/convert")(convert_document_endpoint)
        self.app.get("/formats")(supported_formats)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    """Main entry point - creates and runs document converter worker."""
    worker = DocumentConverterWorker()
    worker.run()


if __name__ == "__main__":
    main()
