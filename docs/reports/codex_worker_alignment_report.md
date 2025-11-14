## Codex Worker Alignment Report

**Purpose.** Assess every current `WorkerApplication` implementation against the combined Codex/Sonnet best-practice pattern (capability scope, domain separation + extension hooks, API/route style, storage metadata decisions, and dual-layer testing) and highlight refactoring opportunities ahead of the next Sonnet/Codex comparison cycle.

### Summary Matrix

| Worker | Alignment Snapshot | Key Deviations / Opportunities |
| --- | --- | --- |
| `services/crank_codex_zettel_repository.py` | Baseline reference implementation with dataclass domain model, explicit extension hooks, JSON front matter, explicit route binding, and CLI `--test` harness | Use as the “north star” pattern for other ingestion-style workers |
| `services/crank_sonnet_zettel_manager.py` | Strong alignment: schema-first models, engine class, multiple endpoints, YAML front matter, comprehensive `--test` flow | Clarify when to use YAML vs JSON front matter and document how retrieval/publishing hooks should integrate with controller workflows |
| `services/crank_hello_world.py` | Demonstrates almost every best-practice element (engine class, explicit binding, `--test` mode) | Add explicit extension hooks (e.g., `_transform_message`) so assistants see how to scaffold optional behaviors |
| `services/crank_doc_converter.py` | Contract + engine separation is solid, but infra surfaced only through form uploads | Add structured request models, introduce repository abstraction for converted artefacts, and supply a lightweight `--test` harness |
| `services/crank_email_classifier.py` | Multi-classification logic lives in one mega-endpoint | Split capability scopes (spam/bill/etc.) or add routing hints, expose extension hooks per classifier, and add domain-level tests |
| `services/crank_email_parser.py` | Multiple endpoints with explicit binding, but storage/reporting is ad-hoc | Introduce metadata strategy for parsed archives, create domain service for analytics, and provide CLI validation path |
| `services/crank_streaming.py` | Covers SSE/WebSocket cases with explicit routes | Extract connection/orchestration logic into a service for easier extension and add simulation tests (e.g., mocked WebSocket driver) |
| `services/crank_philosophical_analyzer.py` | Provides meaningful analysis but diverges on routing + typing | Replace decorator usage, adopt Pydantic request model instead of raw dict, and expose extension points for future analyzer modes |
| `services/crank_image_classifier_advanced.py` & `services/relaxed-checking/crank_image_classifier.py` | Tier-D legacy workers that predate WorkerApplication adoption | Migrate to WorkerApplication, replace decorator-style routing, add capability definitions + CLI tests, and factor GPU-specific logic into a service layer |

### Detailed Findings

#### Codex Zettel Repository (reference)
- Domain layering and extension hooks (`ZettelRepository`, `CodexZettelService`, `_generate_title`, `plan_publication`) establish the intended pattern (`services/crank_codex_zettel_repository.py:29`-`services/crank_codex_zettel_repository.py:205`).
- Explicit binding and lifecycle logging follow the runtime guidance (`services/crank_codex_zettel_repository.py:230`-`services/crank_codex_zettel_repository.py:254`).
- CLI `--test` switch enables domain-only validation without FastAPI (`services/crank_codex_zettel_repository.py:275`-`services/crank_codex_zettel_repository.py:289`).

#### Sonnet Zettel Manager
- Schema-first approach plus engine abstraction (`services/crank_sonnet_zettel_manager.py:345`-`services/crank_sonnet_zettel_manager.py:408`) already aligns with the pattern, and explicit extension comments exist (`services/crank_sonnet_zettel_manager.py:320`-`services/crank_sonnet_zettel_manager.py:337`).
- Recommendation: document when YAML metadata is preferred over JSON to match the “storage format decision” criterion, and add hooks equivalent to Codex’s `_generate_title` to centralize future AI-powered enrichments.

#### Hello World Worker
- Serves as a teaching example with a clean engine (`services/crank_hello_world.py:88`-`services/crank_hello_world.py:165`), explicit binding (`services/crank_hello_world.py:217`-`services/crank_hello_world.py:219`), and robust `--test` mode (`services/crank_hello_world.py:255`-`services/crank_hello_world.py:279`).
- Opportunity: add placeholder methods (e.g., `_apply_transformations`) so assistants practice leaving hook points even in trivial workers.

#### Document Converter
- Conversion logic is isolated inside `DocumentConverter` (`services/crank_doc_converter.py:36`-`services/crank_doc_converter.py:151`), and endpoints follow explicit binding (`services/crank_doc_converter.py:174`-`services/crank_doc_converter.py:249`).
- Deviations:
  - No structured request/response objects for uploads, making schema evolution harder.
  - Lack of extension hooks for future auto-formatting/metadata; everything is embedded in the FastAPI handler.
  - Missing CLI/domain-level `--test` harness prevents quick regression checks.
- Refactor ideas: introduce a `ConversionPlan` dataclass, add `_select_engine`/`_post_process` hooks, and port the Codex-style CLI smoke test.

#### Email Classifier
- All classification modes are multiplexed through one endpoint (`services/crank_email_classifier.py:352`-`services/crank_email_classifier.py:465`), which conflicts with the “capability scope” guidance from the comparison study.
- Domain logic (`SimpleEmailClassifier`) mixes multiple behaviors without extension points, so assistants have no obvious place to add new classifiers.
- Recommended actions: split the capability into sub-capabilities (spam, billing, sentiment), expose per-classifier strategy hooks, and create a domain-only test harness similar to Codex/HelloWorld for deterministic validation.

#### Email Parser
- Uses explicit binding (`services/crank_email_parser.py:385`-`services/crank_email_parser.py:438`) but lacks an ingestion repository or metadata format decision, so outputs stay ad-hoc dicts.
- No CLI `--test`, and analytics helpers (`services/crank_email_parser.py:332`-`services/crank_email_parser.py:358`) are private methods without extension guidance.
- Opportunity: add a `ParsedArchive` model with JSON/YAML serialization, include hooks for similarity/publishing (aligned with the zettel workers), and add a `--test` path to exercise parsing without FastAPI.

#### Streaming Worker
- Provides rich real-time functionality with explicit route binding (`services/crank_streaming.py:80`-`services/crank_streaming.py:211`), but couples orchestration logic directly to the worker.
- Missing extension hooks for alternative transport layers or batching, and no automated simulation/test harness.
- Refactor idea: introduce a `StreamingCoordinator` service that handles `text_stream_generator`, WebSocket broadcasting, etc., and create a CLI test that replays canned messages (even without network sockets) to validate the service methods.

#### Philosophical Analyzer
- Still uses decorator syntax (`services/crank_philosophical_analyzer.py:191`) despite the route-binding guidance.
- Accepts raw `dict[str, Any]` instead of Pydantic models, making schema alignment/manual validation harder.
- Lacks explicit extension methods for additional analyzer modes, even though comments hint at future readiness.
- Recommended: switch to explicit binding, introduce request/response Pydantic models, add hook methods (e.g., `_preprocess_context`, `_postprocess_markers`), and keep the existing `--test` harness (`services/crank_philosophical_analyzer.py:253`-`services/crank_philosophical_analyzer.py:265`) as the foundation for regression checks.

#### Image Classifier Workers (Advanced + Relaxed-Checking)
- Both GPU and CPU versions still run outside the WorkerApplication pattern, so controller registration, health checks, and TLS handling are bespoke.
- Route handlers rely on decorators (e.g., `services/crank_image_classifier_advanced.py:425`) and mix FastAPI concerns with model inference code.
- No capability definitions exist for these workers, so future assistants cannot reason about contracts or compose them with other services.
- Neither worker offers the Codex/Sonnet dual-testing approach (only ad-hoc scripts), and storage metadata for classification outputs is absent.
- Recommended remediation:
  1. Create `IMAGE_CLASSIFICATION` capability entries (GPU/non-GPU variants) and wire them into new WorkerApplication subclasses.
  2. Extract inference logic into dedicated service classes with extension hooks for batching/quantization.
  3. Standardize request/response Pydantic models plus JSON/YAML front matter for result metadata.
  4. Add CLI `--test` paths that load lightweight fixtures so regressions are caught without GPU runtime.

### Next Steps
1. Prioritize refactors starting with workers that actively power pipelines (Email Classifier, Document Converter, Philosophical Analyzer).
2. Apply the Codex reference pattern incrementally: introduce domain service classes, add extension hooks, then wire lightweight `--test` commands.
3. After Codex+Sonnet both deliver reports, update the worker development guide with any archetype-specific allowances discovered during refactors.
