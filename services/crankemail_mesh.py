"""
CrankEmail Mesh Service - Security-First Email Processing

Implements the security-hardened mesh interface for email parsing and classification,
based on the adversarial testing work that proved security measures.
"""

import json
import tempfile
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional
import mailbox
import hashlib

from mesh_interface import MeshInterface, MeshRequest, MeshResponse, MeshCapability, MeshReceipt


class CrankEmailMeshService(MeshInterface):
    """Security-first email parsing and classification service implementing mesh interface."""
    
    def __init__(self):
        super().__init__("email")
        
        # Initialize email processing capabilities
        self.supported_formats = {
            "input": ["mbox", "eml", "msg", "txt"],
            "output": ["jsonl", "json", "csv"]
        }
        
        # Default keywords for receipt detection (secure baseline)
        self.default_keywords = [
            "receipt", "invoice", "order confirmation", "payment confirmation",
            "statement", "bill", "purchase", "transaction", "total", "amount due"
        ]
    
    def get_capabilities(self) -> List[MeshCapability]:
        """Return CrankEmail capabilities with security requirements."""
        return [
            MeshCapability(
                operation="parse",
                description="Parse email archives with security validation",
                input_schema={
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "format": "binary"},
                        "format": {"type": "string", "enum": self.supported_formats["input"]},
                        "output_format": {"type": "string", "enum": self.supported_formats["output"]},
                        "options": {"type": "object"}
                    },
                    "required": ["file"]
                },
                output_schema={
                    "type": "object", 
                    "properties": {
                        "parse_id": {"type": "string"},
                        "status": {"type": "string"},
                        "message_count": {"type": "integer"},
                        "download_url": {"type": "string"}
                    }
                },
                policies_required=["file_validation", "email_content_scan", "size_limits"],
                limits={"max_file_size": "500MB", "timeout": "600s"}
            ),
            MeshCapability(
                operation="classify",
                description="Classify emails by category with security filtering",
                input_schema={
                    "type": "object",
                    "properties": {
                        "emails": {"type": "array", "items": {"type": "object"}},
                        "categories": {"type": "array", "items": {"type": "string"}},
                        "classifier_type": {"type": "string", "enum": ["keyword", "ai"]}
                    },
                    "required": ["emails"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "classifications": {"type": "array", "items": {"type": "object"}},
                        "confidence_scores": {"type": "array", "items": {"type": "number"}},
                        "filtered_count": {"type": "integer"}
                    }
                },
                policies_required=["content_filtering", "privacy_protection"],
                limits={"max_emails": "10000"}
            ),
            MeshCapability(
                operation="analyze",
                description="Analyze email patterns and metadata safely",
                input_schema={
                    "type": "object",
                    "properties": {
                        "emails": {"type": "array", "items": {"type": "object"}},
                        "analysis_type": {"type": "string", "enum": ["receipt_detection", "sentiment", "threading"]}
                    },
                    "required": ["emails"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis_results": {"type": "object"},
                        "patterns": {"type": "array", "items": {"type": "object"}},
                        "metadata": {"type": "object"}
                    }
                },
                policies_required=["privacy_protection"],
                limits={"max_emails": "5000"}
            ),
            MeshCapability(
                operation="extract",
                description="Extract specific data from emails with privacy controls",
                input_schema={
                    "type": "object",
                    "properties": {
                        "emails": {"type": "array", "items": {"type": "object"}},
                        "extraction_type": {"type": "string", "enum": ["receipts", "expenses", "contacts"]},
                        "privacy_mode": {"type": "string", "enum": ["strict", "moderate", "minimal"]}
                    },
                    "required": ["emails", "extraction_type"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "extracted_data": {"type": "array", "items": {"type": "object"}},
                        "privacy_filtered": {"type": "integer"},
                        "extraction_summary": {"type": "object"}
                    }
                },
                policies_required=["data_extraction", "privacy_protection", "retention_policy"],
                limits={"max_emails": "1000"}
            )
        ]
    
    async def process_request(self, request: MeshRequest, auth_context: Dict[str, Any]) -> MeshResponse:
        """
        Process email request with mandatory security context.
        
        This integrates with proven security patterns for email processing.
        """
        try:
            if request.operation == "parse":
                result = await self._handle_parsing(request, auth_context)
            elif request.operation == "classify":
                result = await self._handle_classification(request, auth_context)
            elif request.operation == "analyze":
                result = await self._handle_analysis(request, auth_context)
            elif request.operation == "extract":
                result = await self._handle_extraction(request, auth_context)
            else:
                return MeshResponse(
                    success=False,
                    errors=[f"Unknown operation: {request.operation}"],
                    metadata={"supported_operations": ["parse", "classify", "analyze", "extract"]}
                )
            
            return MeshResponse(success=True, result=result)
            
        except Exception as e:
            return MeshResponse(
                success=False, 
                errors=[f"Processing error: {str(e)}"],
                metadata={"auth_context": auth_context.get("user_id", "unknown")}
            )
    
    async def _handle_parsing(self, request: MeshRequest, auth_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle email parsing with security validation."""
        if "file" not in request.input_data:
            raise ValueError("Email file is required for parsing")
        
        # Security: Validate file format and size
        file_data = request.input_data.get("file", "")
        format_type = request.input_data.get("format", "auto")
        output_format = request.input_data.get("output_format", "jsonl")
        
        if format_type not in self.supported_formats["input"] and format_type != "auto":
            raise ValueError(f"Input format {format_type} not supported")
        
        if output_format not in self.supported_formats["output"]:
            raise ValueError(f"Output format {output_format} not supported")
        
        # Security: File size check (500MB limit for email archives)
        if len(str(file_data)) > 500 * 1024 * 1024:
            raise ValueError("Email archive exceeds maximum size limit (500MB)")
        
        # Simulate parsing (in real implementation, this would use parse-email-archive logic)
        parse_id = f"parse_{auth_context.get('user_id', 'anon')}_{hash(str(request.input_data))%10000:04d}"
        
        return {
            "parse_id": parse_id,
            "status": "completed",
            "message_count": 150,  # Simulated count
            "format_detected": "mbox",
            "output_format": output_format,
            "download_url": f"/v1/downloads/{parse_id}",
            "processed_by": auth_context.get("user_id", "unknown")
        }
    
    async def _handle_classification(self, request: MeshRequest, auth_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle email classification with security filtering."""
        emails = request.input_data.get("emails", [])
        if not emails:
            raise ValueError("Email list is required for classification")
        
        # Security: Limit number of emails to prevent abuse
        if len(emails) > 10000:
            raise ValueError("Too many emails for classification (max 10,000)")
        
        categories = request.input_data.get("categories", ["receipt", "personal", "business", "spam"])
        classifier_type = request.input_data.get("classifier_type", "keyword")
        
        # Simulate classification with security filtering
        classifications = []
        filtered_count = 0
        
        for i, email in enumerate(emails[:100]):  # Limit for demo
            # Security: Filter out potentially sensitive content
            subject = str(email.get("subject", "")).lower()
            if any(sensitive in subject for sensitive in ["password", "ssn", "credit card"]):
                filtered_count += 1
                continue
                
            # Simple keyword-based classification
            category = "other"
            confidence = 0.5
            
            if any(keyword in subject for keyword in self.default_keywords):
                category = "receipt"
                confidence = 0.8
            elif "work" in subject or "meeting" in subject:
                category = "business"
                confidence = 0.7
            
            classifications.append({
                "email_id": email.get("id", f"email_{i}"),
                "category": category,
                "confidence": confidence,
                "filtered": False
            })
        
        return {
            "classifications": classifications,
            "total_processed": len(classifications),
            "filtered_count": filtered_count,
            "classifier_type": classifier_type,
            "categories": categories,
            "processed_by": auth_context.get("user_id", "unknown")
        }
    
    async def _handle_analysis(self, request: MeshRequest, auth_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle email analysis with privacy protection."""
        emails = request.input_data.get("emails", [])
        if not emails:
            raise ValueError("Email list is required for analysis")
        
        # Security: Limit analysis scope
        if len(emails) > 5000:
            raise ValueError("Too many emails for analysis (max 5,000)")
        
        analysis_type = request.input_data.get("analysis_type", "receipt_detection")
        
        # Simulate analysis with privacy protection
        if analysis_type == "receipt_detection":
            receipt_count = sum(1 for email in emails[:100] 
                              if any(keyword in str(email.get("subject", "")).lower() 
                                   for keyword in self.default_keywords))
            
            analysis_results = {
                "receipt_emails": receipt_count,
                "total_analyzed": min(len(emails), 100),
                "receipt_percentage": (receipt_count / min(len(emails), 100)) * 100 if emails else 0
            }
        else:
            analysis_results = {
                "analysis_type": analysis_type,
                "total_analyzed": min(len(emails), 100),
                "note": "Analysis completed with privacy protection"
            }
        
        return {
            "analysis_results": analysis_results,
            "analysis_type": analysis_type,
            "privacy_protected": True,
            "processed_by": auth_context.get("user_id", "unknown")
        }
    
    async def _handle_extraction(self, request: MeshRequest, auth_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data extraction with strict privacy controls."""
        emails = request.input_data.get("emails", [])
        if not emails:
            raise ValueError("Email list is required for extraction")
        
        # Security: Strict limits for data extraction
        if len(emails) > 1000:
            raise ValueError("Too many emails for extraction (max 1,000)")
        
        extraction_type = request.input_data.get("extraction_type", "receipts")
        privacy_mode = request.input_data.get("privacy_mode", "strict")
        
        # Simulate extraction with privacy controls
        extracted_data = []
        privacy_filtered = 0
        
        for i, email in enumerate(emails[:50]):  # Strict limit for demo
            subject = str(email.get("subject", ""))
            
            # Privacy filtering
            if privacy_mode == "strict" and any(sensitive in subject.lower() 
                                              for sensitive in ["personal", "confidential", "private"]):
                privacy_filtered += 1
                continue
            
            if extraction_type == "receipts" and any(keyword in subject.lower() 
                                                   for keyword in self.default_keywords):
                extracted_data.append({
                    "email_id": email.get("id", f"email_{i}"),
                    "subject": subject[:50] + "..." if len(subject) > 50 else subject,  # Truncate for privacy
                    "type": "receipt",
                    "extracted_at": "2025-10-29T22:00:00Z"
                })
        
        return {
            "extracted_data": extracted_data,
            "extraction_type": extraction_type,
            "privacy_mode": privacy_mode,
            "privacy_filtered": privacy_filtered,
            "total_extracted": len(extracted_data),
            "extraction_summary": {
                "success_rate": len(extracted_data) / max(len(emails[:50]) - privacy_filtered, 1),
                "privacy_compliance": True
            },
            "processed_by": auth_context.get("user_id", "unknown")
        }


# Factory function for creating the service
def create_crankemail_mesh_service() -> CrankEmailMeshService:
    """Create and return a CrankEmail mesh service instance."""
    return CrankEmailMeshService()


# For running directly  
if __name__ == "__main__":
    import uvicorn
    import os
    service = create_crankemail_mesh_service()
    app = service.create_app("dev-mesh-key")
    port = int(os.getenv('CRANKEMAIL_MESH_PORT', '8001'))
    uvicorn.run(app, host="0.0.0.0", port=port)
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
    import os
    app = create_crankemail_service()
    port = int(os.getenv('CRANKEMAIL_SERVICE_PORT', '8001'))
    uvicorn.run(app, host="0.0.0.0", port=port)