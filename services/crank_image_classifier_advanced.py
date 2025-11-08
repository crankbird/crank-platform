"""
Crank GPU Image Classifier Service

GPU-accelerated computer vision ML service with YOLOv8, CLIP, and modern deep learning models.
Only runs on GPU-capable nodes with NVIDIA CUDA support.
Part of the separation-ready plugin architecture.
"""

import asyncio
import contextlib
import io
import logging
import os
import sys
import warnings
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import clip  # type: ignore[import-untyped]
import cv2
import httpx
import numpy as np
import torch
import uvicorn
import yaml
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

# Import our boundary shims for type safety
from ml_boundary_shims import (
    CLIPResult,
    safe_clip_analyze,
    safe_get_gpu_stats,
    safe_sentence_transformer_encode,
    safe_yolo_detect,
)
from PIL import Image
from pydantic import BaseModel
from security_config import initialize_security
from sentence_transformers import SentenceTransformer
from ultralytics.models.yolo import YOLO

sys.path.append(str(Path(__file__).parent.parent / "src"))
from gpu_manager import UniversalGPUManager

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI dependency defaults - create at module level to avoid evaluation in defaults
_DEFAULT_FILE_UPLOAD = File(...)
DEFAULT_FORM_CLASSIFICATION_TYPES = Form(default="yolo_detection,clip_analysis,advanced_scene_classification")

# Worker registration model
class WorkerRegistration(BaseModel):
    """Model for worker registration with platform."""
    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: list[str]


class GPUImageClassificationRequest(BaseModel):
    """Request model for GPU image classification."""
    classification_types: list[str] = ["yolo_detection", "clip_analysis", "scene_classification"]
    confidence_threshold: float = 0.5
    batch_size: int = 1
    return_embeddings: bool = False


class GPUImageClassificationResult(BaseModel):
    """Result model for GPU image classification."""
    classification_type: str
    prediction: str
    confidence: float
    details: Optional[dict[str, Any]] = None
    embeddings: Optional[list[float]] = None


class GPUClassificationResponse(BaseModel):
    """Response model for GPU image classification."""
    success: bool
    image_id: str
    results: list[GPUImageClassificationResult]
    metadata: dict[str, Any]
    gpu_stats: dict[str, Any]


class GPUImageClassifier:
    """GPU-accelerated computer vision classifier with modern deep learning models."""

    def __init__(self) -> None:
        self.device: torch.device = None  # type: ignore[assignment]
        self.yolo_model: Optional[YOLO] = None
        self.clip_model: Optional[Any] = None
        self.clip_preprocess: Optional[Any] = None
        self.sentence_transformer: Optional[SentenceTransformer] = None
        self._check_gpu_availability()
        self._initialize_models()

    def _check_gpu_availability(self) -> None:
        """Check GPU availability and initialize device using UniversalGPUManager."""
        # Use UniversalGPUManager for universal GPU detection
        gpu_manager = UniversalGPUManager()
        device_info = gpu_manager.get_info()

        # Ensure we have GPU acceleration available
        if device_info["device"] == "cpu":
            raise RuntimeError("❌ No GPU acceleration available. This service requires GPU support.")

        self.device = gpu_manager.get_device()

        # Log GPU information in a platform-agnostic way
        logger.info("🎮 GPU Device: %s", device_info["type"])
        if device_info.get("memory_gb"):
            logger.info("🎮 Memory: %.1fGB", device_info["memory_gb"])
        logger.info("🎮 Compute Capability: %s", device_info.get("compute_capability", "Unknown"))
        logger.info("🎮 Platform: %s (%s)", device_info["platform"], device_info["architecture"])

        # Memory optimization based on device type
        if self.device.type == "cuda":
            # CUDA-specific optimizations
            torch.cuda.empty_cache()
            vram_gb = device_info.get("memory_gb", 0)
            if vram_gb < 4.0:
                logger.warning("⚠️ Low VRAM detected. Some models may not load.")
        elif self.device.type == "mps":
            # Apple Silicon optimizations
            logger.info("🍎 Using Apple Metal Performance Shaders")
        else:
            logger.info("💻 Using %s device", self.device.type)

    def _initialize_models(self) -> None:
        """Initialize GPU-accelerated ML models."""
        logger.info("🚀 Initializing GPU-accelerated ML models...")

        try:
            # Initialize YOLOv8 for object detection
            logger.info("📦 Loading YOLOv8 model...")
            self.yolo_model = YOLO("yolov8n.pt")  # Start with nano model for speed
            self.yolo_model.to(self.device)
            logger.info("✅ YOLOv8 model loaded on GPU")

            # Initialize CLIP for image-text understanding
            logger.info("📦 Loading CLIP model...")
            self.clip_model, self.clip_preprocess = clip.load("ViT-B/32", device=self.device)
            logger.info("✅ CLIP model loaded on GPU")

            # Initialize sentence transformer for embeddings
            logger.info("📦 Loading Sentence Transformer...")
            self.sentence_transformer = SentenceTransformer("clip-ViT-B-32")
            self.sentence_transformer = self.sentence_transformer.to(self.device)
            logger.info("✅ Sentence Transformer loaded on GPU")

        except Exception as e:
            logger.exception("❌ Failed to initialize models")
            raise RuntimeError("Model initialization failed") from e

        # Clear cache after model loading (device-specific)
        if self.device.type == "cuda":
            torch.cuda.empty_cache()
        logger.info("🎯 All GPU models initialized successfully")

    def get_gpu_stats(self) -> dict[str, Any]:
        """Get current GPU utilization statistics using safe boundary shims."""
        # Use safe GPU stats wrapper from boundary shims
        return safe_get_gpu_stats()

    def _load_image(self, image_data: bytes) -> tuple[np.ndarray[Any, np.dtype[Any]], Image.Image, torch.Tensor]:
        """Load image from bytes into multiple formats for different models."""
        # Load with PIL
        pil_image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # Convert to OpenCV format
        opencv_image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)

        # Convert to PyTorch tensor for CLIP
        if self.clip_preprocess is not None:
            clip_tensor = self.clip_preprocess(pil_image).unsqueeze(0).to(self.device)
        else:
            # Fallback if clip preprocessing not available
            clip_tensor = torch.zeros((1, 3, 224, 224), device=self.device)  # type: ignore[call-overload]

        return opencv_image, pil_image, clip_tensor

    @torch.no_grad()  # type: ignore[misc]
    def yolo_object_detection(self, image_data: bytes, confidence: float = 0.5) -> tuple[str, float, dict[str, Any]]:
        """Advanced object detection using YOLOv8."""
        if self.yolo_model is None:
            return "model_not_loaded", 0.0, {"error": "YOLO model not initialized"}

        opencv_image, _pil_image, _ = self._load_image(image_data)

        # Use safe YOLO detection wrapper from boundary shims
        result = safe_yolo_detect(self.yolo_model, opencv_image, confidence)

        return result["prediction"], result["confidence"], {
            "detections": result["detections"],
            "model": result["model"],
            "total_objects": result["total_objects"]
        }

    @torch.no_grad()  # type: ignore[misc]
    def clip_image_analysis(self, image_data: bytes, custom_categories: Optional[list[str]] = None) -> CLIPResult:
        """Analyze image using CLIP zero-shot classification with safe wrapper."""
        try:
            if self.clip_model is None:
                return CLIPResult(
                    prediction="clip_not_loaded",
                    confidence=0.0,
                    scores=[],
                    model="CLIP"
                )

            _, pil_image, _ = self._load_image(image_data)

            categories = custom_categories or [
                "a photo of a person", "a photo of a car", "a photo of a cat",
                "a photo of a dog", "a photo of food", "a photo of nature",
                "a photo of a building", "a photo of technology", "a photo of art"
            ]

            return safe_clip_analyze(
                model=self.clip_model,
                processor=self.clip_preprocess,
                image=pil_image,
                text_categories=categories,
                device=str(self.device)
            )

        except Exception as e:
            logger.error(f"CLIP analysis error: {e}")
            return CLIPResult(
                prediction="clip_analysis_failed",
                confidence=0.0,
                scores=[],
                model="CLIP"
            )

    @torch.no_grad()  # type: ignore[misc]
    def advanced_scene_classification(self, image_data: bytes) -> tuple[str, float, dict[str, Any]]:
        """Advanced scene classification combining multiple signals."""
        try:
            opencv_image, _pil_image, _clip_tensor = self._load_image(image_data)

            # Get CLIP analysis
            clip_result = self.clip_image_analysis(image_data)
            clip_prediction = clip_result["prediction"]
            clip_conf = clip_result["confidence"]

            # Color analysis
            blue_pixels = np.sum((opencv_image[:,:,0] > opencv_image[:,:,1]) &
                               (opencv_image[:,:,0] > opencv_image[:,:,2]))
            green_pixels = np.sum((opencv_image[:,:,1] > opencv_image[:,:,0]) &
                                (opencv_image[:,:,1] > opencv_image[:,:,2]))

            total_pixels = opencv_image.shape[0] * opencv_image.shape[1]
            blue_ratio = blue_pixels / total_pixels
            green_ratio = green_pixels / total_pixels

            # Texture analysis
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size

            # Combine signals for enhanced classification
            enhanced_confidence = clip_conf
            enhanced_scene = clip_prediction

            # Adjust based on color analysis
            if (("nature" in clip_result and green_ratio > 0.3) or
                ("outdoors" in clip_result and blue_ratio > 0.2) or
                (edge_density > 0.1 and "architecture" in clip_result)):
                enhanced_confidence += 0.1

            enhanced_confidence = min(0.95, enhanced_confidence)

        except Exception as e:
            logger.exception("Advanced scene classification error")
            return "classification_failed", 0.0, {"error": str(e)}
        else:
            details: dict[str, Any] = {
                "clip_analysis": clip_result,
                "color_analysis": {
                    "blue_ratio": blue_ratio,
                    "green_ratio": green_ratio,
                    "dominant_color_channel": "blue" if blue_ratio > green_ratio else "green",
                },
                "texture_analysis": {
                    "edge_density": edge_density,
                    "texture_complexity": "high" if edge_density > 0.1 else "low",
                },
                "fusion_method": "clip_color_texture",
            }

            return enhanced_scene, enhanced_confidence, details

    @torch.no_grad()  # type: ignore[misc]
    def generate_image_embeddings(self, image_data: bytes) -> tuple[str, float, dict[str, Any]]:
        """Generate image embeddings for similarity search."""
        try:
            _, pil_image, clip_tensor = self._load_image(image_data)

            # Generate CLIP embeddings
            with torch.no_grad():
                if self.clip_model is not None:
                    image_features = self.clip_model.encode_image(clip_tensor)
                    normalized_features = image_features / image_features.norm(dim=-1, keepdim=True)
                    embeddings: list[float] = normalized_features.cpu().numpy()[0].tolist()
                else:
                    embeddings = []

            # Also generate sentence transformer embeddings with safe wrapper
            if self.sentence_transformer is not None:
                st_embeddings: np.ndarray[Any, np.dtype[Any]] = safe_sentence_transformer_encode(
                    model=self.sentence_transformer,
                    inputs=[pil_image]
                )
            else:
                st_embeddings = np.array([], dtype=np.float32)

        except Exception as e:
            logger.exception("Embedding generation error")
            return "embedding_failed", 0.0, {"error": str(e)}
        else:
            details: dict[str, Any] = {
                "clip_embeddings": embeddings,
                "sentence_transformer_embeddings": st_embeddings[0].tolist(),
                "embedding_dimensions": {
                    "clip": len(embeddings),
                    "sentence_transformer": len(st_embeddings[0]),
                },
                "similarity_ready": True,
            }

            return "embeddings_generated", 0.95, details


class CrankGPUImageClassifier:
    """Crank GPU Image Classifier Service that registers with platform."""

    def __init__(self, platform_url: Optional[str] = None) -> None:
        # Store platform URL for potential future use
        self._platform_url = platform_url

        # Create lifespan context manager
        @contextlib.asynccontextmanager
        async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
            # Startup
            logger.info("🎮 Starting Crank GPU Image Classifier Service...")

            # Initialize security and certificates
            logger.info("🔐 Initializing security configuration and certificates...")
            initialize_security()

            # Register with platform
            await self._register_with_platform()

            logger.info("✅ Crank GPU Image Classifier Service startup complete!")

            yield

            # Shutdown
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    logger.info("Heartbeat task cancelled")

        self.app = FastAPI(title="Crank GPU Image Classifier", version="1.0.0", lifespan=lifespan)

        # Worker registration configuration
        self.worker_id = f"image-classifier-gpu-{uuid4().hex[:8]}"
        self.platform_url = os.getenv("PLATFORM_URL", "https://platform:8443")
        self.worker_url = f"https://crank-image-classifier-gpu:{os.getenv('IMAGE_CLASSIFIER_GPU_HTTPS_PORT', '8506')}"
        self.platform_auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "dev-mesh-key")
        self.heartbeat_task: Optional[asyncio.Task[None]] = None

        # Certificate file paths for mTLS - initialize from standard paths
        cert_dir = Path("/etc/certs")
        self.cert_file = cert_dir / "platform.crt" if (cert_dir / "platform.crt").exists() else None
        self.key_file = cert_dir / "platform.key" if (cert_dir / "platform.key").exists() else None
        self.ca_file = cert_dir / "ca.crt" if (cert_dir / "ca.crt").exists() else None

        # Initialize GPU classifier
        self.classifier = GPUImageClassifier()

        # Setup routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""

        @self.app.get("/health")
        async def health_check() -> dict[str, Any]:  # type: ignore[misc]
            """Health check endpoint."""
            gpu_stats = self.classifier.get_gpu_stats()
            return {
                "status": "healthy",
                "service": "crank-image-classifier-gpu",
                "capabilities": ["yolo_object_detection", "clip_image_understanding", "advanced_scene_analysis", "image_embeddings", "batch_processing"],
                "gpu_accelerated": True,
                "models_loaded": {
                    "yolo": self.classifier.yolo_model is not None,
                    "clip": self.classifier.clip_model is not None,
                    "sentence_transformer": self.classifier.sentence_transformer is not None,
                },
                "gpu_stats": gpu_stats,
                "supported_formats": ["jpg", "jpeg", "png", "bmp", "gif", "webp"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        @self.app.post("/classify", response_model=GPUClassificationResponse)
        async def classify_image_gpu(  # type: ignore[misc]
            file: UploadFile = _DEFAULT_FILE_UPLOAD,
            classification_types: str = DEFAULT_FORM_CLASSIFICATION_TYPES,
        ) -> GPUClassificationResponse:
            """GPU-accelerated image classification."""

            def validate_image_file(upload_file: UploadFile) -> None:
                """Validate that uploaded file is an image."""
                if not upload_file.content_type or not upload_file.content_type.startswith("image/"):
                    raise HTTPException(status_code=400, detail="File must be an image")

            try:
                # Validate file type
                validate_image_file(file)

                # Read image data
                image_data = await file.read()

                # Generate image ID
                image_id = f"gpu-image-{uuid4().hex[:8]}"

                # Parse classification types
                types = [t.strip() for t in classification_types.split(",")]

                # Perform GPU-accelerated classifications
                results: list[GPUImageClassificationResult] = []

                for class_type in types:
                    if class_type == "yolo_detection":
                        prediction, confidence, details = self.classifier.yolo_object_detection(image_data)
                        results.append(GPUImageClassificationResult(
                            classification_type="yolo_object_detection",
                            prediction=prediction,
                            confidence=confidence,
                            details=details,
                        ))

                    elif class_type == "clip_analysis":
                        clip_result = self.classifier.clip_image_analysis(image_data)
                        results.append(GPUImageClassificationResult(
                            classification_type="clip_image_understanding",
                            prediction=clip_result["prediction"],
                            confidence=clip_result["confidence"],
                            details=dict(clip_result),
                        ))

                    elif class_type == "advanced_scene_classification":
                        prediction, confidence, details = self.classifier.advanced_scene_classification(image_data)
                        results.append(GPUImageClassificationResult(
                            classification_type="advanced_scene_analysis",
                            prediction=prediction,
                            confidence=confidence,
                            details=details,
                        ))

                    elif class_type == "image_embeddings":
                        prediction, confidence, details = self.classifier.generate_image_embeddings(image_data)
                        results.append(GPUImageClassificationResult(
                            classification_type="image_embeddings",
                            prediction=prediction,
                            confidence=confidence,
                            details=details,
                        ))

                # Get GPU stats for response
                gpu_stats = self.classifier.get_gpu_stats()

                return GPUClassificationResponse(
                    success=True,
                    image_id=image_id,
                    results=results,
                    metadata={
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "image_size": len(image_data),
                        "image_format": file.content_type,
                        "classification_count": len(results),
                        "worker_id": self.worker_id,
                        "gpu_accelerated": True,
                    },
                    gpu_stats=gpu_stats,
                )

            except Exception as e:
                logger.exception("GPU image classification error")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.app.get("/plugin")
        async def get_plugin_metadata() -> dict[str, Any]:  # type: ignore[misc]
            """Get plugin metadata for platform integration."""
            # Read plugin metadata from file
            plugin_file = Path("/app/plugin.yaml")
            if plugin_file.exists():
                try:
                    with plugin_file.open() as f:
                        return yaml.safe_load(f)
                except Exception as e:
                    logger.warning("Failed to read plugin metadata: %s", e)

            # Fallback to hardcoded metadata
            return {
                "name": "crank-image-classifier-gpu",
                "version": "1.0.0",
                "description": "GPU-accelerated computer vision ML classification with YOLOv8, CLIP, and modern deep learning",
                "author": "Crank Platform Team",
                "capabilities": ["yolo_object_detection", "clip_image_understanding", "advanced_scene_analysis", "image_embeddings"],
                "requirements": {"gpu": "required", "vram_min": "4GB"},
                "health_endpoint": "/health",
                "separation_ready": True,
            }

    def _create_mtls_client(self, timeout: float = 10.0) -> httpx.AsyncClient:
        """Create HTTP client with mTLS configuration for platform communication."""
        if self.cert_file and self.key_file and self.ca_file:
            # 🔒 ZERO-TRUST: Use mTLS for secure worker-to-platform communication
            environment = os.getenv("CRANK_ENVIRONMENT", "development")

            if environment == "development":
                logger.info("🔒 Using mTLS with relaxed verification for development")
                return httpx.AsyncClient(
                    cert=(str(self.cert_file), str(self.key_file)),
                    verify=False,
                    timeout=timeout,
                )

            logger.info("🔒 Using mTLS with full certificate verification for production")
            return httpx.AsyncClient(
                cert=(str(self.cert_file), str(self.key_file)),
                verify=str(self.ca_file),
                timeout=timeout,
            )

        logger.warning("⚠️  Using plain HTTP client - certificates not available")
        return httpx.AsyncClient(timeout=timeout)

    async def _register_with_platform(self) -> None:
        """Register this worker with the platform using mTLS."""
        worker_info = WorkerRegistration(
            worker_id=self.worker_id,
            service_type="image_classification_gpu",
            endpoint=self.worker_url,
            health_url=f"{self.worker_url}/health",
            capabilities=["yolo_object_detection", "clip_image_understanding", "advanced_scene_analysis", "image_embeddings", "batch_processing"],
        )

        # Try to register with retries
        max_retries = 5
        for attempt in range(max_retries):
            try:
                async with self._create_mtls_client() as client:
                    response = await client.post(
                        f"{self.platform_url}/v1/workers/register",
                        json=worker_info.model_dump(),
                        headers={"Authorization": f"Bearer {self.platform_auth_token}"},
                        timeout=10.0,
                    )
                    response.raise_for_status()
                    logger.info("🔒 Successfully registered GPU image classifier service via mTLS. Worker ID: %s", self.worker_id)

                    # Start heartbeat task
                    self._start_heartbeat_task()
                    return
            except Exception as e:
                logger.warning("Registration attempt %d failed: %s", attempt + 1, e)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        logger.error("Failed to register with platform after all retries")

    def _start_heartbeat_task(self) -> None:
        """Start the background heartbeat task."""
        async def heartbeat_loop() -> None:
            while True:
                try:
                    await asyncio.sleep(int(os.getenv("WORKER_HEARTBEAT_INTERVAL", "20")))
                    await self._send_heartbeat()
                except asyncio.CancelledError:
                    logger.info("Heartbeat task cancelled")
                    break
                except Exception:
                    logger.exception("Heartbeat error")

        self.heartbeat_task = asyncio.create_task(heartbeat_loop())
        heartbeat_interval = os.getenv("WORKER_HEARTBEAT_INTERVAL", "20")
        logger.info("🫀 Started heartbeat task with %ss interval", heartbeat_interval)

    async def _send_heartbeat(self) -> None:
        """Send heartbeat to platform."""
        try:
            async with self._create_mtls_client() as client:
                response = await client.post(
                    f"{self.platform_url}/v1/workers/{self.worker_id}/heartbeat",
                    data={
                        "service_type": "image_classification_gpu",
                        "load_score": 0.4,  # Higher load for GPU processing
                    },
                    headers={"Authorization": f"Bearer {self.platform_auth_token}"},
                    timeout=5.0,
                )
                response.raise_for_status()
        except Exception as e:
            logger.warning("Heartbeat failed: %s", e)

    async def _shutdown(self) -> None:
        """Shutdown handler - deregister from platform."""
        if self.worker_id:
            try:
                async with self._create_mtls_client(timeout=5.0) as client:
                    await client.delete(f"{self.platform_url}/v1/workers/{self.worker_id}")
                logger.info("🔒 Successfully deregistered GPU image classifier via mTLS")
            except Exception as e:
                logger.warning("Failed to deregister from platform: %s", e)


def create_crank_gpu_image_classifier(platform_url: Optional[str] = None) -> FastAPI:
    """Create Crank GPU Image Classifier application."""
    classifier = CrankGPUImageClassifier(platform_url)
    return classifier.app


def main() -> None:
    """Main entry point with HTTPS auto-detection."""

    app = create_crank_gpu_image_classifier()

    # 🔒 ZERO-TRUST: Auto-detect HTTPS based on certificate availability
    cert_dir = Path("/etc/certs")
    has_certs = (cert_dir / "platform.crt").exists() and (cert_dir / "platform.key").exists()

    # Kevin's port configuration - environment-based for maximum portability
    https_port = int(os.getenv("GPU_CLASSIFIER_HTTPS_PORT", "8443"))
    http_port = int(os.getenv("GPU_CLASSIFIER_HTTP_PORT", "8007"))

    if has_certs:
        print(f"🔒 Starting Crank GPU Image Classifier with HTTPS on port {https_port}")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=https_port,
            ssl_keyfile=str(cert_dir / "platform.key"),
            ssl_certfile=str(cert_dir / "platform.crt"),
        )
    else:
        print(f"⚠️  Starting Crank GPU Image Classifier with HTTP on port {http_port} (development only)")
        uvicorn.run(app, host="0.0.0.0", port=http_port)


if __name__ == "__main__":
    main()
