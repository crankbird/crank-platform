# Dockerfile Permission Regression After Docker Upgrade

**Date**: 2025-11-15
**Impact**: All services except `crank-cert-authority` fail to start
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

## Services Affected

- ✅ `crank-cert-authority` - FIXED (commit 5b7f9f3)
- ❌ `crank-platform` - Broken (controller)
- ❌ `crank-email-classifier` - Unknown
- ❌ `crank-email-parser` - Unknown
- ❌ `crank-streaming` - Unknown
- ❌ `crank-doc-converter` - Unknown
- ❌ All other workers - Unknown

## Solution

Add `--chown=<user>:<group>` to all COPY commands:

```dockerfile
# Before
COPY services/some_file.py .

# After
COPY --chown=worker:worker services/some_file.py .
```

**Note**: For platform (controller), user is `worker:worker` (gid/uid 1000), NOT `controller`.

## Testing Blocked

- Issue #19 integration testing blocked until platform Dockerfile fixed
- Cannot test certificate bootstrap flow end-to-end
- Workers depend on platform (controller) for registration

## Action Items

1. Fix `services/Dockerfile.crank-platform` immediately (blocking Issue #19)
2. Audit all Dockerfiles in `services/` directory
3. Add `--chown` to all COPY commands
4. Test each service starts successfully
5. Document Docker version requirements in README

## Related

- Issue #19: Security Configuration Scattered
- Docker upgrade: v20.10.17 → v28.5.2
- Compose upgrade: v1.29.2 → v2.40.3
