"""Crank Email Classifier Service - Refactored to use WorkerApplication.

ML-based email classification service providing spam detection, sentiment analysis,
and email categorization using sklearn pipelines.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import nltk  # type: ignore[import-untyped]
import numpy as np
from fastapi import Form, HTTPException
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore[import-untyped]
from sklearn.naive_bayes import MultinomialNB  # type: ignore[import-untyped]
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]

from crank.capabilities.schema import EMAIL_CLASSIFICATION, CapabilityDefinition
from crank.worker_runtime import WorkerApplication

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find("tokenizers/punkt")  # pyright: ignore[reportUnknownMemberType]
except LookupError:
    logger.info("Downloading NLTK punkt tokenizer...")
    nltk.download("punkt", quiet=True)  # pyright: ignore[reportUnknownMemberType]

try:
    nltk.data.find("corpora/stopwords")  # pyright: ignore[reportUnknownMemberType]
except LookupError:
    logger.info("Downloading NLTK stopwords...")
    nltk.download("stopwords", quiet=True)  # pyright: ignore[reportUnknownMemberType]


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


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


# ============================================================================
# ML ENGINE - BUSINESS LOGIC
# ============================================================================


class SimpleEmailClassifier:
    """Simple ML-based email classifier with multiple classification types.
    
    This is the core business logic - pure ML functionality with no infrastructure.
    Uses sklearn pipelines for text classification (TF-IDF + Naive Bayes).
    """

    def __init__(self) -> None:
        # Initialize classifiers - these will be set by _initialize_models
        self.spam_classifier: Pipeline
        self.bill_classifier: Pipeline
        self.receipt_classifier: Pipeline
        self.category_classifier: Pipeline
        self._initialize_models()

    def _initialize_models(self) -> None:
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
        self.spam_classifier.fit(spam_texts, spam_labels)  # pyright: ignore[reportUnknownMemberType]

        # Train bill classifier
        bill_texts, bill_labels = zip(*bill_data)
        self.bill_classifier = Pipeline(
            [
                ("tfidf", TfidfVectorizer(stop_words="english", max_features=500)),
                ("classifier", MultinomialNB()),
            ],
        )
        self.bill_classifier.fit(bill_texts, bill_labels)  # pyright: ignore[reportUnknownMemberType]

        # Train receipt classifier
        receipt_texts, receipt_labels = zip(*receipt_data)
        self.receipt_classifier = Pipeline(
            [
                ("tfidf", TfidfVectorizer(stop_words="english", max_features=500)),
                ("classifier", MultinomialNB()),
            ],
        )
        self.receipt_classifier.fit(receipt_texts, receipt_labels)  # pyright: ignore[reportUnknownMemberType]

        # Train category classifier
        category_texts, category_labels = zip(*category_data)
        self.category_classifier = Pipeline(
            [
                ("tfidf", TfidfVectorizer(stop_words="english", max_features=800)),
                ("classifier", MultinomialNB()),
            ],
        )
        self.category_classifier.fit(category_texts, category_labels)  # pyright: ignore[reportUnknownMemberType]

        logger.info("✅ ML models initialized successfully")

    def _preprocess_email(self, email_content: str) -> str:
        """Preprocess email content for classification."""
        # Simple preprocessing - convert to lowercase and strip whitespace
        processed = email_content.lower().strip()
        return processed

    def detect_spam(self, email_content: str, threshold: float = 0.7) -> tuple[str, float]:
        """Detect if email is spam using ML model."""
        processed_text = self._preprocess_email(email_content)

        try:
            prediction = self.spam_classifier.predict([processed_text])[0]  # pyright: ignore[reportUnknownMemberType]
            probabilities = self.spam_classifier.predict_proba([processed_text])[0]  # pyright: ignore[reportUnknownMemberType]

            confidence = float(np.max(probabilities))
            return str(prediction), confidence
        except Exception as e:
            logger.error(f"Spam detection failed: {e}")
            return "error", 0.0

    def analyze_sentiment(self, email_content: str) -> tuple[str, float]:
        """Analyze email sentiment using keyword-based approach."""
        processed_text = self._preprocess_email(email_content)

        positive_words = ["good", "great", "excellent", "happy", "pleased", "thank", "wonderful"]
        negative_words = ["bad", "terrible", "poor", "unhappy", "disappointed", "sorry", "problem"]

        positive_count = sum(1 for word in positive_words if word in processed_text)
        negative_count = sum(1 for word in negative_words if word in processed_text)

        if positive_count > negative_count:
            return "positive", min(0.9, 0.6 + positive_count * 0.1)
        if negative_count > positive_count:
            return "negative", min(0.9, 0.6 + negative_count * 0.1)
        return "neutral", 0.6

    def classify_category(self, email_content: str) -> tuple[str, float]:
        """Classify email category using ML model."""
        processed_text = self._preprocess_email(email_content)

        try:
            prediction = self.category_classifier.predict([processed_text])[0]  # pyright: ignore[reportUnknownMemberType]
            probabilities = self.category_classifier.predict_proba([processed_text])[0]  # pyright: ignore[reportUnknownMemberType]

            confidence = float(np.max(probabilities))
            return str(prediction), confidence
        except Exception as e:
            logger.error(f"Category classification failed: {e}")
            return "unknown", 0.0

    def detect_bill(self, email_content: str) -> tuple[str, float]:
        """Detect if email is a bill using ML model."""
        processed_text = self._preprocess_email(email_content)

        try:
            prediction = self.bill_classifier.predict([processed_text])[0]  # pyright: ignore[reportUnknownMemberType]
            probabilities = self.bill_classifier.predict_proba([processed_text])[0]  # pyright: ignore[reportUnknownMemberType]

            confidence = float(np.max(probabilities))
            return str(prediction), confidence
        except Exception as e:
            logger.error(f"Bill detection failed: {e}")
            return "error", 0.0

    def detect_receipt(self, email_content: str) -> tuple[str, float]:
        """Detect if email is a receipt using ML model."""
        processed_text = self._preprocess_email(email_content)

        try:
            prediction = self.receipt_classifier.predict([processed_text])[0]  # pyright: ignore[reportUnknownMemberType]
            probabilities = self.receipt_classifier.predict_proba([processed_text])[0]  # pyright: ignore[reportUnknownMemberType]

            confidence = float(np.max(probabilities))
            return str(prediction), confidence
        except Exception as e:
            logger.error(f"Receipt detection failed: {e}")
            return "error", 0.0

    def detect_language(self, email_content: str) -> tuple[str, float]:
        """Detect email language (simplified - English detection only)."""
        # Simplified language detection
        return "en", 0.95

    def classify_priority(self, email_content: str) -> tuple[str, float]:
        """Classify email priority using keyword-based approach."""
        processed_text = self._preprocess_email(email_content)

        high_priority_words = ["urgent", "immediate", "asap", "critical", "important"]
        medium_priority_words = ["soon", "reminder", "follow-up", "update"]

        high_count = sum(1 for word in high_priority_words if word in processed_text)
        medium_count = sum(1 for word in medium_priority_words if word in processed_text)

        if high_count > 0:
            return "high", min(0.9, 0.7 + high_count * 0.1)
        if medium_count > 0:
            return "medium", min(0.8, 0.6 + medium_count * 0.1)
        return "low", 0.6


# ============================================================================
# WORKER APPLICATION
# ============================================================================


class EmailClassifierWorker(WorkerApplication):
    """Email classification worker using ML models.
    
    Provides multiple classification types:
    - Spam detection (TF-IDF + Naive Bayes)
    - Bill/receipt detection (TF-IDF + Naive Bayes)
    - Sentiment analysis (keyword-based)
    - Category classification (TF-IDF + Naive Bayes)
    - Priority classification (keyword-based)
    - Language detection (simplified)
    
    All infrastructure (registration, heartbeat, health checks, certificates)
    is handled by the WorkerApplication base class.
    """

    def __init__(self) -> None:
        """Initialize email classifier worker."""
        super().__init__(
            service_name="crank-email-classifier",
            https_port=int(os.getenv("EMAIL_CLASSIFIER_HTTPS_PORT", "8201")),
        )
        
        # Initialize ML engine (business logic)
        self.classifier = SimpleEmailClassifier()

    def get_capabilities(self) -> list[CapabilityDefinition]:
        """Return worker capabilities."""
        return [EMAIL_CLASSIFICATION]

    def setup_routes(self) -> None:
        """Set up email classification routes.
        
        IMPORTANT: Use explicit binding pattern self.app.METHOD("/path")(handler)
        instead of @self.app.METHOD decorators to avoid Pylance "not accessed" warnings.
        
        Pattern documented in:
        - src/crank/worker_runtime/base.py (lines 11-13, 187-192)
        - .vscode/AGENT_CONTEXT.md (FastAPI Route Handler Pattern section)
        """

        # Classification endpoint - accepts Form data (used by tests/pipeline)
        async def classify_email(
            email_content: str = Form(...),
            classification_types: str = Form(
                default="spam_detection,bill_detection,receipt_detection",
                description="Comma-separated list of classification types",
            ),
        ) -> ClassificationResponse:
            """Classify email content using ML models."""
            try:
                # Parse classification types
                types = [t.strip() for t in classification_types.split(",")]

                # Generate email ID
                email_id = f"email-{uuid4().hex[:8]}"

                # Perform classifications
                results: list[EmailClassificationResult] = []

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
                                details={"algorithm": "simple"},
                            ),
                        )

                return ClassificationResponse(
                    success=True,
                    email_id=email_id,
                    results=results,
                    metadata={
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "email_length": len(email_content),
                        "classification_count": len(results),
                    },
                )

            except Exception as e:
                logger.exception(f"Classification failed: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        # Explicit binding pattern
        self.app.post("/classify", response_model=ClassificationResponse)(classify_email)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    """Main entry point - creates and runs email classifier worker."""
    worker = EmailClassifierWorker()
    worker.run()


if __name__ == "__main__":
    main()
