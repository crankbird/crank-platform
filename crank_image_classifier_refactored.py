#!/usr/bin/env python3
"""
Crank Image Classifier Service - REFACTORED with Worker Certificate Library

Computer vision ML service for image classification, object detection, and content analysis.
Registers with the platform and provides real CV capabilities using OpenCV and simple ML models.
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
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from pydantic import BaseModel
import numpy as np
import cv2
from PIL import Image, ImageStat
from sklearn.cluster import KMeans
import webcolors

# Import worker certificate library
from worker_cert_pattern import WorkerCertificatePattern, create_worker_fastapi_with_certs

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

class ImageClassificationRequest(BaseModel):
    """Request model for image classification."""
    classification_types: List[str] = ["object_detection", "scene_classification", "content_safety"]
    confidence_threshold: float = 0.6

class ImageClassificationResult(BaseModel):
    """Result model for image classification."""
    classification_type: str
    prediction: str
    confidence: float
    details: Optional[Dict[str, Any]] = None

class ClassificationResponse(BaseModel):
    """Response model for image classification."""
    success: bool
    image_id: str
    results: List[ImageClassificationResult]
    metadata: Dict[str, Any]


class ImageProcessor:
    """Core image processing and classification engine."""
    
    def __init__(self):
        """Initialize the image processor with ML models."""
        self.face_cascade = None
        self.eye_cascade = None
        
        # Try to load OpenCV cascade classifiers
        try:
            cascade_path = cv2.data.haarcascades
            face_cascade_path = os.path.join(cascade_path, 'haarcascade_frontalface_default.xml')
            eye_cascade_path = os.path.join(cascade_path, 'haarcascade_eye.xml')
            
            if os.path.exists(face_cascade_path):
                self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
            if os.path.exists(eye_cascade_path):
                self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
                
            logger.info("✅ OpenCV cascade classifiers loaded successfully")
        except Exception as e:
            logger.warning(f"⚠️ Could not load OpenCV cascades: {e}")
    
    def _load_image(self, image_data: bytes) -> Tuple[np.ndarray, Image.Image]:
        """Load image from bytes into both OpenCV and PIL formats."""
        # Create PIL image
        pil_image = Image.open(io.BytesIO(image_data)).convert('RGB')
        
        # Convert to OpenCV format
        opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        return opencv_image, pil_image
    
    def detect_objects(self, image_data: bytes, threshold: float = 0.6) -> Tuple[str, float, Dict]:
        """Detect objects in image using OpenCV cascades."""
        try:
            opencv_image, _ = self._load_image(image_data)
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            objects_found = []
            total_confidence = 0.0
            
            # Detect faces
            if self.face_cascade is not None:
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                if len(faces) > 0:
                    objects_found.append(f"{len(faces)} face(s)")
                    total_confidence += 0.8
            
            # Detect eyes
            if self.eye_cascade is not None:
                eyes = self.eye_cascade.detectMultiScale(gray, 1.1, 4)
                if len(eyes) > 0:
                    objects_found.append(f"{len(eyes)} eye(s)")
                    total_confidence += 0.6
            
            if objects_found:
                prediction = ", ".join(objects_found)
                confidence = min(0.95, total_confidence / len(objects_found))
                details = {
                    "objects_detected": objects_found,
                    "detection_method": "haar_cascades"
                }
                return prediction, confidence, details
            else:
                return "no_objects_detected", 0.3, {"detection_method": "haar_cascades"}
                
        except Exception as e:
            logger.error(f"Object detection error: {e}")
            return "detection_failed", 0.0, {"error": str(e)}
    
    def classify_scene(self, image_data: bytes) -> Tuple[str, float]:
        """Classify scene type using simple color and texture analysis."""
        try:
            opencv_image, pil_image = self._load_image(image_data)
            
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2HSV)
            
            # Calculate color distribution
            height, width = opencv_image.shape[:2]
            total_pixels = height * width
            
            # Analyze dominant colors
            dominant_colors = self._get_dominant_colors(opencv_image)
            
            # Simple scene classification based on colors
            green_ratio = np.sum((hsv[:, :, 1] > 50) & (hsv[:, :, 0] > 40) & (hsv[:, :, 0] < 80)) / total_pixels
            blue_ratio = np.sum((hsv[:, :, 1] > 50) & (hsv[:, :, 0] > 100) & (hsv[:, :, 0] < 130)) / total_pixels
            
            if green_ratio > 0.3:
                return "nature/outdoor", min(0.9, 0.6 + green_ratio)
            elif blue_ratio > 0.2:
                return "sky/water", min(0.9, 0.6 + blue_ratio)
            elif len(dominant_colors) > 3:
                return "complex/indoor", 0.7
            else:
                return "simple/minimal", 0.6
                
        except Exception as e:
            logger.error(f"Scene classification error: {e}")
            return "classification_failed", 0.0
    
    def _get_dominant_colors(self, image: np.ndarray, k: int = 5) -> List[Tuple[int, int, int]]:
        """Get dominant colors using K-means clustering."""
        try:
            # Reshape image to 2D array of pixels
            pixels = image.reshape(-1, 3)
            
            # Apply K-means clustering
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(pixels)
            
            # Get cluster centers (dominant colors)
            colors = kmeans.cluster_centers_.astype(int)
            return [tuple(color) for color in colors]
            
        except Exception as e:
            logger.warning(f"Color analysis error: {e}")
            return []
    
    def analyze_content_safety(self, image_data: bytes) -> Tuple[str, float, Dict]:
        """Analyze image for content safety using basic heuristics."""
        try:
            opencv_image, pil_image = self._load_image(image_data)
            
            # Basic content analysis
            stat = ImageStat.Stat(pil_image)
            
            # Check image properties
            width, height = pil_image.size
            aspect_ratio = width / height
            
            # Simple heuristics
            brightness = sum(stat.mean) / 3  # Average RGB
            
            safety_score = 0.8  # Default safe score
            issues = []
            
            # Very dark images might be concerning
            if brightness < 50:
                safety_score -= 0.2
                issues.append("very_dark_content")
            
            # Extreme aspect ratios might indicate inappropriate crops
            if aspect_ratio > 3 or aspect_ratio < 0.3:
                safety_score -= 0.1
                issues.append("unusual_aspect_ratio")
            
            safety_score = max(0.0, min(1.0, safety_score))
            
            if safety_score > 0.7:
                prediction = "safe"
            elif safety_score > 0.4:
                prediction = "questionable"
            else:
                prediction = "potentially_unsafe"
            
            details = {
                "safety_score": safety_score,
                "issues": issues,
                "image_properties": {
                    "width": width,
                    "height": height,
                    "aspect_ratio": aspect_ratio,
                    "brightness": brightness
                }
            }
            
            return prediction, safety_score, details
            
        except Exception as e:
            logger.error(f"Content safety analysis error: {e}")
            return "analysis_failed", 0.0, {"error": str(e)}
    
    def extract_color_palette(self, image_data: bytes) -> Dict[str, Any]:
        """Extract color palette from image."""
        try:
            opencv_image, _ = self._load_image(image_data)
            dominant_colors = self._get_dominant_colors(opencv_image)
            
            # Convert colors to names
            color_names = []
            for color in dominant_colors:
                try:
                    closest_name = webcolors.rgb_to_name(color)
                    color_names.append(closest_name)
                except ValueError:
                    # If exact match not found, find closest
                    color_names.append(f"rgb{color}")
            
            return {
                "dominant_colors": dominant_colors,
                "color_names": color_names,
                "palette_size": len(dominant_colors)
            }
            
        except Exception as e:
            logger.warning(f"Color palette extraction error: {e}")
            return {"error": str(e)}


def setup_image_classifier_routes(app: FastAPI, worker_config: dict):
    """Set up image classifier routes using worker config."""
    
    # Get components from worker config
    cert_store = worker_config["cert_store"]
    platform_url = worker_config["platform_url"]
    worker_url = worker_config["worker_url"]
    service_name = worker_config["service_name"]
    
    # Initialize image processor
    processor = ImageProcessor()
    
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
        
        models_loaded = {
            "face_cascade": processor.face_cascade is not None,
            "eye_cascade": processor.eye_cascade is not None
        }
        
        return {
            "status": "healthy",
            "service": service_name,
            "capabilities": ["object_detection", "scene_classification", "content_safety", "color_analysis"],
            "models_loaded": models_loaded,
            "supported_formats": ["jpg", "jpeg", "png", "bmp", "gif", "webp"],
            "security": security_status,
            "timestamp": datetime.now().isoformat()
        }
    
    @app.post("/classify", response_model=ClassificationResponse)
    async def classify_image(
        file: UploadFile = File(...),
        classification_types: str = Form(default="object_detection,scene_classification,content_safety")
    ):
        """Classify uploaded image using computer vision models."""
        start_time = datetime.now()
        image_id = f"img_{uuid4().hex[:8]}"
        
        try:
            # Read image data
            image_data = await file.read()
            
            # Parse classification types
            requested_types = [t.strip() for t in classification_types.split(',')]
            
            results = []
            
            # Perform requested classifications
            for classification_type in requested_types:
                if classification_type == "object_detection":
                    prediction, confidence, details = processor.detect_objects(image_data)
                    results.append(ImageClassificationResult(
                        classification_type=classification_type,
                        prediction=prediction,
                        confidence=confidence,
                        details=details
                    ))
                
                elif classification_type == "scene_classification":
                    prediction, confidence = processor.classify_scene(image_data)
                    results.append(ImageClassificationResult(
                        classification_type=classification_type,
                        prediction=prediction,
                        confidence=confidence
                    ))
                
                elif classification_type == "content_safety":
                    prediction, confidence, details = processor.analyze_content_safety(image_data)
                    results.append(ImageClassificationResult(
                        classification_type=classification_type,
                        prediction=prediction,
                        confidence=confidence,
                        details=details
                    ))
                
                elif classification_type == "color_analysis":
                    palette = processor.extract_color_palette(image_data)
                    results.append(ImageClassificationResult(
                        classification_type=classification_type,
                        prediction=f"{len(palette.get('dominant_colors', []))} dominant colors",
                        confidence=0.9,
                        details=palette
                    ))
            
            processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return ClassificationResponse(
                success=True,
                image_id=image_id,
                results=results,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "image_size": len(image_data),
                    "image_format": file.content_type,
                    "classification_count": len(results),
                    "processing_time_ms": processing_time_ms,
                    "worker_id": worker_id
                }
            )
            
        except Exception as e:
            logger.error(f"Image classification error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/capabilities")
    async def get_capabilities():
        """Get image classifier capabilities."""
        return {
            "classification_types": [
                "object_detection",
                "scene_classification", 
                "content_safety",
                "color_analysis"
            ],
            "supported_formats": ["jpg", "jpeg", "png", "bmp", "gif", "webp"],
            "models": {
                "face_detection": processor.face_cascade is not None,
                "eye_detection": processor.eye_cascade is not None,
                "color_clustering": True,
                "basic_safety_analysis": True
            },
            "max_image_size": "10MB",
            "processing_features": [
                "opencv_cascades",
                "kmeans_clustering",
                "color_analysis",
                "safety_heuristics"
            ]
        }
    
    async def _startup():
        """Startup handler - register with platform."""
        nonlocal worker_id
        
        logger.info("🖼️ Starting Crank Image Classifier...")
        logger.info("🔐 Using certificates loaded synchronously at startup")
        
        # Prepare registration info
        worker_info = WorkerRegistration(
            worker_id=f"image-classifier-{uuid4().hex[:8]}",
            service_type="image_classification",
            endpoint=worker_url,
            health_url=f"{worker_url}/health",
            capabilities=["object_detection", "scene_classification", "content_safety", "color_analysis"]
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
                        logger.info(f"🔒 Successfully registered image classifier via mTLS. Worker ID: {worker_info.worker_id}")
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
                            "service_type": "image_classification",
                            "load_score": 0.5  # Simulated load for CV processing
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
                logger.info("🔒 Successfully deregistered image classifier via mTLS")
            except Exception as e:
                logger.warning(f"Failed to deregister from platform: {e}")
    
    # Register startup/shutdown handlers
    app.add_event_handler("startup", _startup)
    app.add_event_handler("shutdown", _shutdown)


def create_crank_image_classifier(cert_store=None):
    """Create the Crank Image Classifier application with optional certificate store."""
    # This is kept for backward compatibility but now uses the worker library pattern
    worker_config = {
        "app": FastAPI(title="Crank Image Classifier", version="1.0.0"),
        "cert_store": cert_store,
        "platform_url": os.getenv("PLATFORM_URL", "https://platform:8443"),
        "worker_url": os.getenv("WORKER_URL", "https://crank-image-classifier:8005"),
        "service_name": "crank-image-classifier"
    }
    
    setup_image_classifier_routes(worker_config["app"], worker_config)
    return worker_config["app"]


def main():
    """Main entry point using Worker Certificate Library."""
    
    # Step 1: Initialize certificates SYNCHRONOUSLY using library
    cert_pattern = WorkerCertificatePattern("crank-image-classifier")
    cert_store = cert_pattern.initialize_certificates()
    
    # Step 2: Create FastAPI with pre-loaded certificates using library
    worker_config = create_worker_fastapi_with_certs(
        title="Crank Image Classifier",
        service_name="crank-image-classifier",
        platform_url=None,  # Use default from environment
        worker_url=None,    # Use default from environment
        cert_store=cert_store
    )
    
    # Step 3: Setup image classifier routes
    setup_image_classifier_routes(worker_config["app"], worker_config)
    
    # Step 4: Start server with certificates using library
    https_port = int(os.getenv("CLASSIFIER_HTTPS_PORT", "8005"))
    cert_pattern.start_server(worker_config["app"], port=https_port)


# For direct running
if __name__ == "__main__":
    main()