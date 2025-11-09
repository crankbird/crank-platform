"""
Mesh Diagnostic Services - Built-in Testing and Validation

Every mesh service includes lightweight diagnostic operations that help distinguish
between wrapper/infrastructure issues and actual business logic problems.

Think of these as "ICMP ping" for mesh services - minimal functions that test
the entire request/response pipeline without complex business logic.
"""

import hashlib
import time
from datetime import datetime
from typing import Any, Optional

from fastapi import UploadFile
from mesh_interface import MeshCapability, MeshInterface, MeshRequest, MeshResponse


class MeshDiagnostics:
    """Standard diagnostic operations for all mesh services."""

    @staticmethod
    def get_diagnostic_capabilities() -> list[MeshCapability]:
        """Return standard diagnostic capabilities for any service."""
        return [
            MeshCapability(
                operation="ping",
                description="Echo test - verifies mesh wrapper is functioning",
                input_schema={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "default": "hello"},
                        "delay_ms": {
                            "type": "integer",
                            "default": 0,
                            "minimum": 0,
                            "maximum": 5000,
                        },
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "echo": {"type": "string"},
                        "timestamp": {"type": "string"},
                        "processing_time_ms": {"type": "number"},
                        "test_passed": {"type": "boolean"},
                    },
                },
                policies_required=["basic_auth"],
                limits={"max_delay_ms": "5000"},
            ),
            MeshCapability(
                operation="echo_file",
                description="File upload test - verifies file handling pipeline",
                input_schema={
                    "type": "object",
                    "properties": {
                        "return_hash": {"type": "boolean", "default": True},
                        "return_size": {"type": "boolean", "default": True},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "size": {"type": "integer"},
                        "hash": {"type": "string", "description": "SHA256 hash of file"},
                    },
                },
                policies_required=["basic_auth", "file_validation"],
                limits={"max_file_size": "1048576"},  # 1MB for diagnostic
            ),
            MeshCapability(
                operation="load_test",
                description="Load test - verifies performance under controlled load",
                input_schema={
                    "type": "object",
                    "properties": {
                        "cpu_work_ms": {"type": "integer", "default": 100, "maximum": 1000},
                        "memory_mb": {"type": "integer", "default": 1, "maximum": 10},
                        "response_size_kb": {"type": "integer", "default": 1, "maximum": 100},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "load_test_completed": {"type": "boolean"},
                        "cpu_work_ms": {"type": "integer"},
                        "memory_used_mb": {"type": "integer"},
                        "response_size_kb": {"type": "integer"},
                    },
                },
                policies_required=["basic_auth"],
                limits={"max_cpu_work_ms": "1000", "max_memory_mb": "10"},
            ),
            MeshCapability(
                operation="error_test",
                description="Error handling test - verifies error propagation",
                input_schema={
                    "type": "object",
                    "properties": {
                        "error_type": {
                            "type": "string",
                            "enum": ["validation", "timeout", "resource", "business_logic"],
                            "default": "validation",
                        },
                        "error_message": {"type": "string", "default": "Diagnostic error test"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "error_triggered": {"type": "boolean"},
                        "error_type": {"type": "string"},
                        "error_message": {"type": "string"},
                    },
                },
                policies_required=["basic_auth"],
                limits={},
            ),
        ]

    @staticmethod
    async def handle_ping(request: MeshRequest) -> dict[str, Any]:
        """Ping/echo test - verifies basic mesh functionality."""
        message = request.input_data.get("message", "hello")
        delay_ms = request.input_data.get("delay_ms", 0)

        start_time = time.time()

        # Optional delay for timing tests
        if delay_ms > 0:
            import asyncio

            await asyncio.sleep(delay_ms / 1000)

        processing_time = int((time.time() - start_time) * 1000)

        return {
            "echo": message,
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": processing_time,
            "service_node": (request.metadata or {}).get("mesh_node_id", "unknown"),
            "test_passed": True,
            "diagnostic_info": {
                "request_id": request.job_id,
                "operation": request.operation,
                "policies_applied": request.policies or [],
                "auth_validated": True,  # If we got here, auth worked
            },
        }

    @staticmethod
    async def handle_echo_file(request: MeshRequest, file: Optional[UploadFile]) -> dict[str, Any]:
        """File echo test - verifies file upload/download pipeline."""
        if not file:
            raise ValueError("No file provided for echo_file test")

        start_time = time.time()

        # Read file content
        content = await file.read()
        await file.seek(0)  # Reset for potential re-reading

        result = {
            "filename": file.filename,
            "content_type": file.content_type,
            "test_passed": True,
        }

        # Optional hash calculation
        if request.input_data.get("return_hash", True):
            file_hash = hashlib.sha256(content).hexdigest()
            result["sha256_hash"] = file_hash

        # Optional size calculation
        if request.input_data.get("return_size", True):
            result["size_bytes"] = len(content)

        processing_time = int((time.time() - start_time) * 1000)
        result["processing_time_ms"] = processing_time

        return result

    @staticmethod
    async def handle_load_test(request: MeshRequest) -> dict[str, Any]:
        """Load test - controlled resource usage for testing."""

        cpu_work_ms = request.input_data.get("cpu_work_ms", 100)
        memory_mb = request.input_data.get("memory_mb", 1)
        response_size_kb = request.input_data.get("response_size_kb", 1)

        start_time = time.time()

        # CPU work simulation
        if cpu_work_ms > 0:
            # Simple CPU-bound work
            end_time = start_time + (cpu_work_ms / 1000)
            total = 0
            while time.time() < end_time:
                total += 1

        # Memory allocation test
        memory_test_data = None
        if memory_mb > 0:
            # Allocate requested memory
            memory_test_data = bytearray(memory_mb * 1024 * 1024)
            memory_test_data[0] = 1  # Touch the memory

        # Generate response data of requested size
        response_data = "x" * (response_size_kb * 1024)

        processing_time = int((time.time() - start_time) * 1000)

        return {
            "test_passed": True,
            "requested_cpu_ms": cpu_work_ms,
            "requested_memory_mb": memory_mb,
            "requested_response_kb": response_size_kb,
            "actual_processing_time_ms": processing_time,
            "memory_allocated": memory_mb > 0,
            "response_data": response_data[:100] + "..."
            if len(response_data) > 100
            else response_data,
            "response_size_actual": len(response_data),
        }

    @staticmethod
    async def handle_error_test(request: MeshRequest) -> dict[str, Any]:
        """Error test - verifies error handling and propagation."""
        error_type = request.input_data.get("error_type", "validation")
        error_message = request.input_data.get("error_message", "Diagnostic error test")

        if error_type == "validation":
            raise ValueError(f"Validation error: {error_message}")
        if error_type == "timeout":
            import asyncio

            await asyncio.sleep(10)  # Will likely timeout
        elif error_type == "resource":
            # Try to allocate unreasonable memory
            bytearray(1024 * 1024 * 1024)  # 1GB
        elif error_type == "business_logic":
            raise Exception(f"Business logic error: {error_message}")
        else:
            raise ValueError(f"Unknown error type: {error_type}")


class DiagnosticMeshService(MeshInterface):
    """Pure diagnostic service for testing mesh infrastructure."""

    def __init__(self):
        super().__init__("diagnostic")
        self.diagnostics = MeshDiagnostics()

    def get_capabilities(self) -> list[MeshCapability]:
        """Return only diagnostic capabilities."""
        return self.diagnostics.get_diagnostic_capabilities()

    def generate_receipt(self, request: MeshRequest, response: MeshResponse, auth_context: dict):
        """Simple receipt generation for diagnostics."""

        # Return a simple object with receipt_id attribute
        class SimpleReceipt:
            def __init__(self, receipt_id):
                self.receipt_id = receipt_id

        return SimpleReceipt(f"mesh_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    async def process_request(self, request: MeshRequest, auth_context: dict) -> MeshResponse:
        """Process diagnostic requests."""
        start_time = time.time()

        try:
            if request.operation == "ping":
                result = await self.diagnostics.handle_ping(request)
            elif request.operation == "echo_file":
                # Note: file would be passed separately in real implementation
                result = await self.diagnostics.handle_echo_file(request, None)
            elif request.operation == "load_test":
                result = await self.diagnostics.handle_load_test(request)
            elif request.operation == "error_test":
                result = await self.diagnostics.handle_error_test(request)
            else:
                raise ValueError(f"Unknown diagnostic operation: {request.operation}")

            processing_time = int((time.time() - start_time) * 1000)

            return MeshResponse(
                success=True,
                result=result,
                receipt_id=f"diag-{hash(str(request.input_data)) % 100000}",
                processing_time_ms=processing_time,
                mesh_node_id=self.node_id,
            )

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)

            return MeshResponse(
                success=False,
                result={"error": str(e), "error_type": type(e).__name__},
                errors=[str(e)],
                receipt_id=f"diag-error-{hash(str(e)) % 100000}",
                processing_time_ms=processing_time,
                mesh_node_id=self.node_id,
            )


# Mixin for adding diagnostics to any service
class DiagnosticMixin:
    """Mixin to add diagnostic capabilities to any mesh service."""

    def __init__(self):
        self.diagnostics = MeshDiagnostics()

    def get_diagnostic_capabilities(self) -> list[MeshCapability]:
        """Get diagnostic capabilities to add to service capabilities."""
        return self.diagnostics.get_diagnostic_capabilities()

    async def handle_diagnostic_request(
        self,
        request: MeshRequest,
        file: Optional[UploadFile] = None,
    ) -> dict[str, Any]:
        """Handle diagnostic operations."""
        if request.operation == "ping":
            return await self.diagnostics.handle_ping(request)
        if request.operation == "echo_file":
            return await self.diagnostics.handle_echo_file(request, file)
        if request.operation == "load_test":
            return await self.diagnostics.handle_load_test(request)
        if request.operation == "error_test":
            return await self.diagnostics.handle_error_test(request)
        raise ValueError(f"Unknown diagnostic operation: {request.operation}")


# Example of adding diagnostics to existing service
class EnhancedCrankDocService(MeshInterface, DiagnosticMixin):
    """CrankDoc service with built-in diagnostics."""

    def __init__(self):
        MeshInterface.__init__(self, "document")
        DiagnosticMixin.__init__(self)

    def get_capabilities(self) -> list[MeshCapability]:
        """Return both business and diagnostic capabilities."""
        business_capabilities = [
            MeshCapability(
                operation="convert",
                description="Convert documents between formats",
                input_schema={
                    "type": "object",
                    "properties": {"target_format": {"type": "string"}},
                },
                policies_required=["file_validation", "format_allowlist"],
                limits={"max_file_size": 52428800},  # 50MB
            ),
        ]

        diagnostic_capabilities = self.get_diagnostic_capabilities()

        return business_capabilities + diagnostic_capabilities

    async def process_request(self, request: MeshRequest, auth_context: dict) -> MeshResponse:
        """Process both business and diagnostic requests."""
        start_time = time.time()

        try:
            # Check if it's a diagnostic operation
            diagnostic_ops = ["ping", "echo_file", "load_test", "error_test"]
            if request.operation in diagnostic_ops:
                result = await self.handle_diagnostic_request(request)
            # Handle business operations
            elif request.operation == "convert":
                result = await self._handle_conversion(request)
            else:
                raise ValueError(f"Unknown operation: {request.operation}")

            processing_time = int((time.time() - start_time) * 1000)

            return MeshResponse(
                success=True,
                result=result,
                receipt_id=f"doc-{hash(str(request.input_data)) % 100000}",
                processing_time_ms=processing_time,
                mesh_node_id=self.node_id,
            )

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)

            return MeshResponse(
                success=False,
                result={"error": str(e), "error_type": type(e).__name__},
                errors=[str(e)],
                receipt_id=f"doc-error-{hash(str(e)) % 100000}",
                processing_time_ms=processing_time,
                mesh_node_id=self.node_id,
            )

    async def _handle_conversion(self, request: MeshRequest) -> dict[str, Any]:
        """Handle document conversion (business logic)."""
        # Real conversion logic would go here
        return {
            "converted": True,
            "target_format": request.input_data.get("target_format", "pdf"),
            "message": "This is the real business logic",
        }


if __name__ == "__main__":
    print("🔍 MESH DIAGNOSTIC FRAMEWORK")
    print("=" * 30)
    print()
    print("Built-in diagnostic operations for every mesh service:")

    diagnostics = MeshDiagnostics()
    capabilities = diagnostics.get_diagnostic_capabilities()

    for cap in capabilities:
        print(f"• {cap.operation}: {cap.description}")

    print()
    print("Benefits:")
    print("• Test mesh wrapper without business logic complexity")
    print("• Distinguish infrastructure vs application issues")
    print("• Load testing and performance validation")
    print("• Error handling verification")
    print("• File upload/download pipeline testing")
    print()
    print("Usage: Every service gets these operations automatically")
    print("Just like ICMP ping - always available for diagnostics! 🏥")
