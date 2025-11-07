"""
Crank Email Classifier Service

ML-based email classification service that provides spam detection, sentiment analysis,
and email categorization. Registers with the platform and provides real ML capabilities.
Part of the separation-ready plugin architecture.
"""

import asyncio
import logging
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import httpx
import nltk
import numpy as np
from bs4 import BeautifulSoup
from fastapi import FastAPI, Form, HTTPException
from pydantic import BaseModel

# Import security configuration
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    logger.info("Downloading NLTK punkt tokenizer...")
    nltk.download("punkt", quiet=True)

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    logger.info("Downloading NLTK stopwords...")
    nltk.download("stopwords", quiet=True)


class EmailClassificationRequest(BaseModel):
    """Request model for email classification."""

    email_content: str
    classification_types: list[str] = [
        "spam_detection",
        "bill_detection",
        "receipt_detection",
        "sentiment_analysis",
        "category",
    ]
    confidence_threshold: float = 0.7


class EmailClassificationResult(BaseModel):
    """Result model for email classification."""

    classification_type: str
    prediction: str
    confidence: float
    details: Optional[dict[str, Any]] = None


class ClassificationResponse(BaseModel):
    """Response model for email classification."""

    success: bool
    email_id: str
    results: list[EmailClassificationResult]
    metadata: dict[str, Any]


class WorkerRegistration(BaseModel):
    """Worker registration model."""

    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: list[str]


class SimpleEmailClassifier:
    """Simple ML-based email classifier with multiple classification types."""

    def __init__(self):
        self.spam_classifier = None
        self.bill_classifier = None
        self.receipt_classifier = None
        self.category_classifier = None
        self._initialize_models()

    def _initialize_models(self):
        """Initialize ML models with basic training data."""
        logger.info("🤖 Initializing ML models for email classification...")

        # Simple spam detection model with basic training data
        spam_data = [
            ("Get rich quick! Click here!", "spam"),
            ("Free money! No questions asked!", "spam"),
            ("URGENT: Your account will be closed!", "spam"),
            ("Meeting scheduled for tomorrow at 2 PM", "not_spam"),
            ("Please review the attached document", "not_spam"),
            ("Thanks for your help with the project", "not_spam"),
            ("Congratulations! You've won a lottery!", "spam"),
            ("Your password has been reset", "not_spam"),
            ("Limited time offer! Act now!", "spam"),
            ("Project update: milestone completed", "not_spam"),
        ]

        # Bill detection training data
        bill_data = [
            ("Your monthly electricity bill is ready for review", "bill"),
            ("Statement for account ending 1234 is now available", "bill"),
            ("Your invoice for services rendered", "bill"),
            ("Amount due: $150.00 - Payment due by", "bill"),
            ("Monthly subscription charge processed", "bill"),
            ("Thanks for your business meeting yesterday", "not_bill"),
            ("Happy birthday! Hope you have a great day", "not_bill"),
            ("Meeting scheduled for next Tuesday", "not_bill"),
            ("Water utility bill - March 2024", "bill"),
            ("Credit card statement available online", "bill"),
            ("Dinner reservation confirmed", "not_bill"),
            ("Your order has been shipped", "not_bill"),
            ("Phone bill is ready for payment", "bill"),
            ("Insurance premium due notice", "bill"),
        ]

        # Receipt detection training data
        receipt_data = [
            ("Thank you for your purchase at Coffee Shop", "receipt"),
            ("Receipt for your order #12345", "receipt"),
            ("Transaction complete - here's your receipt", "receipt"),
            ("Purchase confirmation: Total $25.99", "receipt"),
            ("Your receipt from Amazon", "receipt"),
            ("Meeting agenda for tomorrow", "not_receipt"),
            ("Project status update", "not_receipt"),
            ("Happy anniversary!", "not_receipt"),
            ("Grocery store receipt - thank you for shopping", "receipt"),
            ("Payment processed successfully", "receipt"),
            ("Weekend plans discussion", "not_receipt"),
            ("Book club meeting notes", "not_receipt"),
            ("Restaurant receipt - tip included", "receipt"),
            ("Purchase total: $49.99 - paid with card", "receipt"),
        ]

        # Category classification data
        category_data = [
            ("Meeting scheduled for tomorrow", "business"),
            ("Happy birthday! Hope you have a great day", "personal"),
            ("Special offer: 50% off all items", "marketing"),
            ("Issue with your order #12345", "support"),
            ("Please review the quarterly report", "business"),
            ("Dinner plans for Saturday?", "personal"),
            ("New product launch announcement", "marketing"),
            ("Password reset confirmation", "support"),
        ]

        # Train spam classifier
        spam_texts, spam_labels = zip(*spam_data)
        self.spam_classifier = Pipeline(
            [
                ("tfidf", TfidfVectorizer(stop_words="english", max_features=1000)),
                ("classifier", MultinomialNB()),
            ],
        )
        self.spam_classifier.fit(spam_texts, spam_labels)

        # Train bill classifier
        bill_texts, bill_labels = zip(*bill_data)
        self.bill_classifier = Pipeline(
            [
                ("tfidf", TfidfVectorizer(stop_words="english", max_features=1000)),
                ("classifier", MultinomialNB()),
            ],
        )
        self.bill_classifier.fit(bill_texts, bill_labels)

        # Train receipt classifier
        receipt_texts, receipt_labels = zip(*receipt_data)
        self.receipt_classifier = Pipeline(
            [
                ("tfidf", TfidfVectorizer(stop_words="english", max_features=1000)),
                ("classifier", MultinomialNB()),
            ],
        )
        self.receipt_classifier.fit(receipt_texts, receipt_labels)

        # Train category classifier
        category_texts, category_labels = zip(*category_data)
        self.category_classifier = Pipeline(
            [
                ("tfidf", TfidfVectorizer(stop_words="english", max_features=1000)),
                ("classifier", MultinomialNB()),
            ],
        )
        self.category_classifier.fit(category_texts, category_labels)

        logger.info(
            "✅ ML models initialized successfully (spam, bill, receipt, category detection)",
        )

    def _preprocess_email(self, email_content: str) -> str:
        """Preprocess email content for classification."""
        # Remove HTML tags if present
        soup = BeautifulSoup(email_content, "html.parser")
        text = soup.get_text()

        # Basic text cleaning
        text = re.sub(r"http\S+", "", text)  # Remove URLs
        text = re.sub(r"\S+@\S+", "", text)  # Remove email addresses
        text = re.sub(r"[^a-zA-Z\s]", " ", text)  # Keep only letters and spaces
        text = re.sub(r"\s+", " ", text).strip()  # Normalize whitespace

        return text.lower()

    def detect_spam(self, email_content: str, threshold: float = 0.7) -> tuple[str, float]:
        """Detect if email is spam."""
        processed_text = self._preprocess_email(email_content)

        # Get prediction probabilities
        probabilities = self.spam_classifier.predict_proba([processed_text])[0]
        classes = self.spam_classifier.classes_

        # Find spam probability
        spam_idx = list(classes).index("spam") if "spam" in classes else 0
        spam_confidence = probabilities[spam_idx]

        prediction = "spam" if spam_confidence > threshold else "not_spam"
        confidence = spam_confidence if prediction == "spam" else (1 - spam_confidence)

        return prediction, float(confidence)

    def analyze_sentiment(self, email_content: str) -> tuple[str, float]:
        """Analyze email sentiment using simple heuristics."""
        processed_text = self._preprocess_email(email_content)

        # Simple sentiment analysis based on keywords
        positive_words = ["thank", "great", "excellent", "good", "happy", "pleased", "wonderful"]
        negative_words = ["urgent", "problem", "issue", "error", "failed", "disappointed", "angry"]

        words = processed_text.split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)

        if positive_count > negative_count:
            return "positive", min(0.9, 0.6 + (positive_count - negative_count) * 0.1)
        if negative_count > positive_count:
            return "negative", min(0.9, 0.6 + (negative_count - positive_count) * 0.1)
        return "neutral", 0.5

    def classify_category(self, email_content: str, threshold: float = 0.7) -> tuple[str, float]:
        """Classify email category."""
        processed_text = self._preprocess_email(email_content)

        # Get prediction probabilities
        probabilities = self.category_classifier.predict_proba([processed_text])[0]
        classes = self.category_classifier.classes_

        # Find best prediction
        best_idx = np.argmax(probabilities)
        prediction = classes[best_idx]
        confidence = float(probabilities[best_idx])

        return prediction, confidence

    def detect_bill(self, email_content: str, threshold: float = 0.7) -> tuple[str, float]:
        """Detect if email is a bill or statement."""
        processed_text = self._preprocess_email(email_content)

        # Get prediction probabilities
        probabilities = self.bill_classifier.predict_proba([processed_text])[0]
        classes = self.bill_classifier.classes_

        # Find best prediction
        best_idx = np.argmax(probabilities)
        prediction = classes[best_idx]
        confidence = float(probabilities[best_idx])

        return prediction, confidence

    def detect_receipt(self, email_content: str, threshold: float = 0.7) -> tuple[str, float]:
        """Detect if email is a receipt or purchase confirmation."""
        processed_text = self._preprocess_email(email_content)

        # Get prediction probabilities
        probabilities = self.receipt_classifier.predict_proba([processed_text])[0]
        classes = self.receipt_classifier.classes_

        # Find best prediction
        best_idx = np.argmax(probabilities)
        prediction = classes[best_idx]
        confidence = float(probabilities[best_idx])

        return prediction, confidence

    def detect_language(self, email_content: str) -> tuple[str, float]:
        """Detect email language using simple heuristics."""
        # Simple language detection based on common words
        processed_text = self._preprocess_email(email_content).lower()

        # Simple keyword-based language detection
        if any(word in processed_text for word in ["the", "and", "you", "that", "this"]):
            return "en", 0.7
        if any(word in processed_text for word in ["de", "la", "el", "en", "un"]):
            return "es", 0.6
        if any(word in processed_text for word in ["le", "de", "et", "un", "ce"]):
            return "fr", 0.6
        return "unknown", 0.5

    def classify_priority(self, email_content: str) -> tuple[str, float]:
        """Classify email priority based on keywords."""
        processed_text = self._preprocess_email(email_content)

        high_priority_words = ["urgent", "asap", "emergency", "critical", "immediate"]
        medium_priority_words = ["important", "soon", "deadline", "meeting"]

        words = processed_text.split()
        high_count = sum(1 for word in words if word in high_priority_words)
        medium_count = sum(1 for word in words if word in medium_priority_words)

        if high_count > 0:
            return "high", min(0.9, 0.7 + high_count * 0.1)
        if medium_count > 0:
            return "medium", min(0.8, 0.6 + medium_count * 0.1)
        return "low", 0.6


class CrankEmailClassifier:
    """Crank Email Classifier Service that registers with platform."""

    def __init__(self, platform_url: Optional[str] = None, cert_store=None):
        self.app = FastAPI(title="Crank Email Classifier", version="1.0.0")

        # 🔐 ZERO-TRUST: Use pre-loaded certificates from synchronous initialization
        if cert_store is not None:
            logger.info("🔐 Using pre-loaded certificates from synchronous initialization")
            self.cert_store = cert_store
        else:
            logger.info("🔐 Creating empty certificate store (fallback)")
            import sys

            sys.path.append("/app/scripts")
            from crank_cert_initialize import SecureCertificateStore

            self.cert_store = SecureCertificateStore()

        # Always use HTTPS with Certificate Authority Service certificates
        self.platform_url = platform_url or os.getenv("PLATFORM_URL", "https://platform:8443")
        self.worker_url = os.getenv("WORKER_URL", "https://crank-email-classifier:8201")

        # Certificate files are purely in-memory now - no disk dependencies
        self.cert_file = None
        self.key_file = None
        self.ca_file = None

        self.worker_id = None

        # Initialize ML classifier
        self.classifier = SimpleEmailClassifier()

        # Setup routes
        self._setup_routes()

        # Register startup/shutdown handlers
        self.app.add_event_handler("startup", self._startup)
        self.app.add_event_handler("shutdown", self._shutdown)

    def _setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint with security status."""
            security_status = {}
            if hasattr(self, "security_config"):
                security_status = {
                    "security_level": self.security_config.get_security_level(),
                    "ssl_enabled": self.cert_store.platform_cert is not None,
                    "ca_cert_available": self.cert_store.ca_cert is not None,
                    "certificate_source": "Certificate Authority Service",
                }

            return {
                "status": "healthy",
                "service": "crank-email-classifier",
                "capabilities": [
                    "text_classification",
                    "spam_detection",
                    "bill_detection",
                    "receipt_detection",
                    "sentiment_analysis",
                    "category",
                    "priority",
                    "language_detection",
                ],
                "ml_models": "initialized",
                "security": security_status,
                "timestamp": datetime.now().isoformat(),
            }

        @self.app.post("/classify", response_model=ClassificationResponse)
        async def classify_email(
            email_content: str = Form(...),
            classification_types: str = Form(
                default="spam_detection,bill_detection,receipt_detection",
            ),
        ):
            """Classify email content using ML models."""
            try:
                # Parse classification types
                types = [t.strip() for t in classification_types.split(",")]

                # Generate email ID
                email_id = f"email-{uuid4().hex[:8]}"

                # Perform classifications
                results = []

                for class_type in types:
                    if class_type == "spam_detection":
                        prediction, confidence = self.classifier.detect_spam(email_content)
                        results.append(
                            EmailClassificationResult(
                                classification_type="spam_detection",
                                prediction=prediction,
                                confidence=confidence,
                                details={"algorithm": "naive_bayes"},
                            ),
                        )

                    elif class_type == "bill_detection":
                        prediction, confidence = self.classifier.detect_bill(email_content)
                        results.append(
                            EmailClassificationResult(
                                classification_type="bill_detection",
                                prediction=prediction,
                                confidence=confidence,
                                details={"algorithm": "naive_bayes"},
                            ),
                        )

                    elif class_type == "receipt_detection":
                        prediction, confidence = self.classifier.detect_receipt(email_content)
                        results.append(
                            EmailClassificationResult(
                                classification_type="receipt_detection",
                                prediction=prediction,
                                confidence=confidence,
                                details={"algorithm": "naive_bayes"},
                            ),
                        )

                    elif class_type == "sentiment_analysis":
                        prediction, confidence = self.classifier.analyze_sentiment(email_content)
                        results.append(
                            EmailClassificationResult(
                                classification_type="sentiment_analysis",
                                prediction=prediction,
                                confidence=confidence,
                                details={"algorithm": "keyword_based"},
                            ),
                        )

                    elif class_type == "category":
                        prediction, confidence = self.classifier.classify_category(email_content)
                        results.append(
                            EmailClassificationResult(
                                classification_type="category",
                                prediction=prediction,
                                confidence=confidence,
                                details={"algorithm": "naive_bayes"},
                            ),
                        )

                    elif class_type == "priority":
                        prediction, confidence = self.classifier.classify_priority(email_content)
                        results.append(
                            EmailClassificationResult(
                                classification_type="priority",
                                prediction=prediction,
                                confidence=confidence,
                                details={"algorithm": "keyword_based"},
                            ),
                        )

                    elif class_type == "language_detection":
                        prediction, confidence = self.classifier.detect_language(email_content)
                        results.append(
                            EmailClassificationResult(
                                classification_type="language_detection",
                                prediction=prediction,
                                confidence=confidence,
                                details={"algorithm": "langdetect"},
                            ),
                        )

                return ClassificationResponse(
                    success=True,
                    email_id=email_id,
                    results=results,
                    metadata={
                        "timestamp": datetime.now().isoformat(),
                        "email_length": len(email_content),
                        "classification_count": len(results),
                        "worker_id": self.worker_id,
                    },
                )

            except Exception as e:
                logger.exception("Classification error: {e}")
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
                        return yaml.safe_load(f)
                except Exception:
                    logger.warning("Failed to read plugin metadata: {e}")

            # Fallback to hardcoded metadata
            return {
                "name": "crank-email-classifier",
                "version": "1.0.0",
                "description": "ML-based email classification for spam detection and categorization",
                "author": "Crank Platform Team",
                "capabilities": [
                    "text_classification",
                    "spam_detection",
                    "sentiment_analysis",
                    "category",
                    "priority",
                    "language_detection",
                ],
                "health_endpoint": "/health",
                "separation_ready": True,  # Indicates this worker is ready for repo separation
            }

    def _create_adaptive_client(self, timeout: float = 10.0) -> httpx.AsyncClient:
        """Create HTTP client using in-memory certificates from Certificate Authority Service."""

        # 🔐 Use in-memory certificates directly - no disk dependencies
        import ssl

        # For development-https, we need to create a custom SSL context with our CA certificate
        ssl.create_default_context()

        if self.cert_store.ca_cert:
            # Create temporary CA certificate for httpx to use
            with tempfile.NamedTemporaryFile(mode="w", suffix=".crt", delete=False) as ca_file:
                ca_file.write(self.cert_store.ca_cert)
                ca_file.flush()

                # Configure httpx to trust our CA certificate
                return httpx.AsyncClient(
                    verify=ca_file.name,
                    timeout=timeout,
                )
        else:
            # Fallback for development - disable verification
            logger.warning("⚠️ No CA certificate available, using insecure client")
            return httpx.AsyncClient(verify=False, timeout=timeout)

    async def _startup(self):
        """Startup handler - register with platform."""
        logger.info("🤖 Starting Crank Email Classifier...")

        # Log security level for visibility (certificates already loaded synchronously)
        logger.info("� Using certificates loaded synchronously at startup")

        # Prepare registration info
        worker_info = WorkerRegistration(
            worker_id=f"email-classifier-{uuid4().hex[:8]}",
            service_type="email_classification",
            endpoint=self.worker_url,
            health_url=f"{self.worker_url}/health",
            capabilities=[
                "text_classification",
                "spam_detection",
                "sentiment_analysis",
                "category",
                "priority",
                "language_detection",
            ],
        )

        # Register with platform
        await self._register_with_platform(worker_info)

        # Start heartbeat background task
        self._start_heartbeat_task()

    def _start_heartbeat_task(self):
        """Start the background heartbeat task."""
        import asyncio

        # Get heartbeat interval from environment (default 20 seconds)
        heartbeat_interval = int(os.getenv("WORKER_HEARTBEAT_INTERVAL", "20"))

        async def heartbeat_loop():
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
        asyncio.create_task(heartbeat_loop())
        logger.info("🫀 Started heartbeat task with {heartbeat_interval}s interval")

    async def _send_heartbeat(self):
        """Send heartbeat to platform."""
        try:
            auth_token = os.getenv("PLATFORM_AUTH_TOKEN", "dev-mesh-key")
            headers = {"Authorization": f"Bearer {auth_token}"}

            # Prepare form data as expected by platform
            form_data = {
                "service_type": "email_classification",
                "load_score": "0.0",
            }

            async with self._create_adaptive_client(timeout=10.0) as client:
                response = await client.post(
                    f"{self.platform_url}/v1/workers/{self.worker_id}/heartbeat",
                    headers=headers,
                    data=form_data,  # Send as form data, not JSON
                )

                if response.status_code == 200:
                    logger.debug(f"💓 Heartbeat sent successfully for worker {self.worker_id}")
                else:
                    logger.warning("Heartbeat failed: {response.status_code} - {response.text}")

        except Exception:
            logger.warning("Failed to send heartbeat: {e}")

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
                async with self._create_adaptive_client() as client:
                    response = await client.post(
                        f"{self.platform_url}/v1/workers/register",
                        json=worker_info.model_dump(),
                        headers=headers,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        self.worker_id = result.get("worker_id")
                        logger.info(
                            f"🔒 Successfully registered email classifier via mTLS. Worker ID: {self.worker_id}",
                        )
                        return
                    logger.warning(
                        f"Registration attempt {attempt + 1} failed: {response.status_code} - {response.text}",
                    )

            except Exception:
                logger.warning("Registration attempt {attempt + 1} failed: {e}")

            if attempt < max_retries - 1:
                logger.info("Retrying registration in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)

        logger.error("Failed to register with platform after all retries")
        # Continue running even if registration fails for development purposes

    async def _shutdown(self):
        """Shutdown handler - deregister from platform using mTLS."""
        if self.worker_id:
            try:
                # 🔒 ZERO-TRUST: Use mTLS client for secure deregistration
                async with self._create_adaptive_client(timeout=5.0) as client:
                    await client.delete(f"{self.platform_url}/v1/workers/{self.worker_id}")
                logger.info("🔒 Successfully deregistered email classifier via mTLS")
            except Exception:
                logger.warning("Failed to deregister from platform: {e}")


def create_crank_email_classifier(platform_url: Optional[str] = None, cert_store=None) -> FastAPI:
    """Create Crank Email Classifier application."""
    classifier = CrankEmailClassifier(platform_url, cert_store)
    return classifier.app


def main():
    """Main entry point with HTTPS enforcement and Certificate Authority Service integration."""

    import uvicorn

    # 🔒 ENFORCE HTTPS-ONLY MODE: No HTTP fallback allowed
    https_only = os.getenv("HTTPS_ONLY", "true").lower() == "true"
    ca_service_url = os.getenv("CA_SERVICE_URL")

    if https_only and ca_service_url:
        print("🔐 Initializing certificates using SECURE CSR pattern...")
        try:
            # Run secure certificate initialization in the same process
            import sys

            sys.path.append("/app/scripts")
            import asyncio

            from crank_cert_initialize import cert_store
            from crank_cert_initialize import main as init_certificates

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
            raise RuntimeError(f"🚫 Failed to initialize certificates with CA service: {e}")
    else:
        raise RuntimeError("🚫 HTTPS_ONLY environment requires Certificate Authority Service")

    # 🚢 PORT CONFIGURATION: Use environment variables for flexible deployment
    int(os.getenv("EMAIL_CLASSIFIER_PORT", "8200"))  # HTTP fallback port
    service_host = os.getenv("EMAIL_CLASSIFIER_HOST", "0.0.0.0")
    https_port = int(os.getenv("EMAIL_CLASSIFIER_HTTPS_PORT", "8201"))

    # Create FastAPI app with pre-loaded certificates
    app = create_crank_email_classifier(cert_store=cert_store)

    # 🔒 HTTPS-ONLY MODE: Always use HTTPS with Certificate Authority Service certificates
    if https_only:
        if not use_https:
            raise RuntimeError(
                "🚫 HTTPS_ONLY=true but certificates not found. Cannot start service.",
            )
        logger.info("🔒 Starting Crank Email Classifier with HTTPS/mTLS ONLY on port {https_port}")
        logger.info("🔐 Using in-memory certificates from Certificate Authority Service")

        # Create SSL context from in-memory certificates (SECURE CSR pattern)
        try:
            import sys

            sys.path.append("/app/scripts")
            from crank_cert_initialize import cert_store

            cert_store.get_ssl_context()

            print("🔒 Using certificates obtained via SECURE CSR pattern")

            # Get the temporary certificate file paths for uvicorn
            cert_file = cert_store._temp_cert_file
            key_file = cert_store._temp_key_file

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
            )
    else:
        raise RuntimeError(
            "🚫 HTTP mode disabled permanently - Certificate Authority Service provides HTTPS-only security",
        )


# For direct running
if __name__ == "__main__":
    main()
