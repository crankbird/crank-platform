"""
Crank Diagnostic Mesh Service - Refactored Clean Architecture

This provides diagnostic capabilities for testing mesh infrastructure:
- ping: Basic echo test with timing
- echo_file: File upload/download test
- load_test: Controlled load testing
- error_test: Error handling validation

REFACTORED VERSION: Uses clean mesh interface without hacky patches.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Optional

from mesh_interface_v2 import MeshCapability, MeshInterface, MeshRequest, MeshResponse


class DiagnosticMeshService(MeshInterface):
    """Diagnostic mesh service for infrastructure testing."""

    def __init__(self, node_id: Optional[str] = None):
        super().__init__(service_type="diagnostic", node_id=node_id)

    def get_capabilities(self) -> list[MeshCapability]:
        """Return diagnostic capabilities."""
        return [
            MeshCapability(
                operation="ping",
                description="Echo test - verifies mesh wrapper is functioning",
                input_schema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo back",
                            "default": "Hello Crank Mesh",
                        },
                        "delay_ms": {
                            "type": "integer",
                            "description": "Artificial delay in milliseconds",
                            "minimum": 0,
                            "maximum": 5000,
                            "default": 0,
                        },
                    },
                    "required": ["message"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "echo": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"},
                        "processing_time_ms": {"type": "integer"},
                        "service_node": {"type": "string"},
                        "test_passed": {"type": "boolean"},
                        "diagnostic_info": {
                            "type": "object",
                            "properties": {
                                "request_id": {"type": "string"},
                                "operation": {"type": "string"},
                                "policies_applied": {"type": "array", "items": {"type": "string"}},
                                "auth_validated": {"type": "boolean"},
                            },
                        },
                    },
                    "required": ["echo", "timestamp", "processing_time_ms", "test_passed"],
                },
                policies_required=["basic_auth"],
                limits={
                    "max_delay_ms": 5000,
                    "max_message_length": 1000,
                },
            ),
            MeshCapability(
                operation="echo_file",
                description="File upload test - verifies file handling pipeline",
                input_schema={
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Original filename"},
                        "expected_size": {
                            "type": "integer",
                            "description": "Expected file size in bytes",
                        },
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "size_bytes": {"type": "integer"},
                        "content_type": {"type": "string"},
                        "checksum": {"type": "string"},
                        "processing_time_ms": {"type": "integer"},
                        "test_passed": {"type": "boolean"},
                    },
                    "required": ["filename", "size_bytes", "test_passed"],
                },
                policies_required=["basic_auth"],
                limits={
                    "max_file_size_mb": 10,
                    "allowed_types": ["text/plain", "application/json", "text/csv"],
                },
            ),
            MeshCapability(
                operation="load_test",
                description="Load test - verifies performance under controlled load",
                input_schema={
                    "type": "object",
                    "properties": {
                        "cpu_work_ms": {
                            "type": "integer",
                            "description": "CPU work simulation in milliseconds",
                            "minimum": 0,
                            "maximum": 1000,
                            "default": 100,
                        },
                        "memory_mb": {
                            "type": "integer",
                            "description": "Memory allocation test in MB",
                            "minimum": 0,
                            "maximum": 10,
                            "default": 1,
                        },
                        "response_size_kb": {
                            "type": "integer",
                            "description": "Response size simulation in KB",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 1,
                        },
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "load_test_completed": {"type": "boolean"},
                        "cpu_work_ms": {"type": "integer"},
                        "memory_used_mb": {"type": "integer"},
                        "response_size_kb": {"type": "integer"},
                        "processing_time_ms": {"type": "integer"},
                        "performance_metrics": {
                            "type": "object",
                            "properties": {
                                "cpu_efficiency": {"type": "number"},
                                "memory_efficiency": {"type": "number"},
                            },
                        },
                    },
                    "required": ["load_test_completed", "cpu_work_ms", "memory_used_mb"],
                },
                policies_required=["basic_auth"],
                limits={
                    "max_cpu_work_ms": 1000,
                    "max_memory_mb": 10,
                    "max_response_size_kb": 100,
                },
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
                            "description": "Type of error to simulate",
                        },
                        "error_message": {
                            "type": "string",
                            "default": "Diagnostic error test",
                            "description": "Custom error message",
                        },
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "error_triggered": {"type": "boolean"},
                        "error_type": {"type": "string"},
                        "error_message": {"type": "string"},
                        "error_handled_correctly": {"type": "boolean"},
                    },
                    "required": ["error_triggered", "error_type"],
                },
                policies_required=["basic_auth"],
                limits={},
            ),
        ]

    async def process_request(
        self, request: MeshRequest, auth_context: dict[str, Any],
    ) -> MeshResponse:
        """Process diagnostic requests."""
        operation = request.operation

        try:
            if operation == "ping":
                result = await self._handle_ping(request, auth_context)
            elif operation == "echo_file":
                # File operations would need special handling in FastAPI
                result = {"error": "echo_file requires file upload endpoint"}
            elif operation == "load_test":
                result = await self._handle_load_test(request, auth_context)
            elif operation == "error_test":
                result = await self._handle_error_test(request, auth_context)
            else:
                raise ValueError(f"Unknown operation: {operation}")

            return MeshResponse(
                success=True,
                result=result,
                receipt_id="",  # Will be set by base class
                errors=[],
                metadata={"operation_completed": operation},
                processing_time_ms=0,  # Will be set by base class
                mesh_node_id=self.node_id,
            )

        except Exception as e:
            return MeshResponse(
                success=False,
                result=None,
                receipt_id="",  # Will be set by base class
                errors=[str(e)],
                metadata={"operation_failed": operation, "error_type": type(e).__name__},
                processing_time_ms=0,  # Will be set by base class
                mesh_node_id=self.node_id,
            )

    async def _handle_ping(
        self, request: MeshRequest, auth_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle ping operation."""
        start_time = time.time()

        message = request.input_data.get("message", "Hello Crank Mesh")
        delay_ms = request.input_data.get("delay_ms", 0)

        # Validate inputs
        if len(message) > 1000:
            raise ValueError("Message too long (max 1000 characters)")

        if delay_ms > 5000:
            raise ValueError("Delay too long (max 5000ms)")

        # Simulate delay if requested
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return {
            "echo": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "processing_time_ms": processing_time_ms,
            "service_node": request.metadata.get("mesh_node_id", "unknown"),
            "test_passed": True,
            "diagnostic_info": {
                "request_id": request.job_id,
                "operation": request.operation,
                "policies_applied": request.policies,
                "auth_validated": auth_context.get("authenticated", False),
            },
        }

    async def _handle_load_test(
        self, request: MeshRequest, auth_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle load test operation."""
        start_time = time.time()

        cpu_work_ms = request.input_data.get("cpu_work_ms", 100)
        memory_mb = request.input_data.get("memory_mb", 1)
        response_size_kb = request.input_data.get("response_size_kb", 1)

        # Validate limits
        if cpu_work_ms > 1000:
            raise ValueError("CPU work too high (max 1000ms)")
        if memory_mb > 10:
            raise ValueError("Memory allocation too high (max 10MB)")
        if response_size_kb > 100:
            raise ValueError("Response size too large (max 100KB)")

        # Simulate CPU work
        if cpu_work_ms > 0:
            await asyncio.sleep(cpu_work_ms / 1000)

        # Simulate memory allocation (create some data)
        "x" * (memory_mb * 1024 * 1024) if memory_mb > 0 else ""

        # Create response data of specified size
        response_data = "data" * (response_size_kb * 256)  # Approximate KB

        processing_time_ms = int((time.time() - start_time) * 1000)

        return {
            "load_test_completed": True,
            "cpu_work_ms": cpu_work_ms,
            "memory_used_mb": memory_mb,
            "response_size_kb": len(response_data) // 1024,
            "processing_time_ms": processing_time_ms,
            "performance_metrics": {
                "cpu_efficiency": cpu_work_ms / max(processing_time_ms, 1),
                "memory_efficiency": memory_mb / max(memory_mb, 1),
            },
            "response_data": response_data[:100] + "..."
            if len(response_data) > 100
            else response_data,
        }

    async def _handle_error_test(
        self, request: MeshRequest, auth_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle error test operation."""
        error_type = request.input_data.get("error_type", "validation")
        error_message = request.input_data.get("error_message", "Diagnostic error test")

        # Simulate different types of errors
        if error_type == "validation":
            raise ValueError(f"Validation error: {error_message}")
        if error_type == "timeout":
            raise TimeoutError(f"Timeout error: {error_message}")
        if error_type == "resource":
            raise RuntimeError(f"Resource error: {error_message}")
        if error_type == "business_logic":
            raise Exception(f"Business logic error: {error_message}")
        raise ValueError(f"Unknown error type: {error_type}")


# =============================================================================
# SERVICE ENTRY POINT
# =============================================================================


def create_diagnostic_app(api_key: str = "dev-mesh-key") -> "FastAPI":
    """Create diagnostic mesh service app."""
    service = DiagnosticMeshService()
    return service.create_app(api_key)


if __name__ == "__main__":
    import os

    import uvicorn

    app = create_diagnostic_app()
    port = int(os.getenv("DIAGNOSTICS_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
