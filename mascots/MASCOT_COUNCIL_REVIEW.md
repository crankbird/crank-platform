# Mascot Council Repository Review

_Run date: 2025-11-10 (update if regenerated)_  
Scope: Root repository (`crank-platform`)

## 🐰 Wendy the Zero-Trust Security Bunny

**Validated Defenses**
- Parametrized adversarial fixtures guard the capability schema against SQLi, Unicode exploitation, and other Bobby Tables tricks (`tests/test_capability_schema.py:364-405`).  
- Test corpus documentation codifies adversarial fixture provenance so red-team inputs remain repeatable (`tests/data/README.md:3-55`).

**Critical Findings (OWASP A02/A03/A10)**
- Multiple workers still instantiate `httpx.AsyncClient(verify=False)` even when a CA bundle exists, violating NIST SP 800-53 SC-8 requirements for encrypted channels (`services/crank_doc_converter.py:339-344`).
- Compose health checks lean on `curl -k https://localhost/...`, disabling certificate validation in every container by default (`docker-compose.development.yml:23-65`).
- Security requirements remain untested (0/2 covered) inside the traceability matrix, leaving REQ-SEC gaps invisible to CI (`docs/planning/REQUIREMENTS_TRACEABILITY.md:105-116`).

**Security Orders**
1. Thread the existing `CertificateManager` PEM paths into the worker HTTP clients and end the `verify=False` default; enforce mTLS per REQ-SEC-002.  
2. Replace every `curl -k` health check with CA-backed verification and fail fast if TLS material is missing.  
3. Backfill at least two REQ-SEC-tagged pytest cases (e.g., controller registration authz and certificate rotation) so the traceability matrix is no longer redlined.

## 🦙 Kevin the Portability Llama

**Portability Wins**
- `scripts/dev-universal.sh` already fingerprints macOS/Linux/WSL and adapts prerequisite messaging, a solid baseline for multi-host development (`scripts/dev-universal.sh:35-141`).  
- Service manifests inject configuration via environment variables rather than hardcoded literals (`docker-compose.development.yml:42-155`).

**Portability Sins**
- The dev harness hard-depends on the Docker CLI/daemon; no abstraction exists for containerd, Podman, or remote runtimes, so “write once, run anywhere” collapses on clusters lacking Docker (`scripts/dev-universal.sh:86-141`).  
- Workers such as the document converter still default to baked-in hostnames like `https://platform:8443`, rather than using discovery or per-environment configuration injection (`services/crank_doc_converter.py:78-86`).

**Runtime Directives**
1. Extract container orchestration behind an adapter (detect Docker vs. `nerdctl`/`podman` at runtime) before Phase 1 hybrid deployments.  
2. Push worker endpoint defaults into environment-driven config (or controller discovery) so binaries run unmodified on Kubernetes, bare metal, or local compose.  
3. Add portability smoke tests that boot via `podman compose` or kind to verify the adapter works off-Docker.

## 🐩 Bella the Modularity Poodle

**Separation Merits**
- `WorkerApplication` centralizes lifecycle, registration, health, and certificate concerns so workers can focus on business endpoints with clean hook points (`src/crank/worker_runtime/base.py:1-198`).

**Coupling Alerts**
- The document converter bypasses the shared worker runtime, re-implements registration models, and wires FastAPI routes manually, inviting divergence from controller expectations (`services/crank_doc_converter.py:31-178`).  
- Mascot documentation advertises a `mascots/bella/` suite, but no such module exists yet, so modularity regressions go unchecked (`mascots/README.md:65-134`).

**Refinement Checklist**
1. Port `CrankDocumentConverter` (and sibling legacy workers) onto `WorkerApplication` + `ControllerClient` to regain consistent lifecycle handling.  
2. Stand up Bella’s promised modularity test harness so dependency graphs and interface contracts are evaluated automatically before merges.  
3. Document planned extension points (route helpers, middleware hooks) so future workers can stay within the shared runtime rather than forking it.

## 🦅 Oliver the Anti-Pattern Eagle

**Recent Triumphs**
- The anti-pattern elimination log confirms lazy initialization, DRY fixtures, and typed factories already landed in the worker runtime (`mascots/oliver/ANTI_PATTERN_ELIMINATION.md:5-167`).

**New Targets**
- Logging statements inside the document converter interpolate braces without `f`-strings, resulting in literal `{file.filename}` text and lost diagnostics (`services/crank_doc_converter.py:158-177`).  
- That same file redefines `WorkerRegistration` and heartbeat logic that already exist in `crank.worker_runtime.registration`, a textbook duplication smell (`services/crank_doc_converter.py:31-178` vs. `src/crank/worker_runtime/registration.py:24-183`).

**Remediation Flight Plan**
1. Normalize all logging calls to actual formatted strings (or `%s` patterns) so telemetry is trustworthy.  
2. Delete the bespoke registration classes and reuse the shared runtime primitives to avoid future shotgun surgery when protocols evolve.  
3. Add Ruff or custom lint rules that flag literal braces in logging to prevent regressions.

## 🐌 Gary the Methodical Snail

**Context Kept**
- The test data loader centralizes fixture IO with docstrings, and the corpus README tracks provenance/licensing, giving future maintainers the “why” alongside the “what” (`tests/data/loader.py:1-142`, `tests/data/README.md:3-130`).

**Context Debt**
- Requirement coverage stalls at 43%, and both security and protocol categories remain entirely untested (`docs/planning/REQUIREMENTS_TRACEABILITY.md:101-117`). Future maintainers lack guidance on which specs are actually enforced.

**Slow-and-Steady Actions**
1. Extend the traceability matrix with the next tranche of requirements (start with REQ-SEC and Universal Protocol Support) and pair each with parametrized tests.  
2. Capture ADRs for the controller/worker refactor decisions now reflected in `WorkerApplication`, so new hires understand the rationale without archeology.  
3. Automate extraction of `REQUIREMENT:`/`VALIDATES:` tags to keep coverage metrics live in CI dashboards.

---

_Prepared collaboratively by the Mascot Council. Each persona stands ready to dive deeper on request._
