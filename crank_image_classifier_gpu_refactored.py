#!/usr/bin/env python3
"""
Crank GPU Image Classifier Service - REFACTORED with Worker Certificate Library

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

# Import worker certificate library
from worker_cert_pattern import WorkerCertificatePattern, create_worker_fastapi_with_certs

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

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
    capabilities: List[str]

class GPUImageClassificationRequest(BaseModel):
    """Request model for GPU image classification."""
    classification_types: List[str] = ["yolo_detection", "clip_analysis", "advanced_scene_classification"]
    confidence_threshold: float = 0.5
    max_detections: int = 10

class GPUClassificationResult(BaseModel):
    """Result model for GPU image classification."""
    classification_type: str
    prediction: str
    confidence: float
    details: Optional[Dict[str, Any]] = None

class GPUClassificationResponse(BaseModel):
    """Response model for GPU image classification."""
    success: bool
    image_id: str
    results: List[GPUClassificationResult]
    metadata: Dict[str, Any]
    gpu_stats: Dict[str, Any]


class GPUImageClassifier:
    """GPU-accelerated image classifier with modern deep learning models."""
    
    def __init__(self):
        """Initialize GPU classifier with CUDA support check."""
        self.yolo_model = None
        self.clip_model = None
        self.clip_preprocess = None
        self.sentence_transformer = None
        self.device = None
        
        # Check GPU availability
        self._check_gpu_requirements()
        self._initialize_models()
        
    def _check_gpu_requirements(self):
        """Check if GPU/CUDA is available and meets requirements."""
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
                gpu_stats = {
                    "gpu_name": gpu.name,
                    "gpu_load": f"{gpu.load * 100:.1f}%",
                    "memory_used": f"{gpu.memoryUsed}MB",
                    "memory_total": f"{gpu.memoryTotal}MB", 
                    "memory_free": f"{gpu.memoryFree}MB",
                    "memory_util": f"{gpu.memoryUtil * 100:.1f}%",
                    "temperature": f"{gpu.temperature}°C" if gpu.temperature else "N/A"
                }
            else:
                gpu_stats = {"error": "GPU not accessible"}
                
            # Add system memory
            memory = psutil.virtual_memory()
            gpu_stats.update({
                "system_memory_used": f"{memory.used / (1024**3):.1f}GB",
                "system_memory_total": f"{memory.total / (1024**3):.1f}GB",
                "system_memory_percent": f"{memory.percent:.1f}%"
            })
            
            return gpu_stats
            
        except Exception as e:
            return {"error": f"Failed to get GPU stats: {e}"}
    
    def detect_objects_yolo(self, image_data: bytes, threshold: float = 0.5, max_detections: int = 10) -> Tuple[str, float, Dict]:
        """Detect objects using YOLOv8."""
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            
            # Run YOLO detection
            with torch.no_grad():
                results = self.yolo_model(image, conf=threshold, max_det=max_detections)
            
            detections = []
            total_confidence = 0.0
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = self.yolo_model.names[class_id]
                        
                        detections.append({
                            "class": class_name,
                            "confidence": confidence,
                            "bbox": box.xyxy[0].tolist()
                        })
                        total_confidence += confidence
            
            if detections:
                avg_confidence = total_confidence / len(detections)
                prediction = f"Detected {len(detections)} objects: " + ", ".join([d["class"] for d in detections[:5]])
                if len(detections) > 5:
                    prediction += f" and {len(detections) - 5} more"
                
                details = {
                    "detections": detections,
                    "detection_count": len(detections),
                    "model": "YOLOv8n",
                    "device": str(self.device)
                }
                
                return prediction, avg_confidence, details
            else:
                return "No objects detected", 0.1, {"model": "YOLOv8n", "device": str(self.device)}
                
        except Exception as e:
            logger.error(f"YOLO detection error: {e}")
            return "detection_failed", 0.0, {"error": str(e)}
    
    def analyze_with_clip(self, image_data: bytes, text_queries: List[str] = None) -> Tuple[str, float, Dict]:
        """Analyze image using CLIP model."""
        try:
            if text_queries is None:
                text_queries = [
                    "a photo of a person", "a photo of an animal", "a photo of a vehicle",
                    "a photo of nature", "a photo of food", "a photo of a building",
                    "indoor scene", "outdoor scene", "urban scene", "rural scene"
                ]
            
            # Load and preprocess image
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            image_tensor = self.clip_preprocess(image).unsqueeze(0).to(self.device)
            
            # Tokenize text queries
            text_tokens = clip.tokenize(text_queries).to(self.device)
            
            with torch.no_grad():
                # Get image and text features
                image_features = self.clip_model.encode_image(image_tensor)
                text_features = self.clip_model.encode_text(text_tokens)
                
                # Calculate similarities
                similarities = (100.0 * image_features @ text_features.T).softmax(dim=-1)
                values, indices = similarities[0].topk(3)
            
            # Get top matches
            top_matches = []
            for i, (value, idx) in enumerate(zip(values, indices)):
                top_matches.append({
                    "query": text_queries[idx],
                    "similarity": float(value),
                    "rank": i + 1
                })
            
            best_match = top_matches[0]
            prediction = f"Best match: {best_match['query']}"
            confidence = best_match['similarity'] / 100.0
            
            details = {
                "top_matches": top_matches,
                "model": "CLIP ViT-B/32",
                "device": str(self.device),
                "total_queries": len(text_queries)
            }
            
            return prediction, confidence, details
            
        except Exception as e:
            logger.error(f"CLIP analysis error: {e}")
            return "analysis_failed", 0.0, {"error": str(e)}
    
    def classify_scene_advanced(self, image_data: bytes) -> Tuple[str, float, Dict]:
        """Advanced scene classification using multiple GPU models."""
        try:
            # Use CLIP for scene understanding
            scene_queries = [
                "indoor office", "outdoor park", "bedroom", "kitchen", "bathroom",
                "living room", "restaurant", "street", "beach", "forest",
                "mountain", "city", "countryside", "airport", "hospital"
            ]
            
            prediction, confidence, details = self.analyze_with_clip(image_data, scene_queries)
            
            # Enhance with additional context
            enhanced_details = {
                **details,
                "classification_type": "advanced_scene",
                "confidence_level": "high" if confidence > 0.7 else "medium" if confidence > 0.4 else "low"
            }
            
            return prediction, confidence, enhanced_details
            
        except Exception as e:
            logger.error(f"Advanced scene classification error: {e}")
            return "classification_failed", 0.0, {"error": str(e)}


def setup_gpu_classifier_routes(app: FastAPI, worker_config: dict):
    """Set up GPU image classifier routes using worker config."""
    
    # Get components from worker config
    cert_store = worker_config["cert_store"]
    platform_url = worker_config["platform_url"]
    worker_url = worker_config["worker_url"]
    service_name = worker_config["service_name"]
    
    # Initialize GPU classifier
    try:
        classifier = GPUImageClassifier()
        logger.info("🎮 GPU Image Classifier initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize GPU classifier: {e}")
        raise RuntimeError(f"GPU classifier initialization failed: {e}")
    
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
        """Health check endpoint with GPU status."""
        gpu_stats = classifier.get_gpu_stats()
        security_status = {
            "ssl_enabled": cert_store.platform_cert is not None if cert_store else False,
            "ca_cert_available": cert_store.ca_cert is not None if cert_store else False,
            "certificate_source": "Worker Certificate Library"
        }
        
        models_loaded = {
            "yolo": classifier.yolo_model is not None,
            "clip": classifier.clip_model is not None,
            "sentence_transformer": classifier.sentence_transformer is not None
        }
        
        return {
            "status": "healthy",
            "service": service_name,
            "capabilities": ["yolo_object_detection", "clip_image_understanding", "advanced_scene_analysis", "image_embeddings", "batch_processing"],
            "gpu_accelerated": True,
            "models_loaded": models_loaded,
            "gpu_stats": gpu_stats,
            "supported_formats": ["jpg", "jpeg", "png", "bmp", "gif", "webp"],
            "security": security_status,
            "timestamp": datetime.now().isoformat()
        }
    
    @app.post("/classify", response_model=GPUClassificationResponse)
    async def classify_image_gpu(
        file: UploadFile = File(...),
        classification_types: str = Form(default="yolo_detection,clip_analysis,advanced_scene_classification")
    ):
        """GPU-accelerated image classification."""
        start_time = datetime.now()
        image_id = f"gpu_img_{uuid4().hex[:8]}"
        
        try:
            # Read image data
            image_data = await file.read()
            
            # Parse classification types
            requested_types = [t.strip() for t in classification_types.split(',')]
            
            results = []
            
            # Perform requested classifications
            for classification_type in requested_types:
                if classification_type == "yolo_detection":
                    prediction, confidence, details = classifier.detect_objects_yolo(image_data)
                    results.append(GPUClassificationResult(
                        classification_type=classification_type,
                        prediction=prediction,
                        confidence=confidence,
                        details=details
                    ))
                
                elif classification_type == "clip_analysis":
                    prediction, confidence, details = classifier.analyze_with_clip(image_data)
                    results.append(GPUClassificationResult(
                        classification_type=classification_type,
                        prediction=prediction,
                        confidence=confidence,
                        details=details
                    ))
                
                elif classification_type == "advanced_scene_classification":
                    prediction, confidence, details = classifier.classify_scene_advanced(image_data)
                    results.append(GPUClassificationResult(
                        classification_type=classification_type,
                        prediction=prediction,
                        confidence=confidence,
                        details=details
                    ))
            
            processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Get GPU stats for response
            gpu_stats = classifier.get_gpu_stats()
            
            return GPUClassificationResponse(
                success=True,
                image_id=image_id,
                results=results,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "image_size": len(image_data),
                    "image_format": file.content_type,
                    "classification_count": len(results),
                    "processing_time_ms": processing_time_ms,
                    "worker_id": worker_id,
                    "gpu_accelerated": True
                },
                gpu_stats=gpu_stats
            )
            
        except Exception as e:
            logger.error(f"GPU image classification error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/capabilities")
    async def get_gpu_capabilities():
        """Get GPU image classifier capabilities."""
        gpu_stats = classifier.get_gpu_stats()
        
        return {
            "classification_types": [
                "yolo_detection",
                "clip_analysis", 
                "advanced_scene_classification"
            ],
            "supported_formats": ["jpg", "jpeg", "png", "bmp", "gif", "webp"],
            "models": {
                "yolo_v8": classifier.yolo_model is not None,
                "clip_vit_b32": classifier.clip_model is not None,
                "sentence_transformer": classifier.sentence_transformer is not None
            },
            "gpu_accelerated": True,
            "gpu_info": gpu_stats,
            "max_image_size": "50MB",
            "processing_features": [
                "real_time_object_detection",
                "semantic_image_understanding", 
                "scene_classification",
                "image_text_matching",
                "embedding_generation"
            ]
        }
    
    @app.get("/gpu/stats")
    async def get_gpu_statistics():
        """Get detailed GPU statistics."""
        return {
            "gpu_stats": classifier.get_gpu_stats(),
            "device": str(classifier.device),
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "models_loaded": {
                "yolo": classifier.yolo_model is not None,
                "clip": classifier.clip_model is not None,
                "sentence_transformer": classifier.sentence_transformer is not None
            }
        }
    
    async def _startup():
        """Startup handler - register with platform."""
        nonlocal worker_id
        
        logger.info("🎮 Starting Crank GPU Image Classifier...")
        logger.info("🔐 Using certificates loaded synchronously at startup")
        
        # Prepare registration info
        worker_info = WorkerRegistration(
            worker_id=f"gpu-image-classifier-{uuid4().hex[:8]}",
            service_type="gpu_image_classification",
            endpoint=worker_url,
            health_url=f"{worker_url}/health",
            capabilities=["yolo_object_detection", "clip_image_understanding", "advanced_scene_analysis", "gpu_acceleration"]
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
                        logger.info(f"🔒 Successfully registered GPU image classifier via mTLS. Worker ID: {worker_info.worker_id}")
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
                gpu_stats = classifier.get_gpu_stats()
                gpu_load = float(gpu_stats.get("gpu_load", "0%").rstrip("%")) / 100.0
                
                async with _create_adaptive_client(timeout=5.0) as client:
                    response = await client.post(
                        f"{platform_url}/v1/workers/{worker_id}/heartbeat",
                        data={
                            "service_type": "gpu_image_classification",
                            "load_score": gpu_load  # Real GPU load as load score
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
                logger.info("🔒 Successfully deregistered GPU image classifier via mTLS")
            except Exception as e:
                logger.warning(f"Failed to deregister from platform: {e}")
    
    # Register startup/shutdown handlers
    app.add_event_handler("startup", _startup)
    app.add_event_handler("shutdown", _shutdown)


def create_crank_gpu_image_classifier(cert_store=None):
    """Create the Crank GPU Image Classifier application with optional certificate store."""
    # This is kept for backward compatibility but now uses the worker library pattern
    worker_config = {
        "app": FastAPI(title="Crank GPU Image Classifier", version="1.0.0"),
        "cert_store": cert_store,
        "platform_url": os.getenv("PLATFORM_URL", "https://platform:8443"),
        "worker_url": os.getenv("WORKER_URL", "https://crank-image-classifier-gpu:8506"),
        "service_name": "crank-image-classifier-gpu"
    }
    
    setup_gpu_classifier_routes(worker_config["app"], worker_config)
    return worker_config["app"]


def main():
    """Main entry point using Worker Certificate Library."""
    
    # Step 1: Initialize certificates SYNCHRONOUSLY using library
    cert_pattern = WorkerCertificatePattern("crank-image-classifier-gpu")
    cert_store = cert_pattern.initialize_certificates()
    
    # Step 2: Create FastAPI with pre-loaded certificates using library
    worker_config = create_worker_fastapi_with_certs(
        title="Crank GPU Image Classifier",
        service_name="crank-image-classifier-gpu",
        platform_url=None,  # Use default from environment
        worker_url=None,    # Use default from environment
        cert_store=cert_store
    )
    
    # Step 3: Setup GPU image classifier routes
    setup_gpu_classifier_routes(worker_config["app"], worker_config)
    
    # Step 4: Start server with certificates using library
    https_port = int(os.getenv("GPU_CLASSIFIER_HTTPS_PORT", "8506"))
    cert_pattern.start_server(worker_config["app"], port=https_port)


# For direct running
if __name__ == "__main__":
    main()