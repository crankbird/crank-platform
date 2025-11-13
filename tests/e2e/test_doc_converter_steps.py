"""
BDD step definitions for document converter E2E tests.

This module implements pytest-bdd steps for the doc_converter.feature scenarios.
Requires:
  - pytest-bdd
  - MCP client fixture (mcp_client)
  - Sample PDF factory (sample_pdf_factory)
  - Audit sink fixture (audit_sink)
  - Request timer fixture (request_timer)

Install dependencies:
    pip install pytest-bdd

Usage:
    pytest tests/e2e/test_doc_converter_steps.py

Note: Type annotations intentionally omitted for pytest-bdd decorated functions.
Fixtures are injected dynamically by pytest-bdd, making static typing impractical.
This entire file is excluded from mypy checking via pyproject.toml.
"""

# mypy: disable-error-code=misc

from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, Callable

from pytest import FixtureRequest
from pytest_bdd import given, parsers, scenarios, then, when  # type: ignore[import-not-found]

PdfFactory = Callable[..., Path]
TimerContext = AbstractContextManager[Any]
MCPClient = Any
AuditSink = Any

# Load all scenarios from the feature file
scenarios("doc_converter.feature")


# ============================================================================
# Background Steps
# ============================================================================


@given('an MCP client is connected to the "crank-doc-converter" server')
def mcp_client_connected(mcp_client: MCPClient) -> None:
    """Verify MCP client has established connection to doc converter server."""
    assert mcp_client.is_connected, "MCP client is not connected to server"


@given('the MCP tool "convert_document" is available')
def tool_available(mcp_client: MCPClient) -> None:
    """Verify the convert_document tool is listed in available tools."""
    available_tools = mcp_client.list_tools()
    assert (
        "convert_document" in available_tools
    ), f"Tool 'convert_document' not found. Available: {available_tools}"


# ============================================================================
# Given Steps - Test Data Setup
# ============================================================================


@given(parsers.parse('a {size:d}MB PDF named "{name}"'))
def have_pdf_fixture(
    size: int,
    name: str,
    sample_pdf_factory: PdfFactory,
    tmp_path: Path,
    request: FixtureRequest,
) -> Path:
    """
    Create a sample PDF of specified size.

    Args:
        size: Size in megabytes
        name: Filename for the PDF
        sample_pdf_factory: Fixture that generates PDFs
        tmp_path: pytest temporary directory
        request: pytest request object for context storage
    """
    pdf_path = sample_pdf_factory(size_mb=size, name=name, output_dir=tmp_path)
    assert pdf_path.exists(), f"Failed to create PDF fixture: {pdf_path}"

    # Store in request context for later steps
    request.config.cache.set("current_pdf_path", str(pdf_path))
    request.config.cache.set("current_pdf_name", name)

    return pdf_path


# ============================================================================
# When Steps - Actions
# ============================================================================


@when(parsers.parse('I invoke MCP tool "{tool}" with:\n{table}'))
def invoke_convert_with_table(
    tool: str,
    table: str,
    mcp_client: MCPClient,
    request_timer: TimerContext,
    request: FixtureRequest,
) -> dict[str, Any]:
    """
    Invoke MCP tool with parameters from a Gherkin table.

    Args:
        tool: Tool name (e.g., "convert_document")
        table: Gherkin table as string
        mcp_client: MCP client fixture
        request_timer: Timer fixture for latency measurement
        request: pytest request object for context storage
    """
    # Parse table into dict (simplified - real implementation needs table parser)
    # Expected format: | key | value |
    params = _parse_gherkin_table(table)

    # Get the PDF path from context
    pdf_path = request.config.cache.get("current_pdf_path", None)
    if pdf_path and "input_path" in params:
        # Replace placeholder with actual path
        params["input_path"] = pdf_path

    # Invoke tool with timing
    with request_timer as timer:
        result = mcp_client.invoke_tool(tool, params=params)

    # Store result and timing for assertions
    request.config.cache.set("last_result", result)
    request.config.cache.set("last_elapsed", timer.elapsed)

    return {"result": result, "elapsed": timer.elapsed}


# ============================================================================
# Then Steps - Assertions
# ============================================================================


@then(parsers.parse('the MCP result status is "{status}"'))
def check_status(status: str, request: FixtureRequest) -> None:
    """Verify the MCP result has expected status."""
    result = request.config.cache.get("last_result", {})
    actual_status = result.get("status")
    assert (
        actual_status == status
    ), f"Expected status '{status}', got '{actual_status}'"


@then(parsers.parse('a file artifact "{name}" is produced'))
def check_artifact(name: str, request: FixtureRequest, tmp_path: Path) -> None:
    """Verify the output artifact file exists."""
    result = request.config.cache.get("last_result", {})
    artifact_path = result.get("artifact_path")

    assert artifact_path, "No artifact_path in result"

    # Check file exists
    artifact_file = Path(artifact_path)
    assert artifact_file.exists(), f"Artifact file not found: {artifact_path}"

    # Check filename matches
    assert artifact_file.name == name, f"Expected {name}, got {artifact_file.name}"


@then('the artifact includes a "sha256" field of length 64')
def check_hash(request: FixtureRequest) -> None:
    """Verify result includes valid SHA-256 hash."""
    result = request.config.cache.get("last_result", {})
    sha256 = result.get("sha256")

    assert sha256, "No sha256 field in result"
    assert isinstance(sha256, str), f"sha256 should be string, got {type(sha256)}"
    assert len(sha256) == 64, f"sha256 should be 64 chars, got {len(sha256)}"
    # Verify it's valid hex
    try:
        int(sha256, 16)
    except ValueError as exc:
        raise AssertionError(f"sha256 is not valid hexadecimal: {sha256}") from exc


@then(parsers.parse("the elapsed time is <= {seconds:d} seconds (p95 budget)"))
def check_latency(seconds: int, request: FixtureRequest) -> None:
    """Verify request completed within latency budget."""
    elapsed = request.config.cache.get("last_elapsed", float("inf"))
    assert elapsed <= seconds, f"Exceeded p95 budget: {elapsed}s > {seconds}s"


@then(parsers.parse("an audit event is recorded with fields:\n{table}"))
def check_audit_with_table(table: str, audit_sink: AuditSink) -> None:
    """
    Verify audit event was recorded with expected fields.

    Args:
        table: Gherkin table specifying required fields
        audit_sink: Fixture for querying audit log
    """
    # Parse expected fields from table
    expected_fields = _parse_audit_table(table)

    # Query most recent audit event
    last_event = audit_sink.get_last_event()
    assert last_event, "No audit event found in sink"

    # Verify all required fields present
    for field in expected_fields:
        assert field in last_event, f"Missing audit field: {field}"

    # Verify redaction (no PII fields)
    pii_fields = ["token", "email", "password"]
    for pii in pii_fields:
        assert pii not in last_event, f"PII field '{pii}' should be redacted"


# ============================================================================
# Async/Progress Steps
# ============================================================================


@then(parsers.parse('I receive an "{status}" response with a "{field}"'))
def check_accepted_with_job_id(
    status: str, field: str, request: FixtureRequest
) -> None:
    """Verify async response has expected status and job ID."""
    result = request.config.cache.get("last_result", {})

    actual_status = result.get("status")
    assert (
        actual_status == status
    ), f"Expected status '{status}', got '{actual_status}'"

    job_id = result.get(field)
    assert job_id, f"No '{field}' in response"

    # Store job_id for subsequent steps
    request.config.cache.set("current_job_id", job_id)


@then(parsers.parse("progress events emit at least every {seconds:d} seconds"))
def check_progress_events(
    seconds: int, mcp_client: MCPClient, request: FixtureRequest
) -> None:
    """Verify progress events arrive at expected intervals."""
    job_id = request.config.cache.get("current_job_id", None)
    assert job_id, "No job_id in context"

    # Subscribe to progress events
    progress_intervals = mcp_client.get_progress_intervals(job_id, timeout=30)

    # Verify no gap exceeds threshold
    for interval in progress_intervals:
        assert (
            interval <= seconds
        ), f"Progress gap {interval}s exceeds {seconds}s threshold"


@then(parsers.parse("a callback payload is delivered with:\n{table}"))
def check_callback_payload(
    table: str, mcp_client: MCPClient, request: FixtureRequest
) -> None:
    """Verify async callback contains expected fields."""
    job_id = request.config.cache.get("current_job_id", None)
    assert job_id, "No job_id in context"

    # Wait for completion callback
    callback = mcp_client.wait_for_callback(job_id, timeout=130)
    assert callback, f"No callback received for job {job_id}"

    # Parse expected fields
    expected_fields = _parse_callback_table(table)

    # Verify all fields present
    for field in expected_fields:
        assert field in callback, f"Missing callback field: {field}"


@then(parsers.parse("the total elapsed time is <= {seconds:d} seconds"))
def check_total_elapsed(seconds: int, request: FixtureRequest) -> None:
    """Verify total operation time including async wait."""
    elapsed = request.config.cache.get("last_elapsed", float("inf"))
    assert elapsed <= seconds, f"Total time {elapsed}s exceeds {seconds}s budget"


@then(parsers.parse('an audit event is recorded with status "{status}"'))
def check_audit_status(status: str, audit_sink: AuditSink) -> None:
    """Verify audit event has expected status."""
    last_event = audit_sink.get_last_event()
    assert last_event, "No audit event found"

    actual_status = last_event.get("status")
    assert (
        actual_status == status
    ), f"Expected audit status '{status}', got '{actual_status}'"


# ============================================================================
# Helper Functions
# ============================================================================


def _parse_gherkin_table(table_str: str) -> dict[str, str]:
    """
    Parse Gherkin table string into dict.

    Example input:
        | input_path | sample-5mb.pdf |
        | target     | docx           |

    Returns:
        {"input_path": "sample-5mb.pdf", "target": "docx"}
    """
    params = {}
    for line in table_str.strip().split("\n"):
        line = line.strip()
        if not line or line == "|":
            continue

        # Split on | and clean
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) == 2:
            key, value = parts
            params[key] = value

    return params


def _parse_audit_table(table_str: str) -> list[str]:
    """
    Extract field names from audit table.

    Example input:
        | request_id | tool | status | duration_ms |

    Returns:
        ["request_id", "tool", "status", "duration_ms"]
    """
    # First row has field names
    first_line = table_str.strip().split("\n")[0]
    parts = [p.strip() for p in first_line.split("|") if p.strip()]
    return parts


def _parse_callback_table(table_str: str) -> list[str]:
    """Extract expected callback fields from table."""
    return _parse_audit_table(table_str)
