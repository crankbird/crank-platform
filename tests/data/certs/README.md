# Certificate Test Fixtures

## Purpose

Test the `CertificateBundle` dataclass and `CertificateManager` against:

- Valid certificate bundles (mTLS pairs)
- Malformed PEM structures
- Corrupted/truncated files
- Missing components (cert without key, etc.)

## Generation

All certificates in `valid/` are generated using `mkcert` for local development:

```bash
./generate_fixtures.sh
```

This creates:

- Self-signed CA certificates
- Valid client/server certificate pairs
- Expired certificates (for time-based testing)

## Structure

```text
certs/
├── README.md                # This file
├── generate_fixtures.sh     # Regeneration script
├── valid/                   # Well-formed certificates
│   ├── ca.crt              # Certificate authority
│   ├── ca.key              # CA private key
│   ├── platform.crt        # Server certificate
│   ├── platform.key        # Server private key
│   ├── client.crt          # Client certificate
│   └── client.key          # Client private key
└── invalid/                 # Malformed fixtures
    ├── truncated-cert.pem  # Incomplete PEM block
    ├── corrupted-key.pem   # Invalid key data
    ├── wrong-format.txt    # Non-PEM file
    └── missing-header.pem  # PEM without BEGIN marker
```

## Provenance

- **Generator**: mkcert v1.4.4 (BSD 3-Clause)
- **URL**: <https://github.com/FiloSottile/mkcert>
- **Generated**: 2025-11-10
- **License**: Test fixtures are MIT (same as crank-platform)

## Testing patterns

### Valid bundle loading

```python
from tests.data.loader import load_cert_bundle

bundle = load_cert_bundle("valid/platform")  # Loads platform.crt + platform.key
assert bundle.cert_path.exists()
assert bundle.key_path.exists()
```

### Error handling

```python
import pytest
from crank.worker_runtime import CertificateBundle

with pytest.raises(ValueError, match="Missing BEGIN CERTIFICATE"):
    CertificateBundle(
        cert_path=Path("tests/data/certs/invalid/missing-header.pem"),
        key_path=Path("tests/data/certs/valid/platform.key"),
    )
```

### Parametrized validation

```python
@pytest.mark.parametrize("invalid_cert", [
    "truncated-cert.pem",
    "corrupted-key.pem",
    "wrong-format.txt",
    "missing-header.pem",
])
def test_certificate_validation(invalid_cert):
    """CertificateBundle should reject malformed certificates."""
    # Implementation uses beauty pass validation logic
```

## Beauty pass coverage

These fixtures specifically test the improvements from commit 824bb96:

1. **Automatic validation** - Invalid PEM structures trigger clear errors
2. **Type safety** - CertificateBundle enforces Path types
3. **to_uvicorn_config()** - Converts bundle to SSL config dict
4. **Human-readable repr** - Debug output shows file paths

---

**Related**:

- Implementation: `src/crank/worker_runtime/security.py`
- Tests: `tests/test_worker_runtime.py::TestCertificateManager`
- Beauty pass: commit 824bb96, AGENT_CONTEXT.md
