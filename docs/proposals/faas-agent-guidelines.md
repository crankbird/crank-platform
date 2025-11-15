# Agent Instructions for Crank Execution

## Summary
Agents generate Python code. Crank executes it.

## Rules
- Always generate Python 3.11.
- Choose an env profile:
  - python-core: general logic
  - python-docs: pandoc workflows
  - python-ml: ML or numeric work
- Specify accelerator needs:
  ```json
  "constraints": { "accelerator": "gpu" }
  ```
- Do not use pip install.
- Only assume tools listed in env profile.
