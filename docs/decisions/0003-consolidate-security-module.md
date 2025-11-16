# ADR-0003: Consolidate Security Module

**Status**: Accepted
**Date**: 2025-11-15
**Deciders**: Platform Team
**Technical Story**: Security Consolidation (Issue #19)

## Context and Problem Statement

After implementing mTLS (ADR-0002), we had 675 lines of duplicated security code scattered across 9 workers. Each worker manually configured certificates, SSL contexts, and uvicorn settings. How should we eliminate this duplication while maintaining flexibility?

## Decision Drivers

- DRY principle: 675 lines of duplicate code
- Type safety: Manual SSL configuration error-prone
- Consistency: All workers should have identical security setup
- Developer experience: Security should be automatic, not manual
- Docker compatibility: Certificate paths vary by environment

## Considered Options

- **Option 1**: Unified `crank.security` module with `WorkerApplication.run()` pattern
- **Option 2**: Shared base class with manual SSL configuration
- **Option 3**: Security library but workers still configure uvicorn manually

## Decision Outcome

**Chosen option**: "Unified `crank.security` module with `WorkerApplication.run()` pattern", because it provides the best developer experience while ensuring consistent security across all workers.

### Positive Consequences

- 675 lines of deprecated code removed
- Clean minimal worker pattern: 3-line main function
- Automatic HTTPS+mTLS for all workers
- Environment-aware certificate path detection
- Impossible to bypass security (it's automatic)
- Reference implementation (`crank_hello_world.py`) is trivially simple

### Negative Consequences

- Workers must subclass `WorkerApplication`
- Less flexibility for custom SSL configurations
- Migration effort for existing workers (but one-time cost)

## Pros and Cons of the Options

### Option 1: Unified Security Module with `.run()` Pattern

Central security module, workers call `.run()` for automatic setup.

**Pros:**
- Eliminates all code duplication
- Impossible to configure security incorrectly
- Clean developer experience (3-line main function)
- Environment-aware path detection
- Easy to extend with new security features
- Reference implementation is minimal

**Cons:**
- Workers must use `WorkerApplication` base class
- Custom SSL configs require module changes
- Migration effort for legacy workers

### Option 2: Shared Base Class with Manual Configuration

Base class provides methods, workers configure SSL themselves.

**Pros:**
- More flexibility for custom configurations
- Workers control their own setup
- Easier to migrate incrementally

**Cons:**
- Still allows security misconfiguration
- Workers must understand SSL/certificates
- Code duplication reduced but not eliminated
- Inconsistent security setup across workers

### Option 3: Security Library Without Auto-Setup

Library functions available, workers call them manually.

**Pros:**
- Maximum flexibility
- No enforced patterns
- Easy to adopt incrementally

**Cons:**
- Security still optional (can be bypassed)
- Each worker duplicates setup code
- Inconsistent patterns across codebase
- Easy to misconfigure
- Doesn't solve the duplication problem

## Links

- [Refines] ADR-0002 (Adopt mTLS)
- [Related to] ADR-0001 (Controller/Worker model)
- [Related to] [docs/development/WORKER_SECURITY_PATTERN.md]

## Implementation Notes

**Security Module Structure**:

```
src/crank/security/
  __init__.py              # Public API
  certificate_authority.py # CA service
  certificate_manager.py   # Worker cert bootstrap
  ssl_config.py           # SSL context creation
  paths.py                # Environment-aware paths
  heartbeat.py            # Health reporting
  types.py                # Type definitions
  constants.py            # Configuration
```

**Clean Worker Pattern**:

```python
def main() -> None:
    port = int(os.getenv("WORKER_HTTPS_PORT", "8500"))
    worker = MyWorker(https_port=port)
    worker.run()  # Automatic HTTPS+mTLS
```

**Migrated Workers**: All 9 production + reference workers now use this pattern.

## Review History

- 2025-11-15 - Initial decision during Issue #19
- 2025-11-15 - Implemented and validated across all workers
- 2025-11-15 - 40.4% code reduction achieved in Phase 1, security adds more savings
