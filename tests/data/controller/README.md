# Controller Exchange Fixtures

## Purpose

Test the `ControllerClient` improvements from commit 824bb96:

- Lazy httpx.AsyncClient initialization
- Proper connection pooling and reuse
- Resource cleanup (close() method)
- SSL/TLS configuration (verify_ssl parameter)
- Error handling for network failures

## Structure

```text
controller/
├── registration/          # Worker registration exchanges
│   ├── successful.json   # Successful registration
│   ├── retry.json        # Registration with retry
│   └── ssl-error.json    # TLS handshake failure
├── heartbeat/             # Heartbeat exchanges
│   ├── normal.json       # Regular heartbeat sequence
│   ├── timeout.json      # Controller timeout
│   └── reconnect.json    # Connection recovery
└── shutdown/              # Shutdown sequences (see shutdown/README.md)
```

## Fixture schema

Each JSON file contains request/response pairs:

```json
{
  "exchange": "registration",
  "description": "Successful worker registration with controller",
  "request": {
    "method": "POST",
    "url": "https://controller:8000/api/workers/register",
    "json": {
      "worker_id": "test-worker-1",
      "service_type": "streaming",
      "endpoint": "https://worker:8500",
      "health_url": "https://worker:8500/health",
      "capabilities": ["streaming.classify"]
    },
    "headers": {
      "Content-Type": "application/json"
    }
  },
  "response": {
    "status_code": 200,
    "json": {
      "status": "registered",
      "worker_id": "test-worker-1",
      "heartbeat_interval": 30
    },
    "headers": {
      "Content-Type": "application/json"
    }
  },
  "expected_client_state": {
    "http_client_created": true,
    "connection_pooling": true,
    "ssl_verify": true
  }
}
```

## Testing patterns

### Successful registration

```python
from tests.data.loader import load_controller_exchange
from unittest.mock import AsyncMock

exchange = load_controller_exchange("registration/successful.json")

# Mock httpx response
mock_response = AsyncMock()
mock_response.status_code = exchange["response"]["status_code"]
mock_response.json.return_value = exchange["response"]["json"]

# Test ControllerClient
client = ControllerClient(controller_url="https://controller:8000")
result = await client.register(registration_data)

assert result == exchange["response"]["json"]
```

### Connection lifecycle

```python
# Test lazy client creation
client = ControllerClient(controller_url="https://controller:8000")
assert client._http_client is None  # Not created yet

# First request triggers creation
await client.register(data)
assert client._http_client is not None  # Now created

# Subsequent requests reuse client
await client.send_heartbeat()
assert client._http_client is not None  # Same instance

# Cleanup closes client
await client.close()
assert client._http_client is None  # Cleaned up
```

### Parametrized error handling

```python
@pytest.mark.parametrize("error_exchange", [
    "registration/ssl-error.json",
    "heartbeat/timeout.json",
    "heartbeat/reconnect.json",
])
def test_network_errors(error_exchange):
    """Validate ControllerClient error handling."""
    # Implementation
```

## Beauty pass coverage

These fixtures validate improvements from commit 824bb96:

1. **Lazy initialization** - Client created on first request, not in `__init__`
2. **Connection pooling** - Same client reused across requests
3. **Resource cleanup** - close() method properly releases resources
4. **SSL configuration** - verify_ssl parameter controls TLS verification

## Edge case coverage

- **Network timeouts**: Controller doesn't respond in time
- **SSL failures**: Certificate validation errors
- **Connection reuse**: Verify pooling across multiple requests
- **Graceful degradation**: Handle transient network failures
- **Resource leaks**: Ensure httpx.AsyncClient properly closed

---

**Related**:

- Implementation: `src/crank/worker_runtime/registration.py`
- Tests: `tests/test_worker_runtime.py::TestControllerClient`
- Beauty pass: commit 824bb96, AGENT_CONTEXT.md
