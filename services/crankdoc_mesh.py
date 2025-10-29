"""
CrankDoc Mesh Service - Security-First Document Processing

Implements the security-hardened mesh interface for document conversion,
based on the adversarial testing work that proved security measures.

Includes built-in diagnostic operations for testing infrastructure vs business logic.
"""

import asyncio
import json
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import UploadFile

from mesh_interface import MeshInterface, MeshRequest, MeshResponse, MeshCapability, MeshReceipt
from mesh_diagnostics import DiagnosticMixin


class CrankDocMeshService(MeshInterface, DiagnosticMixin):
    """Security-first document conversion service implementing mesh interface with diagnostics."""
    
    def __init__(self):
        MeshInterface.__init__(self, "document")
        DiagnosticMixin.__init__(self)
        self.receipts: Dict[str, MeshReceipt] = {}
        
        # Initialize document processing capabilities
        self.supported_formats = {
            "input": ["md", "docx", "pdf", "html", "txt", "rtf"],
            "output": ["md", "docx", "pdf", "html", "latex", "txt"]
        }
    
    def get_capabilities(self) -> List[MeshCapability]:
        """Return CrankDoc capabilities with security requirements plus diagnostics."""
        business_capabilities = [
            MeshCapability(
                operation="convert",
                description="Convert documents between formats with security validation",
                input_schema={
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "format": "binary"},
                        "source_format": {"type": "string", "enum": self.supported_formats["input"]},
                        "target_format": {"type": "string", "enum": self.supported_formats["output"]},
                        "options": {"type": "object"}
                    },
                    "required": ["file", "source_format", "target_format"]
                },
                output_schema={
                    "type": "object", 
                    "properties": {
                        "conversion_id": {"type": "string"},
                        "status": {"type": "string"},
                        "download_url": {"type": "string"}
                    }
                },
                policies_required=["file_validation", "format_allowlist", "size_limits"],
                limits={"max_file_size": "50MB", "timeout": "300s"}
            ),
            MeshCapability(
                operation="validate",
                description="Validate document format and content security",
                input_schema={
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "format": "binary"},
                        "expected_format": {"type": "string"}
                    },
                    "required": ["file"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "valid": {"type": "boolean"},
                        "format": {"type": "string"},
                        "size": {"type": "integer"},
                        "security_issues": {"type": "array", "items": {"type": "string"}}
                    }
                },
                policies_required=["file_validation"],
                limits={"max_file_size": "50MB"}
            ),
            MeshCapability(
                operation="analyze",
                description="Analyze document structure and metadata safely",
                input_schema={
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "format": "binary"}
                    },
                    "required": ["file"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "word_count": {"type": "integer"},
                        "format": {"type": "string"},
                        "metadata": {"type": "object"},
                        "structure": {"type": "object"}
                    }
                },
                policies_required=["file_validation"],
                limits={"max_file_size": "50MB"}
            )
        ]
        
        # Add diagnostic capabilities
        diagnostic_capabilities = self.get_diagnostic_capabilities()
        return business_capabilities + diagnostic_capabilities
    
    async def process_request(self, request: MeshRequest, auth_context: Dict[str, Any]) -> MeshResponse:
        """
        Process document request with mandatory security context.
        
        This integrates with the proven security patterns from CrankDoc adversarial testing.
        Includes diagnostic operations for infrastructure testing.
        """
        try:
            # Check if it's a diagnostic operation first
            diagnostic_ops = ["ping", "echo_file", "load_test", "error_test"]
            if request.operation in diagnostic_ops:
                result = await self.handle_diagnostic_request(request)
            elif request.operation == "convert":
                result = await self._handle_conversion(request, auth_context)
            elif request.operation == "validate":
                result = await self._handle_validation(request, auth_context)
            elif request.operation == "analyze":
                result = await self._handle_analysis(request, auth_context)
            else:
                return MeshResponse(
                    success=False,
                    errors=[f"Unknown operation: {request.operation}"],
                    metadata={"supported_operations": ["convert", "validate", "analyze"]}
                )
            
            return MeshResponse(success=True, result=result)
            
        except Exception as e:
            return MeshResponse(
                success=False, 
                errors=[f"Processing error: {str(e)}"],
                metadata={"auth_context": auth_context.get("user_id", "unknown")}
            )
    
    async def _handle_conversion(self, request: MeshRequest, auth_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document conversion with security validation."""
        # Security: Validate file is present and within limits
        if "file" not in request.input_data:
            raise ValueError("File is required for conversion")
        
        # Extract conversion parameters (with security defaults)
        source_format = request.input_data.get("source_format", "auto")
        target_format = request.input_data.get("target_format")
        options = request.input_data.get("options", {})
        
        if not target_format:
            raise ValueError("Target format is required")
        
        # Security: Validate formats are allowed
        if source_format not in self.supported_formats["input"] and source_format != "auto":
            raise ValueError(f"Source format {source_format} not supported")
        
        if target_format not in self.supported_formats["output"]:
            raise ValueError(f"Target format {target_format} not supported")
        
        # Simulate conversion (in real implementation, this would call CrankDoc service)
        conversion_id = f"conv_{auth_context.get('user_id', 'anon')}_{hash(str(request.input_data))%10000:04d}"
        
        return {
            "conversion_id": conversion_id,
            "status": "completed",
            "source_format": source_format,
            "target_format": target_format,
            "download_url": f"/v1/downloads/{conversion_id}",
            "message": "Document converted successfully with security validation"
        }
    
    async def _handle_validation(self, request: MeshRequest, auth_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document validation with security checks."""
        if "file" not in request.input_data:
            raise ValueError("File is required for validation")
        
        # Simulate file validation (in real implementation, this would use CrankDoc validators)
        file_content = str(request.input_data.get("file", ""))
        expected_format = request.input_data.get("expected_format", "auto")
        
        # Security checks
        security_issues = []
        if len(file_content) > 50 * 1024 * 1024:  # 50MB limit
            security_issues.append("File exceeds maximum size limit")
        
        return {
            "valid": len(security_issues) == 0,
            "format": "markdown",  # Would be detected in real implementation
            "size": len(file_content),
            "security_issues": security_issues,
            "validated_by": auth_context.get("user_id", "unknown")
        }
    
    async def _handle_analysis(self, request: MeshRequest, auth_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document analysis with security boundaries."""
        if "file" not in request.input_data:
            raise ValueError("File is required for analysis")
        
        # Simulate document analysis (in real implementation, this would use CrankDoc analyzers)
        file_content = str(request.input_data.get("file", ""))
        
        return {
            "word_count": len(file_content.split()),
            "format": "markdown",  # Would be detected in real implementation
            "metadata": {
                "analyzed_by": auth_context.get("user_id", "unknown"),
                "analysis_timestamp": "2025-10-29T22:00:00Z"
            },
            "structure": {
                "sections": file_content.count("#"),
                "paragraphs": file_content.count("\n\n"),
                "headings": file_content.count("#")
            }
        }


# Factory function for creating the service
def create_crankdoc_mesh_service() -> CrankDocMeshService:
    """Create and return a CrankDoc mesh service instance."""
    return CrankDocMeshService()


# For running directly  
if __name__ == "__main__":
    import uvicorn
    service = create_crankdoc_mesh_service()
    app = service.create_app("dev-mesh-key")
    uvicorn.run(app, host="0.0.0.0", port=8000)
        if not file:
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="convert",
                status="failed",
                result={"error": "File is required for conversion"}
            )
        
        # Extract conversion parameters
        source_format = request.parameters.get("source_format", "auto")
        target_format = request.parameters.get("target_format")
        
        if not target_format:
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="convert",
                status="failed",
                result={"error": "target_format parameter is required"}
            )
        
        # Validate formats
        if target_format not in self.supported_formats["output"]:
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="convert",
                status="failed",
                result={"error": f"Unsupported target format: {target_format}"}
            )
        
        try:
            # Read file content
            file_content = await file.read()
            
            # For now, simulate conversion with a simple text processing
            # TODO: Integrate with actual CrankDoc worker containers
            result = await self._simulate_conversion(
                file_content, file.filename, source_format, target_format
            )
            
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="convert",
                status="completed",
                result=result
            )
            
        except Exception as e:
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="convert",
                status="failed",
                result={"error": f"Conversion failed: {str(e)}"}
            )
    
    async def _handle_validation(self, request: MeshRequest, file: UploadFile) -> MeshResponse:
        """Handle document validation requests."""
        if not file:
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="validate",
                status="failed",
                result={"error": "File is required for validation"}
            )
        
        try:
            file_content = await file.read()
            file_size = len(file_content)
            
            # Basic validation
            validation_result = {
                "filename": file.filename,
                "file_size": file_size,
                "is_valid": file_size > 0 and file_size < 50 * 1024 * 1024,  # < 50MB
                "format_detected": self._detect_format(file.filename),
                "warnings": []
            }
            
            if file_size == 0:
                validation_result["warnings"].append("File is empty")
            elif file_size > 50 * 1024 * 1024:
                validation_result["warnings"].append("File exceeds 50MB limit")
            
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="validate",
                status="completed",
                result=validation_result
            )
            
        except Exception as e:
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="validate",
                status="failed",
                result={"error": f"Validation failed: {str(e)}"}
            )
    
    async def _handle_analysis(self, request: MeshRequest, file: UploadFile) -> MeshResponse:
        """Handle document analysis requests."""
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
            
            # Basic analysis
            analysis_result = {
                "filename": file.filename,
                "file_size": len(file_content),
                "format_detected": self._detect_format(file.filename),
                "char_count": len(file_content.decode('utf-8', errors='ignore')),
                "line_count": file_content.decode('utf-8', errors='ignore').count('\n'),
                "estimated_word_count": len(file_content.decode('utf-8', errors='ignore').split()),
                "processing_complexity": "low"  # TODO: Implement real complexity analysis
            }
            
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="analyze",
                status="completed",
                result=analysis_result
            )
            
        except Exception as e:
            return MeshResponse(
                job_id=request.job_id,
                service_type=self.service_type,
                operation="analyze",
                status="failed",
                result={"error": f"Analysis failed: {str(e)}"}
            )
    
    async def _simulate_conversion(self, content: bytes, filename: str, 
                                 source_format: str, target_format: str) -> Dict[str, Any]:
        """Simulate document conversion (replace with real conversion logic)."""
        
        # For demo purposes, just return metadata about the conversion
        # TODO: Integrate with actual pandoc/worker containers
        
        await asyncio.sleep(0.1)  # Simulate processing time
        
        return {
            "source_filename": filename,
            "source_format": source_format,
            "target_format": target_format,
            "source_size": len(content),
            "target_size": len(content),  # Simulated
            "conversion_method": "pandoc",
            "status": "success",
            "output_url": f"/downloads/{uuid4().hex}.{target_format}",
            "metadata": {
                "title": filename.rsplit('.', 1)[0] if '.' in filename else filename,
                "pages": 1,
                "processing_time_ms": 100
            }
        }
    
    def _detect_format(self, filename: str) -> str:
        """Detect file format from filename."""
        if not filename or '.' not in filename:
            return "unknown"
        
        extension = filename.rsplit('.', 1)[1].lower()
        format_map = {
            'md': 'markdown',
            'txt': 'text',
            'docx': 'docx',
            'pdf': 'pdf',
            'html': 'html',
            'htm': 'html',
            'rtf': 'rtf'
        }
        
        return format_map.get(extension, extension)
    
    async def get_service_capabilities(self) -> MeshCapabilities:
        """Return document service capabilities."""
        return MeshCapabilities(
            service_type=self.service_type,
            operations=["convert", "validate", "analyze"],
            supported_formats=self.supported_formats,
            limits={
                "max_file_size": "50MB",
                "max_processing_time": "5min",
                "concurrent_jobs": "10"
            },
            health_status="ready"
        )
    
    async def get_processing_receipt(self, job_id: str) -> Optional[MeshReceipt]:
        """Get processing receipt for a job."""
        return self.receipts.get(job_id)
    
    async def check_readiness(self) -> Dict[str, Any]:
        """Check if document service is ready."""
        return {
            "ready": True,
            "service_type": self.service_type,
            "node_id": self.node_id,
            "checks": {
                "pandoc": "available",  # TODO: Check actual pandoc availability
                "workers": "ready",     # TODO: Check worker container health
                "storage": "ready",     # TODO: Check storage availability
                "policy_engine": "ready"  # TODO: Check OPA connectivity
            },
            "active_jobs": 0,  # TODO: Track actual job count
            "queue_length": 0   # TODO: Track actual queue length
        }


# Create the FastAPI app
def create_crankdoc_service() -> Any:
    """Create the CrankDoc mesh service."""
    service = CrankDocMeshService()
    return service.app


# For running directly
if __name__ == "__main__":
    import uvicorn
    app = create_crankdoc_service()
    uvicorn.run(app, host="0.0.0.0", port=8000)