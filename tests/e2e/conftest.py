"""
Shared pytest-bdd fixtures for E2E tests.

This module provides:
  - MCP client fixture (mcp_client)
  - Sample PDF factory (sample_pdf_factory)
  - Audit sink fixture (audit_sink)
  - Request timer fixture (request_timer)

Note: These are skeleton implementations. Replace with actual MCP client,
real PDF generation, and proper audit infrastructure.
"""

import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

# ============================================================================
# MCP Client Fixture (Mock - Replace with Real Implementation)
# ============================================================================


class MCPClientMock:
    """Mock MCP client for testing. Replace with real MCP SDK client."""

    def __init__(self) -> None:
        self.is_connected = True
        self._tools = ["convert_document"]
        self._results: dict[str, Any] = {}

    def list_tools(self) -> list[str]:
        """Return available tools."""
        return self._tools

    def invoke_tool(self, tool: str, params: dict[str, Any]) -> dict[str, Any]:
        """Invoke MCP tool with parameters."""
        # Mock implementation - replace with real MCP call
        return {
            "status": "ok",
            "artifact_path": f"/tmp/{Path(params['input_path']).stem}.{params['target']}",
            "sha256": "a" * 64,  # Mock hash
        }

    def get_progress_intervals(self, job_id: str, timeout: int = 30) -> list[float]:
        """Get intervals between progress events."""
        # Mock: simulate progress every 1.5 seconds
        return [1.5, 1.5, 1.5]

    def wait_for_callback(
        self, job_id: str, timeout: int = 130
    ) -> dict[str, Any] | None:
        """Wait for async job completion callback."""
        # Mock: return success after brief wait
        time.sleep(0.1)
        return {
            "job_id": job_id,
            "status": "ok",
            "artifact_path": "/tmp/output.docx",
            "sha256": "b" * 64,
        }


@pytest.fixture
def mcp_client() -> Generator[MCPClientMock, None, None]:
    """
    Provide MCP client for testing.

    Replace this mock with real MCP client initialization:
        from mcp import Client
        client = Client("crank-doc-converter")
        yield client
        client.close()
    """
    client = MCPClientMock()
    yield client
    # Cleanup if needed


# ============================================================================
# Sample PDF Factory Fixture
# ============================================================================


@pytest.fixture
def sample_pdf_factory(tmp_path: Path) -> Any:
    """
    Factory fixture to create sample PDFs of specified size.

    Usage:
        pdf_path = sample_pdf_factory(size_mb=5, name="test.pdf", output_dir=tmp_path)

    Replace with real PDF generation (e.g., using reportlab, PyPDF2):
        def factory(size_mb: int, name: str, output_dir: Path) -> Path:
            from reportlab.pdfgen import canvas
            output = output_dir / name
            c = canvas.Canvas(str(output))
            # Generate pages until size_mb reached
            return output
    """

    def factory(size_mb: int, name: str, output_dir: Path) -> Path:
        """Create a sample PDF of specified size."""
        output = output_dir / name

        # Mock: create empty file for now
        # Real implementation: generate actual PDF with reportlab
        with open(output, "wb") as f:
            # Write placeholder bytes (real PDFs have headers/structure)
            f.write(b"%PDF-1.4\n")
            f.write(b"Mock PDF content\n" * (size_mb * 1024 * 50))  # Approximate size

        return output

    return factory


# ============================================================================
# Audit Sink Fixture
# ============================================================================


class AuditSinkMock:
    """Mock audit log sink. Replace with real audit infrastructure."""

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def get_last_event(self) -> dict[str, Any] | None:
        """Get most recent audit event."""
        if not self._events:
            # Mock: return synthetic event
            return {
                "request_id": "req-123",
                "tool": "convert_document",
                "status": "ok",
                "duration_ms": 2500,
            }
        return self._events[-1]

    def record_event(self, event: dict[str, Any]) -> None:
        """Record audit event."""
        self._events.append(event)


@pytest.fixture
def audit_sink() -> Generator[AuditSinkMock, None, None]:
    """
    Provide audit sink for verification.

    Replace with real audit log reader:
        from crank.audit import AuditReader
        reader = AuditReader("/var/log/crank/audit.jsonl")
        yield reader
    """
    sink = AuditSinkMock()
    yield sink


# ============================================================================
# Request Timer Fixture
# ============================================================================


class RequestTimer:
    """Context manager for timing requests."""

    def __init__(self) -> None:
        self.elapsed: float = 0.0
        self._start: float = 0.0

    def __enter__(self) -> "RequestTimer":
        """Start timer."""
        self._start = time.time()
        return self

    def __exit__(self, *args: Any) -> None:
        """Stop timer and record elapsed time."""
        self.elapsed = time.time() - self._start


@pytest.fixture
def request_timer() -> RequestTimer:
    """Provide timer for measuring request latency."""
    return RequestTimer()


# ============================================================================
# pytest-bdd Configuration
# ============================================================================


def pytest_bdd_apply_tag(tag: str, function: Any) -> None:
    """
    Apply pytest markers based on Gherkin tags.

    Example:
        @sync -> pytest.mark.sync
        @latency -> pytest.mark.latency
    """
    marker = tag.lstrip("@")
    if hasattr(pytest.mark, marker):
        getattr(pytest.mark, marker)(function)
