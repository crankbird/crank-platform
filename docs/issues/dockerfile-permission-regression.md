# Dockerfile Permission Regression After Docker Upgrade

**Date**: 2025-11-15
**Status**: ✅ RESOLVED
**Impact**: All services fixed and running
**Root Cause**: Docker v28.5.2 stricter file permission enforcement

## What Happened

Upgraded Docker from v20.10.17 → v28.5.2 to resolve docker-compose v1/v2 compatibility issues during Issue #19 (Security Configuration Consolidation) testing.

After upgrade, all service containers fail with:
```
/usr/local/bin/python: can't open file '/app/scripts/crank_cert_initialize.py': [Errno 13] Permission denied
```

## Root Cause

Dockerfiles use pattern:
```dockerfile
RUN adduser --uid 1000 --gid 1000 --disabled-password worker
COPY services/some_file.py .           # ❌ Owned by root
USER worker                             # Switch to non-root
CMD ["python", "some_file.py"]         # ❌ Permission denied
```

Files copied before `USER` directive are owned by `root:root`, but container runs as `worker` user → permission denied.

**Why this worked before**: Docker v20.10.17 had more permissive file access for COPY commands. Docker v28.5.2 enforces stricter ownership.

## Services Status (All Fixed ✅)

- ✅ `crank-cert-authority` - FIXED (commit bff7284)
- ✅ `crank-platform` - FIXED (commit bff7284)
- ✅ `crank-email-classifier` - FIXED (commit a10e831)
- ✅ `crank-email-parser` - FIXED (commit 38a05b3)
- ✅ `crank-streaming` - FIXED (commit 38a05b3)
- ✅ `crank-doc-converter` - FIXED (commit 38a05b3)

**Result**: All 6 services running healthy with HTTPS + mTLS## Solution

Add `--chown=<user>:<group>` to all COPY commands:

```dockerfile
# Before
COPY services/some_file.py .

# After
COPY --chown=worker:worker services/some_file.py .
```

**Note**: For platform (controller), user is `worker:worker` (gid/uid 1000), NOT `controller`.

## Resolution Complete ✅

All Dockerfiles fixed with `--chown` flags and certificate bootstrap:

1. ✅ `services/Dockerfile.crank-platform` - Controller fixed
2. ✅ `services/Dockerfile.crank-cert-authority` - CA service fixed
3. ✅ `services/Dockerfile.crank-email-classifier` - Worker fixed
4. ✅ `services/Dockerfile.crank-streaming` - Worker fixed
5. ✅ `services/Dockerfile.crank-doc-converter` - Worker fixed
6. ✅ `services/Dockerfile.crank-email-parser` - Worker fixed

**Additional fixes**:
- Legacy `crank_cert_initialize.py` updated to write correct filenames (client.crt/client.key)
- All workers use unified `crank.security` module
- Deprecated security modules removed (675 lines cleaned up)

**Testing verified**: End-to-end certificate bootstrap (CA → Platform → 4 Workers) all healthy

## Related

- Issue #19: Security Configuration Scattered
- Docker upgrade: v20.10.17 → v28.5.2
- Compose upgrade: v1.29.2 → v2.40.3
