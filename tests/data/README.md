# Test Data Corpus

> **Purpose**: Deterministic, adversarial-friendly fixtures for regression testing worker runtime, capability schema, and ML workers.

## Directory structure

```text
tests/data/
├── README.md                    # This file
├── certs/                       # Certificate fixtures (PEM files)
│   ├── README.md               # Certificate generation/provenance
│   ├── valid/                  # Valid certificate bundles
│   ├── invalid/                # Malformed/corrupted certificates
│   └── generate_fixtures.sh   # Regeneration script
├── controller/                  # Mock controller exchanges
│   ├── registration/           # Registration request/response pairs
│   ├── heartbeat/              # Heartbeat scenarios
│   └── shutdown/               # Shutdown sequences
├── capabilities/                # Capability definition fixtures
│   ├── valid/                  # Well-formed capability specs
│   ├── invalid/                # Schema violations
│   └── adversarial/            # Edge cases (injection, overflow)
└── workers/                     # Worker-specific test data
    ├── streaming/              # WebSocket/SSE fixtures
    ├── email/                  # Email corpus (builds on classifier_test_emails.json)
    └── image/                  # Image fixtures for classifier
```

## Provenance and licensing

All test data in this directory follows strict licensing requirements:

### License types

- **Generated fixtures**: MIT (same as crank-platform)
- **Public domain**: Project Gutenberg text samples, NIST reference data
- **Permissive licensed**: JSON Schema Test Suite (MIT), OWASP FuzzDB (CC-BY)
- **Original**: mkcert-generated certificates, synthetic payloads

### External sources

- **JSON Schema Test Suite**: MIT License - <https://github.com/json-schema-org/JSON-Schema-Test-Suite>
- **OWASP FuzzDB**: CC-BY 3.0 - <https://github.com/fuzzdb-project/fuzzdb>
- **mkcert**: BSD 3-Clause - <https://github.com/FiloSottile/mkcert>

### Attribution

When using external corpora, each subdirectory contains a `SOURCE.md` documenting:

- Origin URL and version/commit
- License terms
- Date fetched
- Modifications made

## Usage in tests

### Certificate fixtures

```python
from tests.data.loader import load_cert_bundle

# Load valid certificate bundle
cert_bundle = load_cert_bundle("valid/platform-cert.pem")

# Load corrupted certificate for error testing
with pytest.raises(ValueError):
    load_cert_bundle("invalid/truncated-cert.pem")
```

### Controller exchanges

```python
from tests.data.loader import load_controller_exchange

# Load registration request/response pair
exchange = load_controller_exchange("registration/successful.json")
assert exchange["request"]["worker_id"] == "test-worker-1"
```

### Parametrization

```python
import pytest
from tests.data.loader import list_fixtures

@pytest.mark.parametrize("cert_file", list_fixtures("certs/invalid"))
def test_certificate_validation(cert_file):
    """Ensure CertificateBundle rejects malformed certificates."""
    # Test implementation
```

## CI/CD considerations

- **Size limit**: Default fixtures ≤10 MB per module
- **Extended corpus**: Heavy datasets gated by `CRANK_RUN_EXTENDED_FIXTURES=1`
- **Freshness**: CI job validates external corpus checksums monthly
- **Determinism**: All fixtures versioned in git (no dynamic downloads in CI)

## Maintenance

### Adding new fixtures

1. Place in appropriate subdirectory
2. Document provenance in `SOURCE.md` if external
3. Update `tests/data/loader.py` if new category
4. Add parametrized test using fixture
5. Verify CI size budget (<10 MB total)

### Regenerating certificates

```bash
cd tests/data/certs
./generate_fixtures.sh  # Creates fresh mkcert bundles
```

### Corpus refresh

```bash
# Fetch external corpora with version pinning
python scripts/fetch_test_corpus.py --verify-checksums
```

## Coverage goals

By Phase 4 completion:

- **80% parametrization**: Existing tests use corpus fixtures
- **10+ adversarial cases**: Each module has attack/edge inputs
- **0 ad-hoc fixtures**: All test data lives in this directory
- **100% attribution**: Every external source documented

---

**Related documents**:

- Roadmap: `docs/planning/test-data-corpus-roadmap.md`
- Issues: GitHub #32-36 (test corpus implementation)
- Test suite: `tests/test_worker_runtime.py`, `tests/test_capability_schema.py`
