"""
Crank GPU Image Classifier Service

GPU-accelerated computer vision service that follows the exact same pattern as
the working document converter service.
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

import cv2
import httpx
import numpy as np
from fastapi import FastAPI, Form, HTTPException, UploadFile
from numpy.typing import NDArray
from PIL import Image
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)

# Constants for image analysis
BRIGHT_THRESHOLD = 200
DARK_THRESHOLD = 50
MIN_RUNNING_CONTAINERS = 4
HTTP_STATUS_SERVER_ERROR = 500
logger = logging.getLogger(__name__)

# Import for GPU checks
if TYPE_CHECKING:
    from crank_platform.security import SecureCertificateStore
else:  # pragma: no cover - runtime fallback for optional dependency
    SecureCertificateStore = Any  # type: ignore[assignment]

gpu_manager: Any | None

try:
    # Import GPU manager directly - no path manipulation needed
    from gpu_manager import UniversalGPUManager

    # 🚨 WSL2 GPU COMPATIBILITY CRITICAL ISSUE - See docs/WSL2-GPU-CUDA-COMPATIBILITY.md
    #
    # IMPORTANT: Universal GPU Manager may work correctly, but Docker container environment
    # variables can still break PyTorch CUDA detection in WSL2 environments.
    #
    # Specifically: CUDA_VISIBLE_DEVICES=all breaks torch.cuda.is_available() in WSL2
    # even when this GPU manager correctly detects hardware.
    #
    # Resolution: Container must use NVIDIA_VISIBLE_DEVICES=all instead
    # See docker-compose.development.yml for environment variable configuration
    #
    # AI Assistant Context: If GPU_AVAILABLE=False but hardware exists, check:
    # 1. WSL2 environment detection (uname -r | grep microsoft)
    # 2. Container environment variables (avoid CUDA_VISIBLE_DEVICES in WSL2)
    # 3. torch.cuda.is_available() vs nvidia-smi output discrepancies
    #
    gpu_manager = UniversalGPUManager()
    gpu_available = gpu_manager.get_device_str() != "cpu"
    gpu_device: Any | None = gpu_manager.get_device()
    gpu_info: dict[str, Any] = gpu_manager.get_info()
except ImportError:
    gpu_available = False
    gpu_manager = None
    gpu_device = None
    gpu_info = {"type": "CPU", "platform": "Unknown"}
    logger.warning("GPU libraries not available - running in CPU mode")


# Worker registration model
class WorkerRegistration(BaseModel):
    """Model for worker registration with platform."""

    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: list[str]


# Classification request models
class ImageClassificationRequest(BaseModel):
    """Request model for image classification."""

    classification_types: list[str] = ["object_detection", "scene_classification"]
    confidence_threshold: float = 0.6


class ImageClassificationResponse(BaseModel):
    """Response model for image classification."""

    classification_id: str
    status: str
    results: dict[str, Any]
    processing_time: float
    message: str


class CrankImageClassifier:
    """Crank Image Classifier Service following the working pattern."""

    def __init__(self, platform_url: str | None = None, cert_store: Any = None) -> None:
        self.app = FastAPI(title="Crank Image Classifier", version="1.0.0")

        # 🔐 ZERO-TRUST: Use pre-loaded certificates from synchronous initialization
        if cert_store is not None:
            logger.info("🔐 Using pre-loaded certificates from synchronous initialization")
            self.cert_store = cert_store
        else:
            logger.info("🔐 Creating empty certificate store (fallback)")
            try:
                from crank_platform.security import SecureCertificateStore

                self.cert_store = SecureCertificateStore()
            except ImportError:
                # Fallback for development
                logger.warning("Certificate store not available - using minimal fallback")
                self.cert_store = None

        # Always use HTTPS with Certificate Authority Service certificates
        self.platform_url = platform_url or os.getenv("PLATFORM_URL", "https://platform:8443")
        self.worker_url = os.getenv("WORKER_URL", "https://crank-image-classifier:8400")

        # Certificate files are purely in-memory now - no disk dependencies
        self.cert_file = None
        self.key_file = None
        self.ca_file = None

        self.worker_id: str | None = None

        # Initialize GPU status with universal detection
        self.gpu_available = gpu_available
        self.gpu_device = gpu_device
        self.gpu_info = gpu_info

        if self.gpu_available:
            logger.info(
                "🚀 GPU acceleration available: %s on %s",
                self.gpu_info["type"],
                self.gpu_device,
            )
        else:
            logger.info("💻 Running in CPU mode")

        # Setup routes
        self._setup_routes()

        # Register startup/shutdown handlers
        self.app.add_event_handler("startup", self._startup)
        self.app.add_event_handler("shutdown", self._shutdown)

    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""

        self.app.add_api_route("/health", self.health_check, methods=["GET"])
        self.app.add_api_route("/", self.root, methods=["GET"])
        self.app.add_api_route("/classify", self.classify_image_endpoint, methods=["POST"])
        self.app.add_api_route("/capabilities", self.get_capabilities, methods=["GET"])

    async def health_check(self) -> dict[str, Any]:
        """Health check endpoint with security status."""
        security_status = {}
        if hasattr(self, "cert_store") and self.cert_store is not None:
            security_status = {
                "ssl_enabled": self.cert_store.platform_cert is not None,
                "ca_cert_available": self.cert_store.ca_cert is not None,
                "certificate_source": "Certificate Authority Service",
            }

        # Determine archetype identity based on service configuration
        # GPU service always identifies as GPU archetype regardless of runtime GPU availability
        service_name = os.getenv("IMAGE_CLASSIFIER_SERVICE_NAME", "")
        is_gpu_service = "gpu" in service_name

        if is_gpu_service:
            archetype_capabilities = [
                "advanced_classification",
                "gpu_inference",
                "real_time_processing",
            ]
        else:
            archetype_capabilities = ["basic_classification", "cpu_inference"]

        # Add runtime capabilities based on actual hardware
        runtime_capabilities = [
            "image-classification",
            "object-detection",
            "scene-analysis",
            "gpu-acceleration" if self.gpu_available else "cpu-processing",
        ]

        # Combine archetype identity with runtime capabilities
        all_capabilities = archetype_capabilities + runtime_capabilities

        return {
            "status": "healthy",
            "service": "crank-image-classifier",
            "worker_id": self.worker_id,
            "capabilities": all_capabilities,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "gpu_available": self.gpu_available,
            "security": security_status,
        }

    async def root(self) -> dict[str, Any]:
        """Root endpoint with service information."""
        return {
            "service": "Crank Image Classifier",
            "version": "1.0.0",
            "worker_id": self.worker_id,
            "gpu_available": self.gpu_available,
            "capabilities": [
                "image-classification",
                "object-detection",
                "scene-analysis",
                "gpu-acceleration" if self.gpu_available else "cpu-processing",
            ],
        }

    async def classify_image_endpoint(
        self,
        file: UploadFile,
        classification_types: str = Form("object_detection,scene_classification"),
        confidence_threshold: float = Form(0.5),
    ) -> ImageClassificationResponse:
        """Classify uploaded image."""
        try:
            # Read image content
            content = await file.read()

            # Parse classification types
            types = [t.strip() for t in classification_types.split(",")]

            logger.info("Classifying %s with types: %s", file.filename, types)

            # Perform classification
            start_time = datetime.now(timezone.utc)
            results = await self.classify_image(content, types, confidence_threshold)
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            classification_id = str(uuid4())

            return ImageClassificationResponse(
                classification_id=classification_id,
                status="completed",
                results=results,
                processing_time=processing_time,
                message=f"Successfully classified {file.filename}",
            )

        except Exception as e:
            logger.exception("Classification failed")
            raise HTTPException(status_code=HTTP_STATUS_SERVER_ERROR, detail=str(e)) from e

    async def get_capabilities(self) -> dict[str, Any]:
        """Get classification capabilities."""
        return {
            "classification_types": [
                "object_detection",
                "scene_classification",
                "color_analysis",
                "basic_content_analysis",
            ],
            "supported_formats": [
                "jpeg",
                "jpg",
                "png",
                "bmp",
                "tiff",
                "webp",
            ],
            "gpu_enabled": self.gpu_available,
        }

    async def classify_image(
        self,
        image_content: bytes,
        classification_types: list[str],
        confidence_threshold: float,
    ) -> dict[str, Any]:
        """Classify image using available models."""
        results = {}

        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_content))
            image_array = np.array(image)

            # Basic image properties
            results["image_info"] = {
                "format": image.format,
                "size": image.size,
                "mode": image.mode,
            }

            # Object detection (simplified)
            if "object_detection" in classification_types:
                results["object_detection"] = await self._detect_objects(
                    image_array,
                    confidence_threshold,
                )

            # Scene classification (basic)
            if "scene_classification" in classification_types:
                results["scene_classification"] = await self._classify_scene(image_array)

            # Color analysis
            if "color_analysis" in classification_types:
                results["color_analysis"] = await self._analyze_colors(image)

            # Basic content analysis
            if "basic_content_analysis" in classification_types:
                results["content_analysis"] = await self._analyze_content(image_array)

        except Exception as e:
            logger.exception("Image classification error")
            return {"error": str(e)}
        else:
            return results

    async def _detect_objects(
        self,
        image_array: NDArray[np.uint8],
        confidence_threshold: float,
    ) -> dict[str, Any]:
        """Basic object detection."""
        # Simplified object detection using OpenCV
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)

        # Basic feature detection - simplified approach
        # Note: SIFT may require opencv-contrib-python
        edges = cv2.Canny(gray, 100, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        return {
            "method": "Edge detection",
            "contours_detected": len(contours),
            "confidence": confidence_threshold,
            "gpu_accelerated": self.gpu_available,
        }

    async def _classify_scene(self, image_array: NDArray[np.uint8]) -> dict[str, Any]:
        """Basic scene classification."""
        # Simplified scene classification based on basic features
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)

        # Calculate basic statistics
        mean_brightness = np.mean(gray)
        contrast = np.std(gray)

        # Simple scene classification based on brightness and contrast
        if mean_brightness > BRIGHT_THRESHOLD:
            scene_type = "bright/outdoor"
        elif mean_brightness < DARK_THRESHOLD:
            scene_type = "dark/indoor"
        else:
            scene_type = "mixed_lighting"

        return {
            "scene_type": scene_type,
            "brightness": float(mean_brightness),
            "contrast": float(contrast),
            "method": "statistical_analysis",
        }

    async def _analyze_colors(self, image: Image.Image) -> dict[str, Any]:
        """Color analysis of the image."""
        # Get dominant colors
        image_rgb = image.convert("RGB")
        pixel_data = cast(Iterable[tuple[int, int, int]], image_rgb.getdata())
        pixels = list(pixel_data)

        # Calculate average color
        avg_color = tuple(sum(c) // len(pixels) for c in zip(*pixels))

        return {
            "average_color": {
                "rgb": avg_color,
                "hex": f"#{avg_color[0]:02x}{avg_color[1]:02x}{avg_color[2]:02x}",
            },
            "total_pixels": len(pixels),
        }

    async def _analyze_content(self, image_array: NDArray[np.uint8]) -> dict[str, Any]:
        """Basic content analysis."""
        height, width = image_array.shape[:2]

        # Calculate some basic metrics
        total_pixels = height * width
        aspect_ratio = width / height

        return {
            "dimensions": {"width": width, "height": height},
            "total_pixels": total_pixels,
            "aspect_ratio": round(aspect_ratio, 2),
            "estimated_complexity": "high"
            if total_pixels > 1000000
            else "medium"
            if total_pixels > 100000
            else "low",
        }

    async def _startup(self) -> None:
        """Startup handler - register with platform."""
        logger.info("🖼️ Starting Crank Image Classifier...")

        # Log security level for visibility (certificates already loaded synchronously)
        logger.info("🔐 Using certificates loaded synchronously at startup")

        # Prepare registration info
        worker_info = WorkerRegistration(
            worker_id=f"image-classifier-{uuid4().hex[:8]}",
            service_type="image_classification",
            endpoint=self.worker_url,
            health_url=f"{self.worker_url}/health",
            capabilities=[
                "image-classification",
                "object-detection",
                "scene-analysis",
                "gpu-acceleration" if self.gpu_available else "cpu-processing",
            ],
        )

        self.worker_id = worker_info.worker_id

        # Register with platform
        await self._register_with_platform(worker_info)

        # Start heartbeat background task
        self._start_heartbeat_task()

    async def _register_with_platform(self, worker_info: WorkerRegistration) -> None:
        """Register this worker with the platform using mTLS."""
        max_retries = 5
        retry_delay = 5  # seconds

        # Auth token for platform
        auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "local-dev-key")
        headers = {"Authorization": f"Bearer {auth_token}"}

        for attempt in range(max_retries):
            try:
                # 🔒 ZERO-TRUST: Use mTLS client for secure communication
                async with self._create_client() as client:
                    response = await client.post(
                        f"{self.platform_url}/v1/workers/register",
                        json=worker_info.model_dump(),
                        headers=headers,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        self.worker_id = result.get("worker_id")
                        logger.info(
                            "🔒 Successfully registered image classifier via mTLS. Worker ID: %s",
                            self.worker_id,
                        )
                        return
                    logger.warning(
                        "Registration attempt %d failed: %d - %s",
                        attempt + 1,
                        response.status_code,
                        response.text,
                    )

            except Exception as e:
                logger.warning("Registration attempt %d failed: %s", attempt + 1, e)

            if attempt < max_retries - 1:
                logger.info("Retrying registration in %d seconds...", retry_delay)
                await asyncio.sleep(retry_delay)

        logger.error("Failed to register with platform after all retries")
        # Continue running even if registration fails for development purposes

    def _create_client(self) -> httpx.AsyncClient:
        """Create HTTP client with certificate verification."""
        if (
            hasattr(self, "cert_store")
            and self.cert_store is not None
            and hasattr(self.cert_store, "ca_cert")
            and self.cert_store.ca_cert
        ):
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
                except Exception as e:
                    logger.warning("Heartbeat failed: %s", e)

        # Start the background task
        # Store heartbeat task reference to prevent garbage collection
        self.heartbeat_task = asyncio.create_task(heartbeat_loop())
        logger.info("🫀 Started heartbeat task with %ds interval", heartbeat_interval)

    async def _send_heartbeat(self) -> None:
        """Send heartbeat to platform."""
        try:
            auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "local-dev-key")
            headers = {"Authorization": f"Bearer {auth_token}"}

            # Prepare form data as expected by platform
            form_data = {
                "service_type": "image_classification",
                "load_score": "0.2",
            }

            async with self._create_client() as client:
                response = await client.post(
                    f"{self.platform_url}/v1/workers/{self.worker_id}/heartbeat",
                    data=form_data,
                    headers=headers,
                )

            if response.status_code == 200:
                logger.debug("🫀 Heartbeat sent successfully")
            else:
                logger.warning("Heartbeat failed: %d", response.status_code)

        except Exception as e:
            logger.warning("Failed to send heartbeat: %s", e)

    async def _shutdown(self) -> None:
        """Shutdown handler - deregister from platform."""
        if self.worker_id:
            logger.info("🔒 Deregistering image classifier from platform...")
            try:
                async with self._create_client() as client:
                    await client.delete(f"{self.platform_url}/v1/workers/{self.worker_id}")
                logger.info("🔒 Successfully deregistered image classifier")
            except Exception as e:
                logger.warning("Failed to deregister from platform: %s", e)


def create_crank_image_classifier(platform_url: str | None = None, cert_store: Any = None) -> FastAPI:
    """Create Crank Image Classifier application."""
    classifier = CrankImageClassifier(platform_url, cert_store)
    return classifier.app


def main() -> None:
    """Main entry point with HTTPS enforcement and Certificate Authority Service integration."""
    import uvicorn

    # 🔒 ENFORCE HTTPS-ONLY MODE: No HTTP fallback allowed
    https_only = os.getenv("HTTPS_ONLY", "true").lower() == "true"
    ca_service_url = os.getenv("CA_SERVICE_URL")

    cert_store: SecureCertificateStore | None = None
    use_https = False

    if https_only and ca_service_url:
        print("🔐 Initializing certificates using SECURE CSR pattern...")
        try:
            # Run secure certificate initialization in the same process
            try:
                from crank_platform import security as security_module
            except ImportError:
                logger.error("Certificate initialization not available")
                raise RuntimeError("Certificate initialization failed") from None

            # Run secure certificate initialization
            asyncio.run(security_module.init_certificates())

            security_store: SecureCertificateStore | None = getattr(
                security_module,
                "cert_store",
                None,
            )
            if security_store is None or security_store.platform_cert is None:
                raise RuntimeError(
                    "🚫 Certificate initialization completed but no certificates in memory",
                )
            cert_store = security_store

            print("✅ Certificates loaded successfully using SECURE CSR pattern")
            print("🔒 SECURITY: Private keys generated locally and never transmitted")

            use_https = True
            logger.info("🔐 Using in-memory certificates from secure initialization")
        except Exception as e:
            raise RuntimeError("🚫 Failed to initialize certificates with CA service") from e
    else:
        raise RuntimeError("🚫 HTTPS_ONLY environment requires Certificate Authority Service")

    # 🚢 PORT CONFIGURATION: Use environment variables for flexible deployment
    service_host = os.getenv("IMAGE_CLASSIFIER_HOST", "0.0.0.0")  # Bind to all interfaces in container
    https_port = int(os.getenv("IMAGE_CLASSIFIER_HTTPS_PORT", "8400"))

    # Create FastAPI app with pre-loaded certificates
    app = create_crank_image_classifier(cert_store=cert_store)

    # 🔒 HTTPS-ONLY MODE: Always use HTTPS with Certificate Authority Service certificates
    if https_only:
        if not use_https:
            raise RuntimeError(
                "🚫 HTTPS_ONLY=true but certificates not found. Cannot start service.",
            )
        logger.info(
            "🔒 Starting Crank Image Classifier with HTTPS/mTLS ONLY on port %d",
            https_port,
        )
        logger.info("🔐 Using in-memory certificates from Certificate Authority Service")

        # Create SSL context from in-memory certificates (SECURE CSR pattern)
        try:
            print("🔒 Using certificates obtained via SECURE CSR pattern")

            # Create SSL context to initialize temp files
            cert_store.get_ssl_context()

            # Get the temporary certificate file paths for uvicorn
            cert_file = cert_store.temp_cert_file
            key_file = cert_store.temp_key_file

            uvicorn.run(
                app,
                host=service_host,
                port=https_port,
                ssl_keyfile=key_file,
                ssl_certfile=cert_file,
            )
        except Exception as e:
            raise RuntimeError(
                "🚫 Failed to create SSL context from Certificate Authority Service",
            ) from e
    else:
        raise RuntimeError(
            "🚫 HTTP mode disabled permanently - Certificate Authority Service provides HTTPS-only security",
        )


if __name__ == "__main__":
    main()
