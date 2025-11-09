# Pre-Controller Architecture Archive

**Date**: November 9, 2025  
**Reason**: Architectural refactor from platform-centric to controller/worker model

## What's Archived Here

This directory contains a snapshot of the **working platform-centric architecture** before the controller/worker refactor described in `docs/planning/CONTROLLER_WORKER_REFACTOR_PLAN.md`.

### Archived Components

- **services-old/** - Original service implementations (email-classifier, streaming, doc-converter, etc.)
  - Each service contained duplicated registration/heartbeat/cert logic
  - Services registered to monolithic "platform" URL
  - Ad-hoc capability declarations embedded in code
  - ~200 lines per worker (now ~80 lines with worker_runtime)

- **image-classifier/** & **image-classifier-gpu/** - Standalone classifier directories
  - Nearly identical to other services
  - Violated "workers are not containers" principle

- **docker-compose.*.yml** - Platform-centric compose files
  - docker-compose.development.yml
  - docker-compose.local-prod.yml
  - docker-compose.azure.yml
  - Treated platform as single monolithic entity

- **README-old.md** - Original README describing platform architecture

## Working State at Archive Time

✅ **All services were healthy and functional**:
- Platform (8443)
- Cert Authority (9090)
- Email Parser (8300)
- Email Classifier (8200)
- Image Classifier CPU (8401)
- Doc Converter (8100)
- Streaming (8500)

✅ **Test suite passing**: 45 tests, 2 skipped, 3 failing (Azure integration only), zero warnings

✅ **All HTTPS with mTLS**: Certificate management working correctly

## Why This Was Archived

The platform-centric architecture had fundamental issues:

1. **Massive Code Duplication**: Every worker reimplemented registration, heartbeat, cert bootstrap
2. **Platform-as-Monolith**: Violated controller-per-node principle from taxonomy
3. **Dockerfile Redundancy**: 7 nearly identical Dockerfiles differing only in requirements/ports
4. **No Capability Schema**: Ad-hoc capability declarations, no versioning or validation
5. **Privilege Violations**: Workers performing certificate initialization (controller concern)
6. **Tests Bypassed Routing**: Direct service calls instead of capability-based routing

## New Architecture (Post-Refactor)

See:
- `docs/planning/crank-taxonomy-and-deployment.md` - Architectural vision
- `docs/planning/CONTROLLER_WORKER_REFACTOR_PLAN.md` - Implementation plan
- GitHub Issues #27-#31 - Phased migration

**Key Changes**:
- Workers use shared `src/crank/worker_runtime/` base classes
- Capabilities defined in `src/crank/capabilities/schema.py`
- Controller-per-node instead of monolithic platform
- Base Docker image + thin worker layers
- Capability-based routing with version compatibility

## Restoration (If Needed)

If new architecture fails and rollback is needed:

```bash
# Restore services
cp -r archive/2025-11-09-pre-controller-refactor/services-old/* services/

# Restore classifiers
cp -r archive/2025-11-09-pre-controller-refactor/image-classifier* .

# Restore compose files
cp archive/2025-11-09-pre-controller-refactor/docker-compose.*.yml .

# Restore README
cp archive/2025-11-09-pre-controller-refactor/README-old.md README.md

# Rebuild containers
docker-compose -f docker-compose.development.yml up --build
```

## Timeline

- **2025-11-09**: Architecture archived, Phase 0 begins (capability schema + worker runtime)
- **Phase 1-4**: Incremental migration (see CONTROLLER_WORKER_REFACTOR_PLAN.md)
- **Post-Phase 4**: If successful, this becomes permanent archive; if failed, restore from here

---

**This archive represents the last working state of the platform-centric architecture.**
