"""
Crank Image Classifier Service

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


class WorkerRegistration(BaseModel):
    """Worker registration model."""
    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: List[str]


class SimpleImageClassifier:
    """Simple computer vision classifier using OpenCV and basic ML."""
    
    def __init__(self):
        self.face_cascade = None
        self.eye_cascade = None
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize CV models and cascades."""
        logger.info("🖼️ Initializing computer vision models...")
        
        try:
            # Load OpenCV Haar cascades for object detection
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            logger.info("✅ OpenCV cascades loaded successfully")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load some OpenCV cascades: {e}")
        
        logger.info("✅ Computer vision models initialized")
    
    def _load_image(self, image_data: bytes) -> Tuple[np.ndarray, Image.Image]:
        """Load image from bytes into both OpenCV and PIL formats."""
        # Load with PIL
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Convert to OpenCV format
        opencv_image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
        
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
            blue_pixels = np.sum((opencv_image[:,:,0] > opencv_image[:,:,1]) & 
                               (opencv_image[:,:,0] > opencv_image[:,:,2]))
            green_pixels = np.sum((opencv_image[:,:,1] > opencv_image[:,:,0]) & 
                                (opencv_image[:,:,1] > opencv_image[:,:,2]))
            
            blue_ratio = blue_pixels / total_pixels
            green_ratio = green_pixels / total_pixels
            
            # Simple scene classification based on color ratios
            if blue_ratio > 0.3:
                return "outdoor_sky", 0.7
            elif green_ratio > 0.4:
                return "nature_outdoor", 0.8
            elif np.mean(opencv_image) < 100:
                return "indoor_dark", 0.6
            else:
                return "indoor_bright", 0.5
                
        except Exception as e:
            logger.error(f"Scene classification error: {e}")
            return "unknown", 0.0
    
    def assess_content_safety(self, image_data: bytes) -> Tuple[str, float]:
        """Basic content safety assessment using image properties."""
        try:
            opencv_image, pil_image = self._load_image(image_data)
            
            # Simple safety checks based on image properties
            
            # Check image size (very large or very small might be suspicious)
            height, width = opencv_image.shape[:2]
            aspect_ratio = width / height
            
            # Check color diversity (monochrome might indicate certain content)
            color_std = np.std(opencv_image)
            
            # Check brightness distribution
            brightness = np.mean(cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY))
            
            # Simple heuristic scoring
            safety_score = 0.8  # Start with safe assumption
            
            # Adjust based on properties
            if aspect_ratio > 3.0 or aspect_ratio < 0.3:
                safety_score -= 0.1  # Unusual aspect ratios
            
            if color_std < 10:
                safety_score -= 0.2  # Very low color diversity
            
            if brightness < 30 or brightness > 220:
                safety_score -= 0.1  # Very dark or very bright
            
            # Classify as safe or needs_review
            if safety_score > 0.6:
                return "safe", safety_score
            else:
                return "needs_review", safety_score
                
        except Exception as e:
            logger.error(f"Content safety assessment error: {e}")
            return "unknown", 0.0
    
    def assess_image_quality(self, image_data: bytes) -> Tuple[str, float]:
        """Assess image quality using blur detection and other metrics."""
        try:
            opencv_image, pil_image = self._load_image(image_data)
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Calculate blur using Laplacian variance
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Calculate resolution
            height, width = opencv_image.shape[:2]
            resolution_score = min(1.0, (height * width) / (1920 * 1080))
            
            # Calculate overall quality score
            quality_score = (min(1.0, blur_score / 1000) * 0.7 + resolution_score * 0.3)
            
            if quality_score > 0.7:
                return "high", quality_score
            elif quality_score > 0.4:
                return "medium", quality_score
            else:
                return "low", quality_score
                
        except Exception as e:
            logger.error(f"Quality assessment error: {e}")
            return "unknown", 0.0
    
    def extract_dominant_colors(self, image_data: bytes, n_colors: int = 5) -> Tuple[str, float, Dict]:
        """Extract dominant colors using K-means clustering."""
        try:
            opencv_image, _ = self._load_image(image_data)
            
            # Reshape image to be a list of pixels
            pixels = opencv_image.reshape(-1, 3)
            
            # Use K-means to find dominant colors
            kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
            kmeans.fit(pixels)
            
            # Get the dominant colors
            colors = kmeans.cluster_centers_.astype(int)
            
            # Convert BGR to RGB for color naming
            rgb_colors = []
            color_names = []
            
            for color in colors:
                # Convert BGR to RGB
                rgb_color = (int(color[2]), int(color[1]), int(color[0]))
                rgb_colors.append(rgb_color)
                
                # Try to get closest color name
                try:
                    color_name = webcolors.rgb_to_name(rgb_color)
                except ValueError:
                    # If exact match not found, find closest
                    color_name = self._closest_color_name(rgb_color)
                
                color_names.append(color_name)
            
            dominant_color = color_names[0]  # Most dominant
            
            details = {
                "dominant_colors": color_names,
                "rgb_values": [list(rgb) for rgb in rgb_colors],
                "algorithm": "kmeans_clustering"
            }
            
            return dominant_color, 0.8, details
            
        except Exception as e:
            logger.error(f"Color extraction error: {e}")
            return "unknown", 0.0, {"error": str(e)}
    
    def _closest_color_name(self, rgb_color):
        """Find the closest named color to given RGB."""
        min_colors = {}
        for name in webcolors.CSS3_HEX_TO_NAMES.values():
            try:
                r_c, g_c, b_c = webcolors.name_to_rgb(name)
                rd = (r_c - rgb_color[0]) ** 2
                gd = (g_c - rgb_color[1]) ** 2
                bd = (b_c - rgb_color[2]) ** 2
                min_colors[(rd + gd + bd)] = name
            except ValueError:
                continue
        
        if min_colors:
            return min_colors[min(min_colors.keys())]
        return "unknown"
    
    def detect_text(self, image_data: bytes) -> Tuple[str, float]:
        """Simple text detection using edge detection."""
        try:
            opencv_image, _ = self._load_image(image_data)
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Count edge pixels as a proxy for text presence
            edge_ratio = np.sum(edges > 0) / edges.size
            
            if edge_ratio > 0.1:
                return "text_detected", min(0.9, edge_ratio * 5)
            else:
                return "no_text", 0.3
                
        except Exception as e:
            logger.error(f"Text detection error: {e}")
            return "detection_failed", 0.0


class CrankImageClassifier:
    """Crank Image Classifier Service that registers with platform."""
    
    def __init__(self, platform_url: str = None):
        self.app = FastAPI(title="Crank Image Classifier", version="1.0.0")
        
        # Auto-detect HTTPS based on certificate availability
        cert_dir = Path("/etc/certs")
        has_certs = (cert_dir / "platform.crt").exists() and (cert_dir / "platform.key").exists()
        
        # 🔒 ZERO-TRUST: Always use HTTPS for platform communication when certs available
        if has_certs:
            self.platform_url = platform_url or os.getenv("PLATFORM_URL", "https://platform:8443")
            self.worker_url = os.getenv("WORKER_URL", "https://crank-image-classifier:8443")
            # mTLS client configuration with proper CA handling
            self.cert_file = cert_dir / "platform.crt"
            self.key_file = cert_dir / "platform.key"
            self.ca_file = cert_dir / "ca.crt"  # Use proper CA certificate
        else:
            # Fallback to HTTP only in development without certificates
            self.platform_url = platform_url or os.getenv("PLATFORM_URL", "http://platform:8080")
            self.worker_url = os.getenv("WORKER_URL", "http://crank-image-classifier:8005")
            self.cert_file = None
            self.key_file = None
            self.ca_file = None
            logger.warning("⚠️  No certificates found - falling back to HTTP (development only)")
            
        self.worker_id = None
        
        # Initialize computer vision classifier
        self.classifier = SimpleImageClassifier()
        
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
            return {
                "status": "healthy",
                "service": "crank-image-classifier",
                "capabilities": ["object_detection", "scene_classification", "content_safety", "image_quality", "dominant_colors", "text_detection"],
                "cv_models": "initialized",
                "supported_formats": ["jpg", "jpeg", "png", "bmp", "gif", "webp"],
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/classify", response_model=ClassificationResponse)
        async def classify_image(
            file: UploadFile = File(...),
            classification_types: str = Form(default="object_detection,scene_classification,content_safety")
        ):
            """Classify image using computer vision models."""
            try:
                # Validate file type
                if not file.content_type or not file.content_type.startswith('image/'):
                    raise HTTPException(status_code=400, detail="File must be an image")
                
                # Read image data
                image_data = await file.read()
                
                # Generate image ID
                image_id = f"image-{uuid4().hex[:8]}"
                
                # Parse classification types
                types = [t.strip() for t in classification_types.split(",")]
                
                # Perform classifications
                results = []
                
                for class_type in types:
                    if class_type == "object_detection":
                        prediction, confidence, details = self.classifier.detect_objects(image_data)
                        results.append(ImageClassificationResult(
                            classification_type="object_detection",
                            prediction=prediction,
                            confidence=confidence,
                            details=details
                        ))
                    
                    elif class_type == "scene_classification":
                        prediction, confidence = self.classifier.classify_scene(image_data)
                        results.append(ImageClassificationResult(
                            classification_type="scene_classification", 
                            prediction=prediction,
                            confidence=confidence,
                            details={"algorithm": "color_analysis"}
                        ))
                    
                    elif class_type == "content_safety":
                        prediction, confidence = self.classifier.assess_content_safety(image_data)
                        results.append(ImageClassificationResult(
                            classification_type="content_safety",
                            prediction=prediction,
                            confidence=confidence,
                            details={"algorithm": "property_based"}
                        ))
                    
                    elif class_type == "image_quality":
                        prediction, confidence = self.classifier.assess_image_quality(image_data)
                        results.append(ImageClassificationResult(
                            classification_type="image_quality",
                            prediction=prediction,
                            confidence=confidence,
                            details={"algorithm": "blur_detection"}
                        ))
                    
                    elif class_type == "dominant_colors":
                        prediction, confidence, details = self.classifier.extract_dominant_colors(image_data)
                        results.append(ImageClassificationResult(
                            classification_type="dominant_colors",
                            prediction=prediction,
                            confidence=confidence,
                            details=details
                        ))
                    
                    elif class_type == "text_detection":
                        prediction, confidence = self.classifier.detect_text(image_data)
                        results.append(ImageClassificationResult(
                            classification_type="text_detection",
                            prediction=prediction,
                            confidence=confidence,
                            details={"algorithm": "edge_detection"}
                        ))
                
                return ClassificationResponse(
                    success=True,
                    image_id=image_id,
                    results=results,
                    metadata={
                        "timestamp": datetime.now().isoformat(),
                        "image_size": len(image_data),
                        "image_format": file.content_type,
                        "classification_count": len(results),
                        "worker_id": self.worker_id
                    }
                )
                
            except Exception as e:
                logger.error(f"Image classification error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/plugin")
        async def get_plugin_metadata():
            """Get plugin metadata for platform integration."""
            # Read plugin metadata from file (prepared for future separation)
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
                "name": "crank-image-classifier",
                "version": "1.0.0",
                "description": "Computer vision ML classification for image analysis and object detection",
                "author": "Crank Platform Team",
                "capabilities": ["object_detection", "scene_classification", "content_safety", "image_quality", "dominant_colors", "text_detection"],
                "health_endpoint": "/health",
                "separation_ready": True  # Indicates this worker is ready for repo separation
            }
    
    def _create_mtls_client(self, timeout: float = 10.0) -> httpx.AsyncClient:
        """Create HTTP client with mTLS configuration for platform communication."""
        if self.cert_file and self.key_file and self.ca_file:
            # 🔒 ZERO-TRUST: Use mTLS for secure worker-to-platform communication
            # For development with self-signed certificates, we need to handle verification differently
            environment = os.getenv("CRANK_ENVIRONMENT", "development")
            
            if environment == "development":
                # Development: Use encryption but skip strict cert verification for self-signed certs
                logger.info("🔒 Using mTLS with relaxed verification for development")
                return httpx.AsyncClient(
                    cert=(str(self.cert_file), str(self.key_file)),  # Client certificate
                    verify=False,  # Skip verification for self-signed certs
                    timeout=timeout
                )
            else:
                # Production: Full certificate verification
                logger.info("🔒 Using mTLS with full certificate verification for production")
                return httpx.AsyncClient(
                    cert=(str(self.cert_file), str(self.key_file)),  # Client certificate
                    verify=str(self.ca_file),  # CA certificate to verify platform
                    timeout=timeout
                )
        else:
            # Fallback to plain HTTP (development only)
            logger.warning("⚠️  Using plain HTTP client - certificates not available")
            return httpx.AsyncClient(timeout=timeout)
    
    async def _startup(self):
        """Startup handler - register with platform."""
        logger.info("🖼️ Starting Crank Image Classifier...")
        
        # Prepare registration info
        worker_info = WorkerRegistration(
            worker_id=f"image-classifier-{uuid4().hex[:8]}",
            service_type="image_classification",
            endpoint=self.worker_url,
            health_url=f"{self.worker_url}/health",
            capabilities=["object_detection", "scene_classification", "content_safety", "image_quality", "dominant_colors", "text_detection"]
        )
        
        # Register with platform
        await self._register_with_platform(worker_info)
    
    async def _register_with_platform(self, worker_info: WorkerRegistration):
        """Register this worker with the platform using mTLS."""
        max_retries = 5
        retry_delay = 5  # seconds
        
        # Auth token for platform
        auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "dev-mesh-key")
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        for attempt in range(max_retries):
            try:
                # 🔒 ZERO-TRUST: Use mTLS client for secure communication
                async with self._create_mtls_client() as client:
                    response = await client.post(
                        f"{self.platform_url}/v1/workers/register",
                        json=worker_info.model_dump(),
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.worker_id = result.get("worker_id")
                        logger.info(f"🔒 Successfully registered image classifier via mTLS. Worker ID: {self.worker_id}")
                        return
                    else:
                        logger.warning(f"Registration attempt {attempt + 1} failed: {response.status_code} - {response.text}")
                        
            except Exception as e:
                logger.warning(f"Registration attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying registration in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
        
        logger.error("Failed to register with platform after all retries")
        # Continue running even if registration fails for development purposes
    
    async def _shutdown(self):
        """Shutdown handler - deregister from platform using mTLS."""
        if self.worker_id:
            try:
                # 🔒 ZERO-TRUST: Use mTLS client for secure deregistration
                async with self._create_mtls_client(timeout=5.0) as client:
                    await client.delete(f"{self.platform_url}/v1/workers/{self.worker_id}")
                logger.info("🔒 Successfully deregistered image classifier via mTLS")
            except Exception as e:
                logger.warning(f"Failed to deregister from platform: {e}")


def create_crank_image_classifier(platform_url: str = None) -> FastAPI:
    """Create Crank Image Classifier application."""
    classifier = CrankImageClassifier(platform_url)
    return classifier.app


def main():
    """Main entry point with HTTPS auto-detection."""
    import uvicorn
    from pathlib import Path
    
    app = create_crank_image_classifier()
    
    # 🔒 ZERO-TRUST: Auto-detect HTTPS based on certificate availability
    cert_dir = Path("/etc/certs")
    has_certs = (cert_dir / "platform.crt").exists() and (cert_dir / "platform.key").exists()
    
    if has_certs:
        # Start with HTTPS using mTLS
        print("🔒 Starting Crank Image Classifier with HTTPS on port 8443")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8443,
            ssl_keyfile=str(cert_dir / "platform.key"),
            ssl_certfile=str(cert_dir / "platform.crt")
        )
    else:
        print("⚠️  Starting Crank Image Classifier with HTTP on port 8005 (development only)")
        uvicorn.run(app, host="0.0.0.0", port=8005)


# For direct running
if __name__ == "__main__":
    main()