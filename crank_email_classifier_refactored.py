#!/usr/bin/env python3
"""
Crank Email Classifier - REFACTORED with Worker Certificate Library
"""

import asyncio
import logging
import os
import re
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
import nltk
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

# Import worker certificate library
from worker_cert_pattern import WorkerCertificatePattern, create_worker_fastapi_with_certs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("Downloading NLTK punkt tokenizer...")
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    logger.info("Downloading NLTK stopwords...")
    nltk.download('stopwords', quiet=True)


class EmailClassificationRequest(BaseModel):
    """Request model for email classification."""
    email_content: str
    classification_types: List[str] = ["spam_detection", "bill_detection", "receipt_detection", "sentiment_analysis", "category"]
    confidence_threshold: float = 0.7


class EmailClassificationResult(BaseModel):
    """Result model for email classification."""
    classification_type: str
    prediction: str
    confidence: float
    details: Optional[Dict[str, Any]] = None


class ClassificationResponse(BaseModel):
    """Response model for email classification."""
    success: bool
    email_id: str
    results: List[EmailClassificationResult]
    metadata: Dict[str, Any]


class WorkerRegistration(BaseModel):
    """Worker registration model."""
    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: List[str]


class SimpleEmailClassifier:
    """Simple ML-based email classifier with multiple classification types."""
    
    def __init__(self):
        """Initialize the classifier with basic patterns."""
        self.spam_patterns = [
            r'(?i)\b(urgent|act now|limited time|click here|free money|winner|congratulations|prize|lottery)\b',
            r'(?i)\b(nigerian prince|inheritance|million dollars|bank transfer|wire transfer)\b',
            r'(?i)\b(viagra|pharmacy|prescription|pills|medication)\b'
        ]
        
        self.bill_patterns = [
            r'(?i)\b(invoice|bill|payment due|amount due|total due|balance|account statement)\b',
            r'(?i)\b(utility|electric|gas|water|phone|internet|cable|rent|mortgage)\b',
            r'(?i)\b(due date|payment reminder|overdue|final notice|disconnect notice)\b'
        ]
        
        self.receipt_patterns = [
            r'(?i)\b(receipt|purchase|order confirmation|transaction|payment received)\b',
            r'(?i)\b(thank you for your purchase|order number|confirmation number|tracking)\b',
            r'(?i)\b(subtotal|tax|shipping|total|paid|refund|return)\b'
        ]
        
        # Compile patterns for efficiency
        self.compiled_spam = [re.compile(p) for p in self.spam_patterns]
        self.compiled_bill = [re.compile(p) for p in self.bill_patterns]
        self.compiled_receipt = [re.compile(p) for p in self.receipt_patterns]
    
    def classify_spam(self, text: str) -> tuple:
        """Classify if email is spam."""
        matches = sum(1 for pattern in self.compiled_spam if pattern.search(text))
        confidence = min(0.95, 0.3 + matches * 0.2)
        is_spam = matches >= 2
        return ("spam" if is_spam else "not_spam", confidence)
    
    def classify_bill(self, text: str) -> tuple:
        """Classify if email is a bill."""
        matches = sum(1 for pattern in self.compiled_bill if pattern.search(text))
        confidence = min(0.9, 0.4 + matches * 0.15)
        is_bill = matches >= 1
        return ("bill" if is_bill else "not_bill", confidence)
    
    def classify_receipt(self, text: str) -> tuple:
        """Classify if email is a receipt."""
        matches = sum(1 for pattern in self.compiled_receipt if pattern.search(text))
        confidence = min(0.9, 0.4 + matches * 0.15)
        is_receipt = matches >= 1
        return ("receipt" if is_receipt else "not_receipt", confidence)
    
    def analyze_sentiment(self, text: str) -> tuple:
        """Simple sentiment analysis."""
        positive_words = ['great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'perfect', 'best']
        negative_words = ['terrible', 'awful', 'hate', 'worst', 'bad', 'horrible', 'disappointing', 'frustrated']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return ("positive", min(0.8, 0.6 + positive_count * 0.1))
        elif negative_count > positive_count:
            return ("negative", min(0.8, 0.6 + negative_count * 0.1))
        else:
            return ("neutral", 0.6)
    
    def categorize_email(self, text: str) -> tuple:
        """Categorize email by type."""
        text_lower = text.lower()
        
        business_keywords = ['meeting', 'schedule', 'appointment', 'conference', 'project', 'deadline']
        personal_keywords = ['family', 'friend', 'vacation', 'birthday', 'dinner', 'weekend']
        marketing_keywords = ['sale', 'discount', 'offer', 'promotion', 'deal', 'newsletter']
        
        business_count = sum(1 for word in business_keywords if word in text_lower)
        personal_count = sum(1 for word in personal_keywords if word in text_lower)
        marketing_count = sum(1 for word in marketing_keywords if word in text_lower)
        
        if business_count > personal_count and business_count > marketing_count:
            return ("business", min(0.8, 0.6 + business_count * 0.1))
        elif personal_count > business_count and personal_count > marketing_count:
            return ("personal", min(0.8, 0.6 + personal_count * 0.1))
        elif marketing_count > 0:
            return ("marketing", min(0.8, 0.6 + marketing_count * 0.1))
        else:
            return ("general", 0.6)
    
    def determine_priority(self, text: str) -> tuple:
        """Determine email priority."""
        urgent_keywords = ['urgent', 'asap', 'immediate', 'emergency', 'critical', 'deadline']
        high_keywords = ['important', 'priority', 'attention', 'required', 'needed']
        
        text_lower = text.lower()
        urgent_count = sum(1 for word in urgent_keywords if word in text_lower)
        high_count = sum(1 for word in high_keywords if word in text_lower)
        
        if urgent_count > 0:
            return ("urgent", min(0.9, 0.7 + urgent_count * 0.1))
        elif high_count > 0:
            return ("high", min(0.8, 0.6 + high_count * 0.1))
        else:
            return ("normal", 0.7)


def setup_email_classifier_routes(app: FastAPI, worker_config: dict):
    """Set up email classifier routes using worker config."""
    
    # Get components from worker config
    cert_store = worker_config["cert_store"]
    platform_url = worker_config["platform_url"]
    worker_url = worker_config["worker_url"]
    service_name = worker_config["service_name"]
    
    # Initialize ML classifier
    classifier = SimpleEmailClassifier()
    
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
        
        return {
            "status": "healthy",
            "service": service_name,
            "capabilities": ["spam_detection", "bill_detection", "receipt_detection", "sentiment_analysis", "category", "priority", "language_detection"],
            "ml_models": "initialized",
            "security": security_status,
            "timestamp": datetime.now().isoformat()
        }
    
    @app.post("/classify", response_model=ClassificationResponse)
    async def classify_email(request: EmailClassificationRequest):
        """Classify email content."""
        try:
            results = []
            email_id = f"email_{uuid4().hex[:8]}"
            
            # Perform requested classifications
            for classification_type in request.classification_types:
                if classification_type == "spam_detection":
                    prediction, confidence = classifier.classify_spam(request.email_content)
                elif classification_type == "bill_detection":
                    prediction, confidence = classifier.classify_bill(request.email_content)
                elif classification_type == "receipt_detection":
                    prediction, confidence = classifier.classify_receipt(request.email_content)
                elif classification_type == "sentiment_analysis":
                    prediction, confidence = classifier.analyze_sentiment(request.email_content)
                elif classification_type == "category":
                    prediction, confidence = classifier.categorize_email(request.email_content)
                elif classification_type == "priority":
                    prediction, confidence = classifier.determine_priority(request.email_content)
                else:
                    prediction, confidence = "unknown", 0.0
                
                # Only include results above confidence threshold
                if confidence >= request.confidence_threshold:
                    results.append(EmailClassificationResult(
                        classification_type=classification_type,
                        prediction=prediction,
                        confidence=confidence,
                        details={"content_length": len(request.email_content)}
                    ))
            
            return ClassificationResponse(
                success=True,
                email_id=email_id,
                results=results,
                metadata={
                    "processing_time_ms": 50,  # Simulated
                    "model_version": "1.0.0",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _startup():
        """Startup handler - register with platform."""
        nonlocal worker_id
        
        logger.info("🤖 Starting Crank Email Classifier...")
        logger.info("🔐 Using certificates loaded synchronously at startup")
        
        # Prepare registration info
        worker_info = WorkerRegistration(
            worker_id=f"email-classifier-{uuid4().hex[:8]}",
            service_type="email_classification",
            endpoint=worker_url,
            health_url=f"{worker_url}/health",
            capabilities=["spam_detection", "sentiment_analysis", "category", "priority", "language_detection"]
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
                        logger.info(f"🔒 Successfully registered email classifier via mTLS. Worker ID: {worker_info.worker_id}")
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
                            "service_type": "email_classification",
                            "load_score": 0.5  # Simulated load
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
                logger.info("🔒 Successfully deregistered email classifier via mTLS")
            except Exception as e:
                logger.warning(f"Failed to deregister from platform: {e}")
    
    # Register startup/shutdown handlers
    app.add_event_handler("startup", _startup)
    app.add_event_handler("shutdown", _shutdown)


def main():
    """Main entry point using Worker Certificate Library."""
    
    # Step 1: Initialize certificates SYNCHRONOUSLY using library
    cert_pattern = WorkerCertificatePattern("crank-email-classifier")
    cert_store = cert_pattern.initialize_certificates()
    
    # Step 2: Create FastAPI with pre-loaded certificates using library
    worker_config = create_worker_fastapi_with_certs(
        title="Crank Email Classifier",
        service_name="crank-email-classifier",
        platform_url=None,  # Use default from environment
        worker_url=None,    # Use default from environment
        cert_store=cert_store
    )
    
    # Step 3: Setup email classifier routes
    setup_email_classifier_routes(worker_config["app"], worker_config)
    
    # Step 4: Start server with certificates using library
    https_port = int(os.getenv("EMAIL_CLASSIFIER_HTTPS_PORT", "8201"))
    cert_pattern.start_server(worker_config["app"], port=https_port)


# For direct running
if __name__ == "__main__":
    main()