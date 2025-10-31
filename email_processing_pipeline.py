"""
Email Processing Pipeline Architecture

This demonstrates how to chain the email parser (batch processor) with 
ML classifiers (transactional processors) for comprehensive email analysis.

Pipeline Flow:
1. Email Parser: mbox/eml → JSON metadata (bulk)
2. ML Classifier: JSON → Classifications (per-email)
3. Results Aggregator: Classifications → Summary reports

This pattern separates concerns:
- Parser: Data extraction and normalization
- Classifier: Intelligence and prediction
- Aggregator: Business logic and reporting
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailProcessingPipeline:
    """Orchestrates email processing through multiple worker stages."""
    
    def __init__(self):
        self.parser_url = "http://localhost:8009"  # Email parser worker
        self.classifier_url = "http://localhost:8003"  # Email classifier worker
        
    async def process_email_archive(
        self, 
        mbox_file_path: str,
        classification_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Process an entire email archive through the pipeline.
        
        Args:
            mbox_file_path: Path to mbox file
            classification_types: Types of classification to perform
            
        Returns:
            Comprehensive analysis results
        """
        if classification_types is None:
            classification_types = ["spam_detection", "bill_detection", "receipt_detection"]
            
        # Stage 1: Parse emails to JSON
        logger.info("🔄 Stage 1: Parsing email archive...")
        parsed_emails = await self._parse_emails(mbox_file_path)
        
        # Stage 2: Classify each email
        logger.info("🤖 Stage 2: Running ML classification...")
        classified_emails = await self._classify_emails(
            parsed_emails["messages"], 
            classification_types
        )
        
        # Stage 3: Aggregate and analyze results
        logger.info("📊 Stage 3: Generating insights...")
        pipeline_results = await self._generate_pipeline_insights(
            parsed_emails, 
            classified_emails
        )
        
        return pipeline_results
        
    async def _parse_emails(self, mbox_file_path: str) -> Dict[str, Any]:
        """Stage 1: Parse mbox file to structured JSON."""
        async with httpx.AsyncClient() as client:
            with open(mbox_file_path, 'rb') as f:
                files = {"file": f}
                data = {
                    "request_data": json.dumps({
                        "keywords": [],  # Don't use keywords for classification
                        "snippet_length": 500,  # More content for ML
                        "max_messages": 1000  # Process more emails
                    })
                }
                
                response = await client.post(
                    f"{self.parser_url}/parse/mbox",
                    files=files,
                    data=data
                )
                
        return response.json()
    
    async def _classify_emails(
        self, 
        emails: List[Dict[str, Any]], 
        classification_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Stage 2: Apply ML classification to each email."""
        classified_results = []
        
        async with httpx.AsyncClient() as client:
            for email in emails:
                # Prepare email content for classification
                email_content = self._prepare_email_for_classification(email)
                
                try:
                    response = await client.post(
                        f"{self.classifier_url}/classify",
                        json={
                            "email_content": email_content,
                            "classification_types": classification_types,
                            "confidence_threshold": 0.6
                        }
                    )
                    
                    classification_result = response.json()
                    
                    # Combine original email data with classification
                    classified_email = {
                        **email,  # Original parsed data
                        "ml_classifications": classification_result.get("results", []),
                        "classification_metadata": classification_result.get("metadata", {})
                    }
                    
                    classified_results.append(classified_email)
                    
                except Exception as e:
                    logger.warning(f"Classification failed for email {email.get('message_id', 'unknown')}: {e}")
                    # Include email anyway with failed classification
                    classified_results.append({
                        **email,
                        "ml_classifications": [],
                        "classification_error": str(e)
                    })
                    
        return classified_results
    
    def _prepare_email_for_classification(self, email: Dict[str, Any]) -> str:
        """Prepare email data for ML classification."""
        # Combine relevant fields for classification
        parts = []
        
        if email.get("subject"):
            parts.append(f"Subject: {email['subject']}")
            
        if email.get("from"):
            parts.append(f"From: {email['from']}")
            
        if email.get("body_snippet"):
            parts.append(f"Body: {email['body_snippet']}")
            
        return "\n".join(parts)
    
    async def _generate_pipeline_insights(
        self, 
        parsed_data: Dict[str, Any], 
        classified_emails: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Stage 3: Generate comprehensive insights from pipeline results."""
        
        # Calculate classification statistics
        classification_stats = {}
        for classification_type in ["spam_detection", "bill_detection", "receipt_detection"]:
            stats = self._calculate_classification_stats(classified_emails, classification_type)
            classification_stats[classification_type] = stats
        
        # Enhanced insights combining parser + classifier
        insights = {
            "pipeline_summary": {
                "total_emails_processed": len(classified_emails),
                "processing_stages_completed": 3,
                "pipeline_success_rate": self._calculate_success_rate(classified_emails),
                "processed_at": datetime.now().isoformat()
            },
            
            "parsing_results": {
                "total_messages": parsed_data.get("message_count", 0),
                "processing_time_ms": parsed_data.get("processing_time_ms", 0),
                "original_summary": parsed_data.get("summary", {})
            },
            
            "ml_classification_results": classification_stats,
            
            "enhanced_insights": {
                "likely_bills": [
                    email for email in classified_emails 
                    if self._is_likely_bill(email)
                ],
                "high_priority_emails": [
                    email for email in classified_emails
                    if self._is_high_priority(email)
                ],
                "suspicious_emails": [
                    email for email in classified_emails
                    if self._is_suspicious(email)
                ]
            },
            
            "recommendations": self._generate_recommendations(classified_emails)
        }
        
        return insights
    
    def _calculate_classification_stats(
        self, 
        emails: List[Dict[str, Any]], 
        classification_type: str
    ) -> Dict[str, Any]:
        """Calculate statistics for a specific classification type."""
        relevant_classifications = []
        
        for email in emails:
            for classification in email.get("ml_classifications", []):
                if classification.get("classification_type") == classification_type:
                    relevant_classifications.append(classification)
        
        if not relevant_classifications:
            return {"count": 0, "average_confidence": 0, "predictions": {}}
        
        # Calculate stats
        predictions = {}
        total_confidence = 0
        
        for classification in relevant_classifications:
            prediction = classification.get("prediction", "unknown")
            confidence = classification.get("confidence", 0)
            
            if prediction not in predictions:
                predictions[prediction] = {"count": 0, "total_confidence": 0}
            
            predictions[prediction]["count"] += 1
            predictions[prediction]["total_confidence"] += confidence
            total_confidence += confidence
        
        # Calculate averages
        for prediction in predictions:
            pred_data = predictions[prediction]
            pred_data["average_confidence"] = pred_data["total_confidence"] / pred_data["count"]
        
        return {
            "count": len(relevant_classifications),
            "average_confidence": total_confidence / len(relevant_classifications),
            "predictions": predictions
        }
    
    def _calculate_success_rate(self, emails: List[Dict[str, Any]]) -> float:
        """Calculate pipeline success rate."""
        successful = sum(1 for email in emails if not email.get("classification_error"))
        return (successful / len(emails)) * 100 if emails else 0
    
    def _is_likely_bill(self, email: Dict[str, Any]) -> bool:
        """Determine if email is likely a bill based on ML classifications."""
        for classification in email.get("ml_classifications", []):
            if (classification.get("classification_type") == "bill_detection" and 
                classification.get("prediction") == "bill" and
                classification.get("confidence", 0) > 0.7):
                return True
        return False
    
    def _is_high_priority(self, email: Dict[str, Any]) -> bool:
        """Determine if email is high priority."""
        # High priority if multiple positive classifications
        positive_classifications = 0
        for classification in email.get("ml_classifications", []):
            if classification.get("confidence", 0) > 0.8:
                positive_classifications += 1
        return positive_classifications >= 2
    
    def _is_suspicious(self, email: Dict[str, Any]) -> bool:
        """Determine if email is suspicious."""
        for classification in email.get("ml_classifications", []):
            if (classification.get("classification_type") == "spam_detection" and 
                classification.get("prediction") == "spam" and
                classification.get("confidence", 0) > 0.8):
                return True
        return False
    
    def _generate_recommendations(self, emails: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        bill_count = sum(1 for email in emails if self._is_likely_bill(email))
        spam_count = sum(1 for email in emails if self._is_suspicious(email))
        
        if bill_count > 0:
            recommendations.append(f"Found {bill_count} potential bills that may need attention")
        
        if spam_count > len(emails) * 0.3:  # More than 30% spam
            recommendations.append("High spam rate detected - consider improving email filters")
        
        if len(emails) > 1000:
            recommendations.append("Large email archive - consider automated processing workflows")
        
        return recommendations


# Example usage function
async def example_pipeline_usage():
    """Example of how to use the email processing pipeline."""
    pipeline = EmailProcessingPipeline()
    
    # Process an email archive
    results = await pipeline.process_email_archive(
        "/path/to/sample.mbox",
        classification_types=["spam_detection", "bill_detection", "receipt_detection"]
    )
    
    print("📊 Pipeline Results:")
    print(f"Total emails: {results['pipeline_summary']['total_emails_processed']}")
    print(f"Success rate: {results['pipeline_summary']['pipeline_success_rate']:.1f}%")
    print(f"Likely bills found: {len(results['enhanced_insights']['likely_bills'])}")
    print(f"Suspicious emails: {len(results['enhanced_insights']['suspicious_emails'])}")
    
    for recommendation in results['recommendations']:
        print(f"💡 {recommendation}")


if __name__ == "__main__":
    asyncio.run(example_pipeline_usage())