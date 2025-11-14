# E2E Testing Guide - MN-DOC-001

**Purpose**: Run end-to-end BDD tests for document conversion via MCP.

## Quick Start

### 1. Install Dependencies

```bash
pip install pytest pytest-bdd
```

### 2. Local Testing (Recommended First)

Run the MCP server locally and point tests at it:

```bash
# In one terminal: Start crank-doc-converter MCP server
python services/crank_doc_converter_mcp_server.py

# In another terminal: Run tests
pytest tests/e2e/test_doc_converter_steps.py -v
```

**Benefits**:

- Fast iteration (no network latency)
- Zero deployment complexity
- Easy debugging with local logs

### 3. Remote Testing (Later)

For hosted MCP servers (Azure Container Apps, App Service, AKS):

```python
# Update conftest.py fixture
@pytest.fixture
def mcp_client():
    client = MCPClient(
        url="https://crank-doc-converter.azurewebsites.net",
        auth_token=os.getenv("MCP_AUTH_TOKEN"),
        verify_tls=True
    )
    yield client
    client.close()
```

Run tests against production:

```bash
export MCP_AUTH_TOKEN="your-token-here"
pytest tests/e2e/test_doc_converter_steps.py -v --remote
```

## Test Structure

### Feature File (`doc_converter.feature`)

Gherkin scenarios define user-facing behavior:

```gherkin
@sync @small @latency
Scenario: Small document returns synchronously with hash and audit
  Given a 5MB PDF named "sample-5mb.pdf"
  When I invoke MCP tool "convert_document" with:
    | input_path | sample-5mb.pdf |
    | target     | docx           |
  Then the MCP result status is "ok"
  And the artifact includes a "sha256" field of length 64
  And the elapsed time is <= 3 seconds (p95 budget)
```

### Step Definitions (`test_doc_converter_steps.py`)

Pytest-bdd implementations of Given/When/Then:

```python
@given(parsers.parse('a {size:d}MB PDF named "{name}"'))
def have_pdf_fixture(size, name, sample_pdf_factory, tmp_path, request):
    pdf_path = sample_pdf_factory(size_mb=size, name=name, output_dir=tmp_path)
    request.config.cache.set("current_pdf_path", str(pdf_path))
    return pdf_path

@then(parsers.parse("the elapsed time is <= {seconds:d} seconds (p95 budget)"))
def check_latency(seconds, request):
    elapsed = request.config.cache.get("last_elapsed", float("inf"))
    assert elapsed <= seconds, f"Exceeded p95 budget: {elapsed}s > {seconds}s"
```

### Fixtures (`conftest.py`)

**Current State**: Mock implementations for offline development

**TODO**: Replace with real implementations:

```python
# Replace MCPClientMock with real MCP SDK
from mcp import Client

@pytest.fixture
def mcp_client():
    client = Client("crank-doc-converter")
    client.connect()
    yield client
    client.close()

# Replace sample_pdf_factory with real PDF generation
from reportlab.pdfgen import canvas

def factory(size_mb: int, name: str, output_dir: Path) -> Path:
    output = output_dir / name
    c = canvas.Canvas(str(output))
    # Generate pages until size_mb reached
    for i in range(size_mb * 10):  # ~100KB per page
        c.drawString(100, 750, f"Page {i}")
        c.showPage()
    c.save()
    return output

# Replace AuditSinkMock with real audit log reader
from crank.audit import AuditReader

@pytest.fixture
def audit_sink():
    reader = AuditReader("/var/log/crank/audit.jsonl")
    yield reader
```

## Running Tests

### Run All Scenarios

```bash
pytest tests/e2e/test_doc_converter_steps.py -v
```

### Run Tagged Scenarios Only

```bash
# Only sync tests
pytest tests/e2e/test_doc_converter_steps.py -m sync

# Only latency-critical tests
pytest tests/e2e/test_doc_converter_steps.py -m latency

# Async + large document tests
pytest tests/e2e/test_doc_converter_steps.py -m "async and large"
```

### Generate Test Report

```bash
pytest tests/e2e/test_doc_converter_steps.py --html=report.html --self-contained-html
```

## Pickle Format

The `doc_converter_pickle.json` file shows the compiled scenario structure:

```json
{
  "id": "MN-DOC-001-sync-happy-path",
  "uri": "tests/e2e/doc_converter.feature",
  "name": "Small document returns synchronously with hash and audit",
  "tags": ["@sync", "@small", "@latency"],
  "steps": [
    {"text": "an MCP client is connected to the \"crank-doc-converter\" server"},
    {"text": "I invoke MCP tool \"convert_document\" with:",
     "argument": {"rows":[["input_path","sample-5mb.pdf"],["target","docx"]]}}
  ]
}
```

**Use Cases**:

- Test result visualization tools
- Coverage analysis (which scenarios ran)
- CI/CD integration (export results as pickles)
- Cross-tool compatibility (Cucumber, SpecFlow, etc.)

## Debugging

### Enable Verbose Output

```bash
pytest tests/e2e/test_doc_converter_steps.py -v -s
```

### Debug Specific Step

Add breakpoint in step definition:

```python
@then(parsers.parse("the elapsed time is <= {seconds:d} seconds (p95 budget)"))
def check_latency(seconds, request):
    elapsed = request.config.cache.get("last_elapsed", float("inf"))
    breakpoint()  # Interactive debugging
    assert elapsed <= seconds
```

### Check Audit Events

```python
# In test or fixture
import json
with open("/var/log/crank/audit.jsonl") as f:
    for line in f:
        event = json.loads(line)
        print(f"Event: {event['request_id']} - {event['status']}")
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pytest pytest-bdd reportlab
          pip install -e src/

      - name: Start MCP server
        run: |
          python services/crank_doc_converter_mcp_server.py &
          sleep 5  # Wait for startup

      - name: Run E2E tests
        run: |
          pytest tests/e2e/ -v --html=e2e-report.html

      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: e2e-test-results
          path: e2e-report.html
```

## Next Steps

1. **Implement Real Fixtures** (Priority: High)
   - [ ] Replace MCPClientMock with MCP SDK client
   - [ ] Implement real PDF generation with reportlab
   - [ ] Connect to actual audit log infrastructure

2. **Add More Scenarios** (Priority: Medium)
   - [ ] Error handling (invalid input, timeout)
   - [ ] Concurrent requests (load testing)
   - [ ] Different document formats (PDF→XLSX, DOCX→PDF)

3. **Remote Testing** (Priority: Low)
   - [ ] Deploy MCP server to Azure
   - [ ] Configure mTLS or token auth
   - [ ] Add remote test configuration

4. **Coverage Analysis** (Priority: Medium)
   - [ ] Map scenarios to UR-DOC-001 requirements
   - [ ] Verify all acceptance criteria tested
   - [ ] Generate traceability report

## Related Documents

- **Feature File**: `tests/e2e/doc_converter.feature`
- **Step Definitions**: `tests/e2e/test_doc_converter_steps.py`
- **Fixtures**: `tests/e2e/conftest.py`
- **Pickle Schema**: `tests/e2e/doc_converter_pickle.json`
- **Requirements**: `docs/architecture/requirements-traceability.md` (MN-DOC-001)
- **Phase 2 Guide**: `docs/planning/PHASE_2_README.md`
