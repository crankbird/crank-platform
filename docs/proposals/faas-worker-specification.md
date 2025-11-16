# FaaS Worker v0 Specification

## Purpose
A minimal Python-only FaaS worker for Crank-Mesh.

## Overview
- Executes Python 3.11 code in a sandbox.
- Supports environment profiles.
- Handles CPU/GPU variants.
- Enforces time/output limits.

## Job Schema

```json
{
  "job_id": "1234",
  "runtime": "python",
  "env_profile": "python-core",
  "constraints": {
    "accelerator": "cpu",
    "timeout_sec": 10,
    "max_output_bytes": 1048576
  },
  "code": "print(42)",
  "args": {"foo": "bar"}
}
```

## Execution Flow
1. Create temp dir.
2. Write code to job.py.
3. Select interpreter based on env_profile.
4. Run subprocess under timeout.
5. Return stdout, stderr, result, metrics.

## Safety Rules
- No network access.
- Limit output size.
- Timeouts enforced.
- CPU/GPU selection via constraints.
