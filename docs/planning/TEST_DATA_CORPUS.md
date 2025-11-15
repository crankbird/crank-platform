# Test Data Corpus Plan

**Type**: Active Plan
**Status**: In Progress
**Temporal Context**: Ongoing Work (Implementation Roadmap)
**Owner**: Platform Quality
**Last Updated**: November 14, 2025

## Why we need this

- Refactors currently rely on ad-hoc inputs (Wikipedia downloads, synthetic stubs), which miss real-world failures.
- We need deterministic, adversarial-friendly fixtures to regression-test the controller, worker runtime, capability schema, and ML workers.
- Shared corpora let every module reuse the same edge cases without re-implementing generators.

## Guiding principles

1. **License clarity**: Prefer public-domain or permissively licensed corpora (MIT/Apache/CC0). Track provenance in `tests/data/README.md`.
2. **Deterministic ingestion**: Large datasets should be fetched via scripted tooling (`scripts/fetch_test_corpus.py`) with checksums, not manual downloads.
3. **Adversarial coverage**: Every corpus should include “Little Bobby Tables” style inputs (SQL/meta injection, binary blobs, truncated files).
4. **Module scoping**: Tag each artifact with the subsystem(s) it covers (schema, worker-runtime, streaming, email, image).
5. **CI friendly**: Keep default fixtures ≤10 MB per module; heavier datasets can be opt-in via env flag (e.g., `CRANK_RUN_EXTENDED_FIXTURES=1`).

## Proposed milestones

| Phase | Goal | Deliverables |
| --- | --- | --- |
| 0 – Bootstrap | Stand up shared structure + quick wins | `tests/data/` layout, README, automated fetch script, first two corpora wired into pytest |
| 1 – Adversarial schema suite | Stress capability schema + controller contracts | JSON Schema Test Suite integration, malformed capability definitions, signed/unsigned CSR samples |
| 1a – BDD Integration (Golden) | Integrate BDD framework with philosophical analysis | pytest-bdd setup, philosophical analysis feature tests, golden gherkins integration |
| 2 – Worker runtime resilience | Exercise lifecycle + heartbeat | Recorded controller exchanges, shutdown edge cases, corrupted heartbeat payloads |
| 3 – Domain corpora | Rich inputs for email/streaming/image workers | Sanitized public emails, audio/text streams, reference images with annotations |
| 3a – Philosophical Test Data | Corpus for philosophical analysis validation | Curated text samples for authentic vs. performed thinking detection, philosophical DNA marker test cases |
| 4 – Continuous expansion | Automation + governance | Checklist for new modules, CI job to validate corpus freshness, issue labels for coverage gaps |

## Quick wins (public domain sources)

- **Capability/JSON validation**
  - JSON Schema Test Suite (MIT) → feed into `tests/test_capability_schema.py` to cover required/optional field enforcement.
  - NIST Cybersecurity reference data (public domain) → use for capability IDs/descriptions requiring special characters.

- **Adversarial text inputs**
  - OWASP FuzzDB payload snippets (creative commons) → seed worker routing + email parsing tests with SQL/script injections.
  - Project Gutenberg sentence extracts (public domain) for multilingual streaming/email tests, including RTL scripts.

- **Certificate/crypto fixtures**
  - mkcert-generated cert bundles checked into `tests/data/certs/` with README + regeneration script; combine with intentionally corrupted PEM files to validate `CertificateManager`.

- **Image/video sanity cases**
  - COCO sample subset (CC-BY) and Unsplash public-domain thumbnails; store resized versions ≤256 KB to keep CI light.

- **Philosophical analysis test data (Golden integration)**
  - Curated text samples from docs/knowledge/ for philosophical DNA marker validation
  - Semantic schema test cases from `src/crank/capabilities/semantic_config.py`
  - BDD feature files archived in `archive/2025-11-14-golden-repository/golden/gherkins/`

## Integration with existing test suite

**Current coverage** (as of Phase 1 completion):

- 24 capability schema tests (`tests/test_capability_schema.py`) - validates 6 standard capabilities + PHILOSOPHICAL_ANALYSIS
- 24 worker runtime tests (`tests/test_worker_runtime.py`) - covers WorkerApplication, ControllerClient, HealthCheckManager, ShutdownHandler, CertificateManager
- BDD framework integration (`tests/bdd/`) - pytest-bdd setup with philosophical analysis feature tests
- 4 streaming worker tests (`tests/test_streaming_worker.py`) - validates migrated crank_streaming.py
- Email classifier fixtures (`tests/fixtures/classifier_test_emails.json`) - existing test data for ML validation

**Integration strategy**: Corpus will extend parametrization in these existing modules rather than creating parallel test files. New fixtures feed into pytest parametrized tests to increase coverage without duplicating infrastructure.

## Worker-specific corpus needs

Based on migrated workers and upcoming targets:

- **Streaming worker** (`services/crank_streaming.py` - 292 lines):
  - WebSocket frame sequences (text, binary, ping/pong, close frames)
  - SSE reconnection scenarios (dropped connections, malformed event streams)
  - Concurrent connection stress cases (100+ simultaneous WebSocket clients)
  - Binary blob streams to test non-text handling

- **Email classifier** (`services/crank_email_classifier.py` - 480 lines):
  - Build on existing `classifier_test_emails.json` foundation
  - Add non-Latin scripts (Arabic RTL, Chinese, Cyrillic) for language detection
  - HTML edge cases (deeply nested tables, CSS injection attempts)
  - Malformed MIME structures (missing boundaries, invalid encodings)
  - Adversarial spam patterns (obfuscation, zero-width characters)

- **Image classifier** (pending migration):
  - COCO subset for standard validation
  - Adversarial images (pixel attacks, truncated files, corrupted headers)
  - Edge dimensions (1x1, 10000x1, non-square aspect ratios)

- **Document converter** (pending migration):
  - Multi-page PDFs with various encodings
  - Office formats (DOCX, XLSX) with macros and embedded objects
  - Corrupted file headers to test error handling

## Proposed directory structure

```text
tests/data/
├── README.md                          # Licensing table + provenance tracking
├── dataset.yaml                       # Template for per-module metadata
├── schema/                            # Capability schema validation
│   ├── json-schema-test-suite/       # Vendored test suite (MIT)
│   └── adversarial-capabilities/     # Custom edge cases
├── worker-runtime/                    # Lifecycle + registration
│   ├── heartbeat-payloads/           # Valid + corrupted heartbeats
│   ├── lifecycle-scenarios/          # Startup, shutdown, crash recovery
│   └── controller-exchanges/         # Recorded registration flows
├── email/                             # Email classification
│   ├── spam-samples/                 # OWASP FuzzDB + curated spam
│   ├── multilingual/                 # Project Gutenberg extracts
│   └── mime-edge-cases/              # Malformed structures
├── streaming/                         # WebSocket/SSE
│   ├── websocket-fixtures/           # Frame sequences
│   └── sse-scenarios/                # Event stream recordings
├── images/                            # Image classification
│   ├── coco-subset/                  # COCO samples (≤256 KB each)
│   └── adversarial/                  # Corrupted + attack images
├── documents/                         # Document conversion
│   └── office-samples/               # PDF, DOCX, XLSX samples
└── certs/                             # Certificate validation
    ├── mkcert-generated/             # Valid cert bundles
    ├── corrupted/                    # Intentionally broken PEMs
    └── regenerate.sh                 # Reproducible generation
```

## Actionable issue breakdown

1. **Issue: "Establish shared test data structure"**
   - **Milestone**: Phase 1 - Worker Migration (support current streaming/email refactors)
   - **Deliverables**:
     - Create `tests/data/` directory structure per layout above
     - Add `tests/data/README.md` with licensing table and provenance tracking
     - Create `tests/data/dataset.yaml` template for per-module metadata
     - Add utility module `tests/utils/data_loader.py` with fixture path resolution
   - **Success criteria**: Any worker test can import data_loader and resolve fixtures by module name

2. **Issue: "Integrate JSON Schema Test Suite into capability tests"**
   - **Milestone**: Phase 1 - Worker Migration
   - **Deliverables**:
     - Vendor minimal JSON Schema Test Suite subset (valid + invalid cases) to `tests/data/schema/`
     - Parametrize existing `tests/test_capability_schema.py` to iterate over vendored fixtures
     - Add test case counting: "Covered X/Y schema edge cases"
   - **Success criteria**: Capability schema tests run against ≥50 standardized JSON validation cases

3. **Issue: "Seed adversarial text corpus for worker runtime"**
   - **Milestone**: Phase 1 - Worker Migration
   - **Deliverables**:
     - Pull curated payloads from OWASP FuzzDB (SQL injection, script injection, unicode exploits)
     - Add to `tests/data/worker-runtime/adversarial-payloads/`
     - Extend `tests/test_worker_runtime.py` with parametrized adversarial cases for:
       - HealthStatus transitions with malformed inputs
       - Controller registration with injection attempts
       - Heartbeat payloads with unexpected data types
   - **Success criteria**: Worker runtime rejects ≥20 adversarial inputs gracefully (no crashes, proper error responses)

4. **Issue: "Add deterministic certificate fixtures"**
   - **Milestone**: Phase 1 - Worker Migration
   - **Deliverables**:
     - Create `tests/data/certs/regenerate.sh` script to generate cert/key/CA bundle via mkcert
     - Add intentionally corrupted variants (truncated PEM, wrong encoding, expired certs)
     - Store fixtures in `tests/data/certs/` with README explaining each variant
     - Refactor `tests/test_worker_runtime.py::TestCertificateManager` to use fixtures instead of temp files
   - **Success criteria**: Certificate tests are fully deterministic (no random temp file generation), ≥5 corruption scenarios validated

5. **Issue: "Document corpus expansion plan and success metrics"**
   - **Milestone**: Phase 2 - Base Worker Image
   - **Deliverables**:
     - Add worker-specific corpus checklist to this roadmap
     - Define success metrics: target coverage %, minimum adversarial cases per category
     - Create GitHub Project "Test Corpus Initiative" to track corpus additions
     - Add corpus requirement to worker migration PR template
   - **Success criteria**: Every future worker migration PR references corpus (even if adding stub fixtures)

## Success metrics

- **Coverage target**: Each module (schema, worker-runtime, streaming, email) achieves ≥80% branch coverage with corpus-backed tests
- **Adversarial minimum**: Each module tests ≥10 unique adversarial/edge cases from corpus
- **Regression detection**: Corpus catches ≥1 previously unknown bug per sprint (validates corpus value)
- **CI performance**: Full corpus run completes in ≤2 minutes (default fixtures only; extended fixtures allowed ≤10 min)

## Implementation steps

1. Create GitHub issues from breakdown above using `gh issue create`
2. Assign milestone "Phase 1: Worker Migration" (#28) to first four issues so they support current refactors
3. Link corpus issues to worker migration PRs for traceability
4. After first two issues land, evaluate impact on test confidence before scaling up

Once bootstrap lands, we can layer in larger corpora (e.g., Enron email subset) behind opt-in flags and start measuring coverage deltas per module.
