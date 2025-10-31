"""
Crank GPU Image Classifier Service

GPU-accelerated computer vision ML service with YOLOv8, CLIP, and modern deep learning models.
Only runs on GPU-capable nodes with NVIDIA CUDA support.
Part of the separation-ready plugin architecture.
"""

import asyncio
import json
import logging
import os
import tempfile
import io
import base64
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4
from datetime import datetime
import warnings

import httpx
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from pydantic import BaseModel
import numpy as np
import cv2
from PIL import Image
import torch
import torchvision.transforms as transforms
from ultralytics import YOLO
import clip
from sentence_transformers import SentenceTransformer
import GPUtil
import psutil

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPUImageClassificationRequest(BaseModel):
    """Request model for GPU image classification."""
    classification_types: List[str] = ["yolo_detection", "clip_analysis", "scene_classification"]
    confidence_threshold: float = 0.5
    batch_size: int = 1
    return_embeddings: bool = False


class GPUImageClassificationResult(BaseModel):
    """Result model for GPU image classification."""
    classification_type: str
    prediction: str
    confidence: float
    details: Optional[Dict[str, Any]] = None
    embeddings: Optional[List[float]] = None


class GPUClassificationResponse(BaseModel):
    """Response model for GPU image classification."""
    success: bool
    image_id: str
    results: List[GPUImageClassificationResult]
    metadata: Dict[str, Any]
    gpu_stats: Dict[str, Any]


class WorkerRegistration(BaseModel):
    """Worker registration model."""
    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: List[str]


class GPUImageClassifier:
    """GPU-accelerated computer vision classifier with modern deep learning models."""
    
    def __init__(self):
        self.device = None
        self.yolo_model = None
        self.clip_model = None
        self.clip_preprocess = None
        self.sentence_transformer = None
        self._check_gpu_availability()
        self._initialize_models()
        
    def _check_gpu_availability(self):
        """Check GPU availability and initialize device."""
        if not torch.cuda.is_available():
            raise RuntimeError("❌ CUDA not available. This service requires GPU support.")
        
        gpu_count = torch.cuda.device_count()
        if gpu_count == 0:
            raise RuntimeError("❌ No CUDA devices found. This service requires GPU support.")
        
        self.device = torch.device("cuda:0")
        gpu_props = torch.cuda.get_device_properties(0)
        vram_gb = gpu_props.total_memory / (1024**3)
        
        logger.info(f"🎮 GPU Device: {gpu_props.name}")
        logger.info(f"🎮 VRAM: {vram_gb:.1f}GB")
        logger.info(f"🎮 CUDA Capability: {gpu_props.major}.{gpu_props.minor}")
        
        if vram_gb < 4.0:
            logger.warning("⚠️ Low VRAM detected. Some models may not load.")
        
        # Set memory optimization
        torch.cuda.empty_cache()
        
    def _initialize_models(self):
        """Initialize GPU-accelerated ML models."""
        logger.info("🚀 Initializing GPU-accelerated ML models...")
        
        try:
            # Initialize YOLOv8 for object detection
            logger.info("📦 Loading YOLOv8 model...")
            self.yolo_model = YOLO('yolov8n.pt')  # Start with nano model for speed
            self.yolo_model.to(self.device)
            logger.info("✅ YOLOv8 model loaded on GPU")
            
            # Initialize CLIP for image-text understanding
            logger.info("📦 Loading CLIP model...")
            self.clip_model, self.clip_preprocess = clip.load("ViT-B/32", device=self.device)
            logger.info("✅ CLIP model loaded on GPU")
            
            # Initialize sentence transformer for embeddings
            logger.info("📦 Loading Sentence Transformer...")
            self.sentence_transformer = SentenceTransformer('clip-ViT-B-32')
            self.sentence_transformer = self.sentence_transformer.to(self.device)
            logger.info("✅ Sentence Transformer loaded on GPU")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize models: {e}")
            raise RuntimeError(f"Model initialization failed: {e}")
        
        # Clear cache after model loading
        torch.cuda.empty_cache()
        logger.info("🎯 All GPU models initialized successfully")
    
    def get_gpu_stats(self) -> Dict[str, Any]:
        """Get current GPU utilization statistics."""
        try:
            gpu = GPUtil.getGPUs()[0] if GPUtil.getGPUs() else None
            if gpu:
                return {
                    "gpu_name": gpu.name,
                    "gpu_utilization": f"{gpu.load * 100:.1f}%",
                    "memory_used": f"{gpu.memoryUsed}MB",
                    "memory_total": f"{gpu.memoryTotal}MB",
                    "memory_utilization": f"{gpu.memoryUtil * 100:.1f}%",
                    "temperature": f"{gpu.temperature}°C"
                }
        except Exception as e:
            logger.warning(f"Could not get GPU stats: {e}")
        
        # Fallback to PyTorch CUDA info
        return {
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "Unknown",
            "memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**2:.1f}MB",
            "memory_reserved": f"{torch.cuda.memory_reserved(0) / 1024**2:.1f}MB",
            "device_count": torch.cuda.device_count()
        }
    
    def _load_image(self, image_data: bytes) -> Tuple[np.ndarray, Image.Image, torch.Tensor]:
        """Load image from bytes into multiple formats for different models."""
        # Load with PIL
        pil_image = Image.open(io.BytesIO(image_data)).convert('RGB')
        
        # Convert to OpenCV format
        opencv_image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
        
        # Convert to PyTorch tensor for CLIP
        clip_tensor = self.clip_preprocess(pil_image).unsqueeze(0).to(self.device)
        
        return opencv_image, pil_image, clip_tensor
    
    @torch.no_grad()
    def yolo_object_detection(self, image_data: bytes, confidence: float = 0.5) -> Tuple[str, float, Dict]:
        """Advanced object detection using YOLOv8."""
        try:
            opencv_image, pil_image, _ = self._load_image(image_data)
            
            # Run YOLO inference
            results = self.yolo_model(opencv_image, conf=confidence, verbose=False)
            
            detections = []
            total_confidence = 0.0
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get class name and confidence
                        class_id = int(box.cls[0])
                        class_name = self.yolo_model.names[class_id]
                        conf = float(box.conf[0])
                        
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        detections.append({
                            "class": class_name,
                            "confidence": conf,
                            "bbox": [int(x1), int(y1), int(x2), int(y2)]
                        })
                        total_confidence += conf
            
            if detections:
                # Sort by confidence and get top detection
                detections.sort(key=lambda x: x["confidence"], reverse=True)
                top_detection = detections[0]
                
                prediction = f"{len(detections)} objects: {top_detection['class']}"
                confidence = min(0.99, total_confidence / len(detections))
                
                details = {
                    "detections": detections,
                    "model": "YOLOv8n",
                    "total_objects": len(detections)
                }
                
                return prediction, confidence, details
            else:
                return "no_objects_detected", 0.1, {"model": "YOLOv8n", "detections": []}
                
        except Exception as e:
            logger.error(f"YOLO detection error: {e}")
            return "detection_failed", 0.0, {"error": str(e)}
    
    @torch.no_grad()
    def clip_image_analysis(self, image_data: bytes) -> Tuple[str, float, Dict]:
        """Advanced image understanding using CLIP."""
        try:
            _, pil_image, clip_tensor = self._load_image(image_data)
            
            # Define scene categories for classification
            scene_categories = [
                "a photo of nature and outdoors",
                "a photo of people and portraits", 
                "a photo of buildings and architecture",
                "a photo of vehicles and transportation",
                "a photo of food and dining",
                "a photo of technology and electronics",
                "a photo of art and creative work",
                "a photo of animals and pets",
                "a photo of sports and recreation",
                "a photo of indoor scenes and interiors"
            ]
            
            # Tokenize text descriptions
            text_tokens = clip.tokenize(scene_categories).to(self.device)
            
            # Calculate similarities
            with torch.no_grad():
                image_features = self.clip_model.encode_image(clip_tensor)
                text_features = self.clip_model.encode_text(text_tokens)
                
                # Normalize features
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                
                # Calculate similarities
                similarities = (image_features @ text_features.T).cpu().numpy()[0]
            
            # Get best match
            best_idx = np.argmax(similarities)
            best_category = scene_categories[best_idx].replace("a photo of ", "")
            confidence = float(similarities[best_idx])
            
            # Convert to percentage and normalize
            confidence = min(0.95, max(0.1, (confidence + 1) / 2))  # Convert from [-1,1] to [0,1]
            
            details = {
                "model": "CLIP-ViT-B/32",
                "all_similarities": {
                    cat.replace("a photo of ", ""): float(sim) 
                    for cat, sim in zip(scene_categories, similarities)
                },
                "image_embedding_shape": list(image_features.shape)
            }
            
            return best_category, confidence, details
            
        except Exception as e:
            logger.error(f"CLIP analysis error: {e}")
            return "analysis_failed", 0.0, {"error": str(e)}
    
    @torch.no_grad()
    def advanced_scene_classification(self, image_data: bytes) -> Tuple[str, float, Dict]:
        """Advanced scene classification combining multiple signals."""
        try:
            opencv_image, pil_image, clip_tensor = self._load_image(image_data)
            
            # Get CLIP analysis
            clip_result, clip_conf, clip_details = self.clip_image_analysis(image_data)
            
            # Additional analysis using color and texture
            hsv = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2HSV)
            
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
            enhanced_scene = clip_result
            
            # Adjust based on color analysis
            if "nature" in clip_result and green_ratio > 0.3:
                enhanced_confidence += 0.1
            elif "outdoors" in clip_result and blue_ratio > 0.2:
                enhanced_confidence += 0.1
            elif edge_density > 0.1 and "architecture" in clip_result:
                enhanced_confidence += 0.1
            
            enhanced_confidence = min(0.95, enhanced_confidence)
            
            details = {
                "clip_analysis": clip_details,
                "color_analysis": {
                    "blue_ratio": blue_ratio,
                    "green_ratio": green_ratio,
                    "dominant_color_channel": "blue" if blue_ratio > green_ratio else "green"
                },
                "texture_analysis": {
                    "edge_density": edge_density,
                    "texture_complexity": "high" if edge_density > 0.1 else "low"
                },
                "fusion_method": "clip_color_texture"
            }
            
            return enhanced_scene, enhanced_confidence, details
            
        except Exception as e:
            logger.error(f"Advanced scene classification error: {e}")
            return "classification_failed", 0.0, {"error": str(e)}
    
    @torch.no_grad()
    def generate_image_embeddings(self, image_data: bytes) -> Tuple[str, float, Dict]:
        """Generate image embeddings for similarity search."""
        try:
            _, pil_image, clip_tensor = self._load_image(image_data)
            
            # Generate CLIP embeddings
            with torch.no_grad():
                image_features = self.clip_model.encode_image(clip_tensor)
                normalized_features = image_features / image_features.norm(dim=-1, keepdim=True)
                embeddings = normalized_features.cpu().numpy()[0].tolist()
            
            # Also generate sentence transformer embeddings
            st_embeddings = self.sentence_transformer.encode([pil_image])
            
            details = {
                "clip_embeddings": embeddings,
                "sentence_transformer_embeddings": st_embeddings[0].tolist(),
                "embedding_dimensions": {
                    "clip": len(embeddings),
                    "sentence_transformer": len(st_embeddings[0])
                },
                "similarity_ready": True
            }
            
            return "embeddings_generated", 0.95, details
            
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return "embedding_failed", 0.0, {"error": str(e)}


class CrankGPUImageClassifier:
    """Crank GPU Image Classifier Service that registers with platform."""
    
    def __init__(self, platform_url: str = None):
        self.app = FastAPI(title="Crank GPU Image Classifier", version="1.0.0")
        
        # Auto-detect HTTPS based on certificate availability
        cert_dir = Path("/etc/certs")
        has_certs = (cert_dir / "platform.crt").exists() and (cert_dir / "platform.key").exists()
        
        # 🔒 ZERO-TRUST: Always use HTTPS for platform communication when certs available
        if has_certs:
            self.platform_url = platform_url or os.getenv("PLATFORM_URL", "https://platform:8443")
            self.worker_url = os.getenv("WORKER_URL", "https://crank-image-classifier-gpu:8443")
            # mTLS client configuration with proper CA handling
            self.cert_file = cert_dir / "platform.crt"
            self.key_file = cert_dir / "platform.key"
            self.ca_file = cert_dir / "ca.crt"
        else:
            # Fallback to HTTP only in development without certificates
            self.platform_url = platform_url or os.getenv("PLATFORM_URL", "http://platform:8080")
            self.worker_url = os.getenv("WORKER_URL", "http://crank-image-classifier-gpu:8007")
            self.cert_file = None
            self.key_file = None
            self.ca_file = None
            logger.warning("⚠️  No certificates found - falling back to HTTP (development only)")
            
        self.worker_id = None
        
        # Initialize GPU classifier
        self.classifier = GPUImageClassifier()
        
        # Setup routes
        self._setup_routes()
        
        # Register startup/shutdown handlers
        self.app.add_event_handler("startup", self._startup)
        self.app.add_event_handler("shutdown", self._shutdown)
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/health")
        async def health_check():
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
                    "sentence_transformer": self.classifier.sentence_transformer is not None
                },
                "gpu_stats": gpu_stats,
                "supported_formats": ["jpg", "jpeg", "png", "bmp", "gif", "webp"],
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/classify", response_model=GPUClassificationResponse)
        async def classify_image_gpu(
            file: UploadFile = File(...),
            classification_types: str = Form(default="yolo_detection,clip_analysis,advanced_scene_classification")
        ):
            """GPU-accelerated image classification."""
            try:
                # Validate file type
                if not file.content_type or not file.content_type.startswith('image/'):
                    raise HTTPException(status_code=400, detail="File must be an image")
                
                # Read image data
                image_data = await file.read()
                
                # Generate image ID
                image_id = f"gpu-image-{uuid4().hex[:8]}"
                
                # Parse classification types
                types = [t.strip() for t in classification_types.split(",")]
                
                # Perform GPU-accelerated classifications
                results = []
                
                for class_type in types:
                    if class_type == "yolo_detection":
                        prediction, confidence, details = self.classifier.yolo_object_detection(image_data)
                        results.append(GPUImageClassificationResult(
                            classification_type="yolo_object_detection",
                            prediction=prediction,
                            confidence=confidence,
                            details=details
                        ))
                    
                    elif class_type == "clip_analysis":
                        prediction, confidence, details = self.classifier.clip_image_analysis(image_data)
                        results.append(GPUImageClassificationResult(
                            classification_type="clip_image_understanding",
                            prediction=prediction,
                            confidence=confidence,
                            details=details
                        ))
                    
                    elif class_type == "advanced_scene_classification":
                        prediction, confidence, details = self.classifier.advanced_scene_classification(image_data)
                        results.append(GPUImageClassificationResult(
                            classification_type="advanced_scene_analysis",
                            prediction=prediction,
                            confidence=confidence,
                            details=details
                        ))
                    
                    elif class_type == "image_embeddings":
                        prediction, confidence, details = self.classifier.generate_image_embeddings(image_data)
                        results.append(GPUImageClassificationResult(
                            classification_type="image_embeddings",
                            prediction=prediction,
                            confidence=confidence,
                            details=details
                        ))
                
                # Get GPU stats for response
                gpu_stats = self.classifier.get_gpu_stats()
                
                return GPUClassificationResponse(
                    success=True,
                    image_id=image_id,
                    results=results,
                    metadata={
                        "timestamp": datetime.now().isoformat(),
                        "image_size": len(image_data),
                        "image_format": file.content_type,
                        "classification_count": len(results),
                        "worker_id": self.worker_id,
                        "gpu_accelerated": True
                    },
                    gpu_stats=gpu_stats
                )
                
            except Exception as e:
                logger.error(f"GPU image classification error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/plugin")
        async def get_plugin_metadata():
            """Get plugin metadata for platform integration."""
            # Read plugin metadata from file
            plugin_file = Path("/app/plugin.yaml")
            if plugin_file.exists():
                import yaml
                try:
                    with open(plugin_file) as f:
                        plugin_data = yaml.safe_load(f)
                    return plugin_data
                except Exception as e:
                    logger.warning(f"Failed to read plugin metadata: {e}")
            
            # Fallback to hardcoded metadata
            return {
                "name": "crank-image-classifier-gpu",
                "version": "1.0.0",
                "description": "GPU-accelerated computer vision ML classification with YOLOv8, CLIP, and modern deep learning",
                "author": "Crank Platform Team",
                "capabilities": ["yolo_object_detection", "clip_image_understanding", "advanced_scene_analysis", "image_embeddings"],
                "requirements": {"gpu": "required", "vram_min": "4GB"},
                "health_endpoint": "/health",
                "separation_ready": True
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
                    timeout=timeout
                )
            else:
                logger.info("🔒 Using mTLS with full certificate verification for production")
                return httpx.AsyncClient(
                    cert=(str(self.cert_file), str(self.key_file)),
                    verify=str(self.ca_file),
                    timeout=timeout
                )
        else:
            logger.warning("⚠️  Using plain HTTP client - certificates not available")
            return httpx.AsyncClient(timeout=timeout)
    
    async def _startup(self):
        """Startup handler - register with platform."""
        logger.info("🎮 Starting Crank GPU Image Classifier...")
        
        # Prepare registration info
        worker_info = WorkerRegistration(
            worker_id=f"gpu-image-classifier-{uuid4().hex[:8]}",
            service_type="image_classification_gpu",
            endpoint=self.worker_url,
            health_url=f"{self.worker_url}/health",
            capabilities=["yolo_object_detection", "clip_image_understanding", "advanced_scene_analysis", "image_embeddings", "batch_processing"]
        )
        
        # Register with platform
        await self._register_with_platform(worker_info)
    
    async def _register_with_platform(self, worker_info: WorkerRegistration):
        """Register this worker with the platform using mTLS."""
        max_retries = 5
        retry_delay = 5
        
        auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "dev-mesh-key")
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        for attempt in range(max_retries):
            try:
                async with self._create_mtls_client() as client:
                    response = await client.post(
                        f"{self.platform_url}/v1/workers/register",
                        json=worker_info.model_dump(),
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.worker_id = result.get("worker_id")
                        logger.info(f"🔒 Successfully registered GPU image classifier via mTLS. Worker ID: {self.worker_id}")
                        return
                    else:
                        logger.warning(f"Registration attempt {attempt + 1} failed: {response.status_code} - {response.text}")
                        
            except Exception as e:
                logger.warning(f"Registration attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying registration in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
        
        logger.error("Failed to register with platform after all retries")
    
    async def _shutdown(self):
        """Shutdown handler - deregister from platform."""
        if self.worker_id:
            try:
                async with self._create_mtls_client(timeout=5.0) as client:
                    await client.delete(f"{self.platform_url}/v1/workers/{self.worker_id}")
                logger.info("🔒 Successfully deregistered GPU image classifier via mTLS")
            except Exception as e:
                logger.warning(f"Failed to deregister from platform: {e}")


def create_crank_gpu_image_classifier(platform_url: str = None) -> FastAPI:
    """Create Crank GPU Image Classifier application."""
    classifier = CrankGPUImageClassifier(platform_url)
    return classifier.app


def main():
    """Main entry point with HTTPS auto-detection."""
    import uvicorn
    from pathlib import Path
    
    app = create_crank_gpu_image_classifier()
    
    # 🔒 ZERO-TRUST: Auto-detect HTTPS based on certificate availability
    cert_dir = Path("/etc/certs")
    has_certs = (cert_dir / "platform.crt").exists() and (cert_dir / "platform.key").exists()
    
    if has_certs:
        print("🔒 Starting Crank GPU Image Classifier with HTTPS on port 8443")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8443,
            ssl_keyfile=str(cert_dir / "platform.key"),
            ssl_certfile=str(cert_dir / "platform.crt")
        )
    else:
        print("⚠️  Starting Crank GPU Image Classifier with HTTP on port 8007 (development only)")
        uvicorn.run(app, host="0.0.0.0", port=8007)


if __name__ == "__main__":
    main()