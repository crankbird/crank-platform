# Capability Schema Adversarial Fixtures

## Purpose

Test capability schema validation against malformed, malicious, and edge-case inputs.

## Structure

```text
capabilities/
├── README.md           # This file
├── valid/              # Well-formed capability definitions
│   └── custom.json    # Example custom capability
├── invalid/            # Schema violations
│   ├── missing-required.json     # Missing required fields
│   ├── wrong-types.json          # Type mismatches
│   └── invalid-version.json      # Bad version format
└── adversarial/        # Attack/edge cases
    ├── injection.json            # SQL/script injection attempts
    ├── unicode-exploits.json     # Unicode normalization attacks
    ├── oversized.json            # Extremely large payloads
    └── deeply-nested.json        # Deep nesting DoS attempt
```

## Provenance

- **Valid fixtures**: Hand-crafted examples based on `src/crank/capabilities/schema.py`
- **Invalid fixtures**: Common JSON schema violations
- **Adversarial fixtures**: Based on OWASP FuzzDB patterns (CC-BY 3.0)

## Testing patterns

### Valid capability validation

```python
from tests.data.loader import load_json_fixture

def test_custom_capability():
    fixture = load_json_fixture("capabilities/valid/custom.json")
    capability = CapabilityDefinition(**fixture)
    assert capability.id == fixture["id"]
```

### Invalid schema rejection

```python
@pytest.mark.parametrize("invalid_file", [
    "invalid/missing-required.json",
    "invalid/wrong-types.json",
])
def test_reject_invalid_capability(invalid_file):
    fixture = load_json_fixture(f"capabilities/{invalid_file}")
    with pytest.raises(ValidationError):
        CapabilityDefinition(**fixture)
```

### Adversarial input handling

```python
@pytest.mark.parametrize("adversarial_file", [
    "adversarial/injection.json",
    "adversarial/unicode-exploits.json",
])
def test_adversarial_capability_rejection(adversarial_file):
    """Ensure malicious inputs are safely rejected."""
    fixture = load_json_fixture(f"capabilities/{adversarial_file}")
    with pytest.raises((ValidationError, ValueError)):
        CapabilityDefinition(**fixture)
```

## Coverage goals

By Phase 2 completion:

- **10+ invalid schema cases** - Common validation failures
- **5+ adversarial cases** - Security-focused edge cases
- **Zero crashes** - All malformed input handled gracefully

---

**Related**:

- Schema implementation: `src/crank/capabilities/schema.py`
- Tests: `tests/test_capability_schema.py`
- Roadmap: `docs/planning/test-data-corpus-roadmap.md` (Issue #33)
