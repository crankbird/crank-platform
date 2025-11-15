# Changelog

All notable changes to the Crank Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Documentation reorganization: standardized directory structure with clear READMEs
- Moved scattered docs to appropriate subdirectories

## [0.1.0] - 2025-11-15

### Added
- Unified security module (`src/crank/security/`) consolidating certificate management
- Automatic HTTPS+mTLS for all workers via `WorkerApplication.run()` pattern
- Clean minimal worker pattern (3-line main function)
- Certificate Authority service (port 9090)
- Worker runtime foundation (`src/crank/worker_runtime/`)
- Capability schema system (`src/crank/capabilities/`)
- Base worker Docker image eliminating 40+ lines per worker
- Hybrid deployment support (macOS Metal native execution)

### Changed
- All 9 workers migrated to `WorkerApplication` base class
- 40.4% code reduction in worker implementations while adding features
- Docker v28 compatibility with strict file ownership

### Removed
- 675 lines of duplicated security code
- Legacy manual SSL configuration patterns
- Scattered certificate management approaches

## [0.0.1] - 2025-11-10

### Added
- Initial controller/worker architecture (Phases 0-2)
- Email classification and parsing workers
- Document conversion worker
- Image classification (CPU and GPU)
- Streaming data processing worker
- Philosophical analyzer and zettel management workers
- Certificate signing service
- Basic test coverage (64 tests passing)

### Documentation
- Architecture documentation (controller/worker model)
- Requirements traceability system
- Development guides for GPU setup, type checking, linting
- Operations runbooks for deployment and monitoring

[Unreleased]: https://github.com/crankbird/crank-platform/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/crankbird/crank-platform/releases/tag/v0.1.0
[0.0.1]: https://github.com/crankbird/crank-platform/releases/tag/v0.0.1
