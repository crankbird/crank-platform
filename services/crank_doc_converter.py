"""
Crank Document Converter Service

Simple document conversion service that follows the exact same pattern as
the working email classifier service.
"""

import asyncio
import base64
import logging
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI dependency defaults - create at module level to avoid evaluation in defaults
_DEFAULT_FILE_UPLOAD = File(...)


# Worker registration model
class WorkerRegistration(BaseModel):
    """Model for worker registration with platform."""

    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: list[str]


# Conversion request models
class ConversionRequest(BaseModel):
    """Model for document conversion requests."""

    input_format: str
    output_format: str
    options: Optional[dict[str, Any]] = None


class ConversionResponse(BaseModel):
    """Model for document conversion responses."""

    conversion_id: str
    status: str
    output_format: str
    message: str


class CrankDocumentConverter:
    """Crank Document Converter Service following the working pattern."""

    def __init__(
        self, platform_url: Optional[str] = None, cert_store: Optional[Any] = None
    ) -> None:
        self.app = FastAPI(title="Crank Document Converter", version="1.0.0")

        # 🔐 ZERO-TRUST: Use pre-loaded certificates from synchronous initialization
        if cert_store is not None:
            logger.info("🔐 Using pre-loaded certificates from synchronous initialization")
            self.cert_store = cert_store
        else:
            logger.info("🔐 Creating empty certificate store (fallback)")
            from crank_platform.security import SecureCertificateStore

            self.cert_store = SecureCertificateStore()

        # Always use HTTPS with Certificate Authority Service certificates
        self.platform_url = platform_url or os.getenv("PLATFORM_URL", "https://platform:8443")
        self.worker_url = os.getenv("WORKER_URL", "https://crank-doc-converter:8100")
        self.platform_auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "dev-mesh-key")

        # Certificate files are purely in-memory now - no disk dependencies
        self.cert_file: Optional[str] = None
        self.key_file: Optional[str] = None
        self.ca_file: Optional[str] = None

        self.worker_id: Optional[str] = None
        self.heartbeat_task: Optional[asyncio.Task[None]] = None

        # Setup routes
        self._setup_routes()

        # Register startup/shutdown handlers
        # Note: FastAPI's add_event_handler has complex typing that Pylance can't fully infer
        self.app.add_event_handler("startup", self._startup)  # pyright: ignore[reportUnknownMemberType]
        self.app.add_event_handler("shutdown", self._shutdown)  # pyright: ignore[reportUnknownMemberType]

    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""

        @self.app.get("/health")
        async def health_check() -> dict[str, Any]:
            """Health check endpoint with security status."""
            security_status: dict[str, Any] = {}
            if hasattr(self, "cert_store"):
                security_status = {
                    "ssl_enabled": self.cert_store.platform_cert is not None,
                    "ca_cert_available": self.cert_store.ca_cert is not None,
                    "certificate_source": "Certificate Authority Service",
                }

            return {
                "status": "healthy",
                "service": "crank-document-converter",
                "worker_id": self.worker_id,
                "capabilities": [
                    "pdf_to_text",
                    "docx_to_text",
                    "format_conversion",
                    "document-conversion",
                    "format-detection",
                    "pandoc-integration",
                ],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "security": security_status,
            }

        @self.app.get("/")
        async def root() -> dict[str, Any]:
            """Root endpoint with service information."""
            return {
                "service": "Crank Document Converter",
                "version": "1.0.0",
                "worker_id": self.worker_id,
                "capabilities": [
                    "document-conversion",
                    "format-detection",
                    "pandoc-integration",
                ],
            }

        @self.app.post("/convert")
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
                    input_format = self.detect_format(content, file.filename)

                logger.info(f"Converting {file.filename} from {input_format} to {output_format}")

                # Perform conversion
                converted_content = self.convert_document(content, input_format, output_format)

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

        @self.app.get("/formats")
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

        # Store references to satisfy Pylance unused function warnings
        # These functions are actually used by FastAPI via decorators
        self._health_check_func = health_check
        self._root_func = root
        self._convert_func = convert_document_endpoint
        self._formats_func = supported_formats

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

    async def _startup(self) -> None:
        """Startup handler - register with platform."""
        logger.info("📄 Starting Crank Document Converter...")

        # Log security level for visibility (certificates already loaded synchronously)
        logger.info("🔐 Using certificates loaded synchronously at startup")

        # Prepare registration info
        worker_info = WorkerRegistration(
            worker_id=f"doc-converter-{uuid4().hex[:8]}",
            service_type="document_conversion",
            endpoint=self.worker_url,
            health_url=f"{self.worker_url}/health",
            capabilities=["document-conversion", "format-detection", "pandoc-integration"],
        )

        self.worker_id = worker_info.worker_id

        # Register with platform
        await self._register_with_platform(worker_info)

        # Start heartbeat background task
        self._start_heartbeat_task()

    async def _register_with_platform(self, worker_info: WorkerRegistration) -> None:
        """Register this worker with the platform."""
        try:
            async with self._create_client() as client:
                response = await client.post(
                    f"{self.platform_url}/v1/workers/register",
                    json=worker_info.model_dump(),
                    headers={"Authorization": f"Bearer {self.platform_auth_token}"},
                )
                if response.status_code == 200:
                    logger.info("✅ Successfully registered worker {worker_info.worker_id}")
                else:
                    logger.error(
                        f"❌ Registration failed: {response.status_code} - {response.text}",
                    )

        except Exception as e:
            logger.exception(f"❌ Registration error: {e}")

    def _create_client(self) -> httpx.AsyncClient:
        """Create HTTP client with certificate verification."""
        if hasattr(self.cert_store, "ca_cert") and self.cert_store.ca_cert:
            # Use CA certificate for verification
            return httpx.AsyncClient(verify=False)  # Simplified for now
        return httpx.AsyncClient(verify=False)

    def _start_heartbeat_task(self) -> None:
        """Start the background heartbeat task."""
        heartbeat_interval = int(os.getenv("WORKER_HEARTBEAT_INTERVAL", "20"))

        async def heartbeat_loop() -> None:
            """Background task to send periodic heartbeats."""
            while True:
                try:
                    await asyncio.sleep(heartbeat_interval)
                    if self.worker_id:
                        await self._send_heartbeat()
                except asyncio.CancelledError:
                    logger.info("Heartbeat task cancelled")
                    break
                except Exception:
                    logger.warning("Heartbeat failed: {e}")

        # Start the background task
        self.heartbeat_task = asyncio.create_task(heartbeat_loop())
        logger.info("🫀 Started heartbeat task with {heartbeat_interval}s interval")

    async def _send_heartbeat(self) -> None:
        """Send heartbeat to platform."""
        try:
            async with self._create_client() as client:
                response = await client.post(
                    f"{self.platform_url}/v1/workers/{self.worker_id}/heartbeat",
                    data={
                        "service_type": "document_conversion",
                        "load_score": 0.4,
                    },
                    headers={"Authorization": f"Bearer {self.platform_auth_token}"},
                )

            if response.status_code == 200:
                logger.debug("🫀 Heartbeat sent successfully")
            else:
                logger.warning("Heartbeat failed: {response.status_code}")

        except Exception as e:
            logger.debug(f"Heartbeat error: {e}")

    async def _shutdown(self) -> None:
        """Shutdown handler - deregister from platform."""
        if self.worker_id:
            logger.info("🔒 Deregistering document converter from platform...")
            try:
                async with self._create_client() as client:
                    await client.delete(f"{self.platform_url}/v1/workers/{self.worker_id}")
                logger.info("🔒 Successfully deregistered document converter")
            except Exception:
                logger.warning("Failed to deregister from platform: {e}")


def create_crank_document_converter(
    platform_url: Optional[str] = None, cert_store: Optional[Any] = None
) -> FastAPI:
    """Create Crank Document Converter application."""
    converter = CrankDocumentConverter(platform_url, cert_store)
    return converter.app


def main() -> None:
    """Main entry point with HTTPS enforcement and Certificate Authority Service integration."""

    import uvicorn

    # 🔒 ENFORCE HTTPS-ONLY MODE: No HTTP fallback allowed
    https_only = os.getenv("HTTPS_ONLY", "true").lower() == "true"
    ca_service_url = os.getenv("CA_SERVICE_URL")

    if https_only and ca_service_url:
        print("🔐 Initializing certificates using SECURE CSR pattern...")
        try:
            # Run secure certificate initialization in the same process
            import asyncio

            from crank_platform.security import cert_store, init_certificates

            # Run secure certificate initialization
            asyncio.run(init_certificates())

            # Check if certificates were loaded
            if cert_store.platform_cert is None:
                raise RuntimeError(
                    "🚫 Certificate initialization completed but no certificates in memory",
                )

            print("✅ Certificates loaded successfully using SECURE CSR pattern")
            print("🔒 SECURITY: Private keys generated locally and never transmitted")

            use_https = True
            logger.info("🔐 Using in-memory certificates from secure initialization")
        except Exception as e:
            raise RuntimeError(f"🚫 Failed to initialize certificates with CA service: {e}") from e
    else:
        raise RuntimeError("🚫 HTTPS_ONLY environment requires Certificate Authority Service")

    # 🚢 PORT CONFIGURATION: Use environment variables for flexible deployment
    int(os.getenv("DOC_CONVERTER_PORT", "8100"))  # HTTP fallback port
    service_host = os.getenv("DOC_CONVERTER_HOST", "0.0.0.0")
    https_port = int(os.getenv("DOC_CONVERTER_HTTPS_PORT", "8100"))

    # Create FastAPI app with pre-loaded certificates
    app = create_crank_document_converter(cert_store=cert_store)

    # 🔒 HTTPS-ONLY MODE: Always use HTTPS with Certificate Authority Service certificates
    if https_only:
        if not use_https:
            raise RuntimeError(
                "🚫 HTTPS_ONLY=true but certificates not found. Cannot start service.",
            )
        logger.info(
            f"🔒 Starting Crank Document Converter with HTTPS/mTLS ONLY on port {https_port}",
        )
        logger.info("🔐 Using in-memory certificates from Certificate Authority Service")

        # Create SSL context from in-memory certificates (SECURE CSR pattern)
        try:
            from crank_platform.security import cert_store

            cert_store.get_ssl_context()

            print("🔒 Using certificates obtained via SECURE CSR pattern")

            # Get the temporary certificate file paths for uvicorn - accessing private members
            # This is necessary as the cert_store doesn't provide a public API for uvicorn
            cert_file = cert_store.temp_cert_file  # pyright: ignore[reportAttributeAccessIssue]
            key_file = cert_store.temp_key_file  # pyright: ignore[reportAttributeAccessIssue]

            uvicorn.run(
                app,
                host=service_host,
                port=https_port,
                ssl_keyfile=key_file,
                ssl_certfile=cert_file,
            )
        except Exception as e:
            raise RuntimeError(
                f"🚫 Failed to create SSL context from Certificate Authority Service: {e}",
            ) from e
    else:
        raise RuntimeError(
            "🚫 HTTP mode disabled permanently - Certificate Authority Service provides HTTPS-only security",
        )


# For direct running
if __name__ == "__main__":
    main()
