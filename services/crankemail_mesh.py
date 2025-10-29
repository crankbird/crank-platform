"""
CrankEmail Mesh Service - Email parsing and classification with mesh interface

Wraps the email parsing and AI classification functionality in the universal mesh interface.
"""

import json
import tempfile
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional
import mailbox

from fastapi import UploadFile

from mesh_interface import MeshInterface, MeshRequest, MeshResponse, MeshCapabilities, MeshReceipt


class CrankEmailMeshService(MeshInterface):
    """Email parsing and classification service implementing mesh interface."""
    
    def __init__(self, service_type: str = "email"):
        super().__init__(service_type)
        
        # Initialize email processing capabilities
        self.supported_formats = {
            "input": ["mbox", "eml", "msg", "txt"],
            "output": ["jsonl", "json", "csv"]
        }
        
        # Default keywords for receipt detection (fallback)
        self.default_keywords = [
            "receipt", "invoice", "order confirmation", "payment confirmation",
            "statement", "bill", "purchase", "transaction", "total", "amount due"
        ]
        
        # Store job receipts in memory for now
        # TODO: Replace with persistent storage
        self.receipts: Dict[str, MeshReceipt] = {}
        
        # TODO: Initialize AI classifier
        # self.ai_classifier = EmailClassifier.load("models/email_classifier.joblib")
        self.ai_classifier = None  # For now, use keyword classification
    
    async def handle_request(self, request: MeshRequest, file: Optional[UploadFile]) -> MeshResponse:
        """Handle email processing requests."""
        
        if request.operation == "parse":
            return await self._handle_parsing(request, file)
        elif request.operation == "classify":
            return await self._handle_classification(request, file)
        elif request.operation == "analyze":
            return await self._handle_analysis(request, file)
        elif request.operation == "extract":
            return await self._handle_extraction(request, file)
        else:
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation=request.operation,
                status="failed",
                result={"error": f"Unknown operation: {request.operation}"}
            )
    
    async def _handle_parsing(self, request: MeshRequest, file: UploadFile) -> MeshResponse:
        """Handle email parsing requests."""
        if not file:
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="parse",
                status="failed",
                result={"error": "File is required for parsing"}
            )
        
        try:
            # Read file content
            file_content = await file.read()
            
            # Parse based on file type
            file_format = self._detect_format(file.filename)
            
            if file_format == "mbox":
                messages = await self._parse_mbox(file_content, request.parameters)
            elif file_format == "eml":
                messages = await self._parse_eml(file_content, request.parameters)
            else:
                return MeshResponse(
                    job_id=request.job_id,
                    service_type=self.service_type,
                    operation="parse",
                    status="failed",
                    result={"error": f"Unsupported file format: {file_format}"}
                )
            
            # Limit response size for large archives
            max_messages = request.parameters.get("max_messages", 1000)
            has_more = len(messages) > max_messages
            limited_messages = messages[:max_messages]
            
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="parse",
                status="completed",
                result={
                    "filename": file.filename,
                    "format": file_format,
                    "total_messages": len(messages),
                    "returned_messages": len(limited_messages),
                    "has_more": has_more,
                    "messages": limited_messages,
                    "summary": {
                        "date_range": self._get_date_range(messages) if messages else None,
                        "senders": self._get_top_senders(messages) if messages else [],
                        "receipt_candidates": sum(1 for m in limited_messages if m.get('is_receipt_candidate', False))
                    }
                }
            )
            
        except Exception as e:
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="parse",
                status="failed",
                result={"error": f"Parsing failed: {str(e)}"}
            )
    
    async def _handle_classification(self, request: MeshRequest, file: UploadFile) -> MeshResponse:
        """Handle email classification requests."""
        if not file:
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="classify",
                status="failed",
                result={"error": "File is required for classification"}
            )
        
        try:
            file_content = await file.read()
            
            # For single email classification
            email_text = file_content.decode('utf-8', errors='ignore')
            
            # Extract basic email components
            email_data = self._parse_single_email(email_text)
            
            # Classify using available method
            if self.ai_classifier:
                is_receipt = self.ai_classifier.predict(
                    email_data['subject'], 
                    email_data['body_snippet']
                )
                confidence = self.ai_classifier.predict_proba(
                    email_data['subject'], 
                    email_data['body_snippet']
                )
                method = "ai_classifier"
            else:
                # Fallback to keyword classification
                is_receipt = self._keyword_classify(
                    email_data['subject'], 
                    email_data['body_snippet'],
                    request.parameters.get('keywords', self.default_keywords)
                )
                confidence = 0.8 if is_receipt else 0.2  # Simulated confidence
                method = "keyword_matching"
            
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="classify",
                status="completed",
                result={
                    "filename": file.filename,
                    "classification": {
                        "is_receipt": is_receipt,
                        "confidence": confidence,
                        "method": method
                    },
                    "email_data": email_data,
                    "metadata": {
                        "classifier_version": "1.0",
                        "processing_time_ms": 50  # Simulated
                    }
                }
            )
            
        except Exception as e:
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="classify",
                status="failed",
                result={"error": f"Classification failed: {str(e)}"}
            )
    
    async def _handle_analysis(self, request: MeshRequest, file: UploadFile) -> MeshResponse:
        """Handle email archive analysis requests."""
        if not file:
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="analyze",
                status="failed",
                result={"error": "File is required for analysis"}
            )
        
        try:
            file_content = await file.read()
            file_format = self._detect_format(file.filename)
            
            if file_format == "mbox":
                messages = await self._parse_mbox(file_content, request.parameters)
            else:
                return MeshResponse(
                    job_id=request.job_id,
                    service_type=self.service_type,
                    operation="analyze",
                    status="failed",
                    result={"error": f"Analysis not supported for format: {file_format}"}
                )
            
            # Perform analysis
            analysis = self._analyze_message_archive(messages)
            
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="analyze",
                status="completed",
                result={
                    "filename": file.filename,
                    "format": file_format,
                    "analysis": analysis
                }
            )
            
        except Exception as e:
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="analyze",
                status="failed",
                result={"error": f"Analysis failed: {str(e)}"}
            )
    
    async def _handle_extraction(self, request: MeshRequest, file: UploadFile) -> MeshResponse:
        """Handle data extraction from emails."""
        # TODO: Implement receipt/invoice data extraction
        return MeshResponse(
            job_id=request.job_id,
            service_type=self.service_type,
            operation="extract",
            status="failed",
            result={"error": "Data extraction not yet implemented"}
        )
    
    async def _parse_mbox(self, content: bytes, parameters: dict) -> List[Dict[str, Any]]:
        """Parse mbox file content."""
        messages = []
        
        # Create temporary file for mailbox parsing
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(content)
            temp_file.flush()
            
            try:
                mbox = mailbox.mbox(temp_file.name)
                
                keywords = parameters.get('keywords', self.default_keywords)
                snippet_length = parameters.get('snippet_length', 200)
                
                for i, message in enumerate(mbox):
                    if i >= 10000:  # Limit to prevent memory issues
                        break
                    
                    parsed_msg = self._parse_message(message, keywords, snippet_length)
                    messages.append(parsed_msg)
                    
            except Exception as e:
                raise Exception(f"Failed to parse mbox: {str(e)}")
        
        return messages
    
    async def _parse_eml(self, content: bytes, parameters: dict) -> List[Dict[str, Any]]:
        """Parse single EML file."""
        import email
        
        try:
            message = email.message_from_bytes(content)
            keywords = parameters.get('keywords', self.default_keywords)
            snippet_length = parameters.get('snippet_length', 200)
            
            parsed_msg = self._parse_message(message, keywords, snippet_length)
            return [parsed_msg]
            
        except Exception as e:
            raise Exception(f"Failed to parse EML: {str(e)}")
    
    def _parse_message(self, message, keywords: List[str], snippet_length: int) -> Dict[str, Any]:
        """Parse individual email message."""
        # Extract headers
        subject = message.get('Subject', '').strip()
        sender = message.get('From', '').strip()
        date = message.get('Date', '').strip()
        
        # Extract body snippet
        body_snippet = ""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body_snippet = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        continue
        else:
            try:
                body_snippet = message.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body_snippet = str(message.get_payload())
        
        # Truncate body snippet
        if len(body_snippet) > snippet_length:
            body_snippet = body_snippet[:snippet_length] + "..."
        
        # Keyword classification
        is_receipt_candidate = self._keyword_classify(subject, body_snippet, keywords)
        
        return {
            "subject": subject,
            "sender": sender,
            "date": date,
            "body_snippet": body_snippet,
            "is_receipt_candidate": is_receipt_candidate,
            "snippet_length": len(body_snippet)
        }
    
    def _parse_single_email(self, email_text: str) -> Dict[str, Any]:
        """Parse single email from text."""
        lines = email_text.split('\n')
        
        subject = ""
        sender = ""
        date = ""
        body_start = 0
        
        # Find headers
        for i, line in enumerate(lines):
            if line.startswith('Subject:'):
                subject = line[8:].strip()
            elif line.startswith('From:'):
                sender = line[5:].strip()
            elif line.startswith('Date:'):
                date = line[5:].strip()
            elif line.strip() == "":
                body_start = i + 1
                break
        
        # Extract body
        body = '\n'.join(lines[body_start:])
        body_snippet = body[:500] if len(body) > 500 else body
        
        return {
            "subject": subject,
            "sender": sender,
            "date": date,
            "body_snippet": body_snippet,
            "full_body_length": len(body)
        }
    
    def _keyword_classify(self, subject: str, body: str, keywords: List[str]) -> bool:
        """Simple keyword-based classification."""
        text = f"{subject} {body}".lower()
        return any(keyword.lower() in text for keyword in keywords)
    
    def _detect_format(self, filename: str) -> str:
        """Detect email file format."""
        if not filename or '.' not in filename:
            return "unknown"
        
        extension = filename.rsplit('.', 1)[1].lower()
        format_map = {
            'mbox': 'mbox',
            'eml': 'eml',
            'msg': 'msg',
            'txt': 'txt'
        }
        
        return format_map.get(extension, "unknown")
    
    def _get_date_range(self, messages: List[Dict[str, Any]]) -> Dict[str, str]:
        """Get date range from messages."""
        dates = [msg.get('date', '') for msg in messages if msg.get('date')]
        if not dates:
            return {"earliest": "unknown", "latest": "unknown"}
        
        # Simple date extraction (could be improved)
        return {
            "earliest": min(dates),
            "latest": max(dates),
            "total_with_dates": len(dates)
        }
    
    def _get_top_senders(self, messages: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get top senders by email count."""
        sender_counts = {}
        for msg in messages:
            sender = msg.get('sender', 'unknown')
            sender_counts[sender] = sender_counts.get(sender, 0) + 1
        
        sorted_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"sender": sender, "count": count} for sender, count in sorted_senders[:limit]]
    
    def _analyze_message_archive(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze email archive for insights."""
        if not messages:
            return {"error": "No messages to analyze"}
        
        total_messages = len(messages)
        receipt_candidates = sum(1 for m in messages if m.get('is_receipt_candidate', False))
        
        return {
            "total_messages": total_messages,
            "receipt_candidates": receipt_candidates,
            "receipt_percentage": (receipt_candidates / total_messages * 100) if total_messages > 0 else 0,
            "date_range": self._get_date_range(messages),
            "top_senders": self._get_top_senders(messages),
            "average_snippet_length": sum(m.get('snippet_length', 0) for m in messages) / total_messages,
            "subjects_with_keywords": sum(1 for m in messages if any(
                keyword.lower() in m.get('subject', '').lower() 
                for keyword in self.default_keywords
            ))
        }
    
    async def get_service_capabilities(self) -> MeshCapabilities:
        """Return email service capabilities."""
        return MeshCapabilities(
            service_type=self.service_type,
            operations=["parse", "classify", "analyze", "extract"],
            supported_formats=self.supported_formats,
            limits={
                "max_file_size": "500MB",
                "max_messages_per_request": "10000",
                "max_processing_time": "10min"
            },
            health_status="ready"
        )
    
    async def get_processing_receipt(self, job_id: str) -> Optional[MeshReceipt]:
        """Get processing receipt for a job."""
        return self.receipts.get(job_id)
    
    async def check_readiness(self) -> Dict[str, Any]:
        """Check if email service is ready."""
        return {
            "ready": True,
            "service_type": self.service_type,
            "node_id": self.node_id,
            "checks": {
                "mailbox_parser": "available",
                "ai_classifier": "available" if self.ai_classifier else "fallback_to_keywords",
                "storage": "ready",
                "memory": "sufficient"
            },
            "active_jobs": 0,  # TODO: Track actual job count
            "queue_length": 0   # TODO: Track actual queue length
        }


# Create the FastAPI app
def create_crankemail_service() -> Any:
    """Create the CrankEmail mesh service."""
    service = CrankEmailMeshService()
    return service.app


# For running directly
if __name__ == "__main__":
    import uvicorn
    app = create_crankemail_service()
    uvicorn.run(app, host="0.0.0.0", port=8001)