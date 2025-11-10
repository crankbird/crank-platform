# Shutdown Scenario Fixtures

## Purpose

Test the `ShutdownTask` dataclass and `ShutdownHandler` improvements from commit 824bb96:

- Named shutdown tasks with metadata (description, timeout, tags)
- Per-task timeout enforcement
- Graceful vs forceful shutdown sequences
- Error recovery during shutdown
- Observability improvements (structured logging)

## Structure

```text
controller/shutdown/
├── README.md              # This file
├── valid/                 # Well-formed shutdown sequences
│   ├── graceful.json     # Standard clean shutdown
│   ├── multi-task.json   # Multiple tasks with dependencies
│   └── minimal.json      # Single task shutdown
├── edge-cases/            # Timing and error scenarios
│   ├── timeout.json      # Task exceeds timeout
│   ├── error.json        # Task raises exception
│   └── concurrent.json   # Parallel task execution
└── adversarial/           # Attack scenarios
    ├── infinite-loop.json  # Task never completes
    └── resource-leak.json  # Task holds resources
```

## Fixture schema

Each JSON file contains a shutdown scenario:

```json
{
  "scenario": "graceful",
  "description": "Standard worker shutdown with connection cleanup",
  "tasks": [
    {
      "name": "stop_heartbeat",
      "description": "Stop sending heartbeats to controller",
      "timeout_seconds": 5.0,
      "tags": ["controller", "network"],
      "expected_duration_ms": 50,
      "should_succeed": true
    },
    {
      "name": "close_connections",
      "description": "Close all active WebSocket connections",
      "timeout_seconds": 10.0,
      "tags": ["network", "cleanup"],
      "expected_duration_ms": 200,
      "should_succeed": true
    }
  ],
  "expected_total_duration_ms": 300,
  "expected_outcome": "success"
}
```

## Testing patterns

### Basic shutdown sequence

```python
from tests.data.loader import load_shutdown_scenario

scenario = load_shutdown_scenario("valid/graceful.json")
for task_spec in scenario["tasks"]:
    handler.register_shutdown_callback(
        name=task_spec["name"],
        callback=mock_callback,
        description=task_spec["description"],
        timeout=task_spec["timeout_seconds"],
        tags=task_spec["tags"],
    )

await handler.execute_shutdown()
```

### Timeout enforcement

```python
scenario = load_shutdown_scenario("edge-cases/timeout.json")
# Verify that tasks exceeding timeout are logged and continue
```

### Parametrized testing

```python
@pytest.mark.parametrize("scenario_file", [
    "valid/graceful.json",
    "valid/multi-task.json",
    "edge-cases/timeout.json",
])
def test_shutdown_scenarios(scenario_file):
    """Validate ShutdownHandler against various scenarios."""
    # Implementation
```

## Beauty pass coverage

These fixtures validate improvements from commit 824bb96:

1. **Named tasks** - `name` parameter replaces anonymous callbacks
2. **Metadata** - `description` and `tags` improve observability
3. **Per-task timeout** - Each task can specify its own timeout
4. **Structured logging** - Logs include task name, duration, success/failure

## Edge case coverage

- **Timeout handling**: Tasks that exceed timeout don't block shutdown
- **Error propagation**: Exceptions in one task don't prevent others
- **Concurrent execution**: Multiple tasks can run in parallel
- **Resource cleanup**: Ensure all resources released even on error
- **Graceful degradation**: System survives malformed task definitions

---

**Related**:

- Implementation: `src/crank/worker_runtime/lifecycle.py`
- Tests: `tests/test_worker_runtime.py::TestShutdownHandler`
- Beauty pass: commit 824bb96, AGENT_CONTEXT.md
