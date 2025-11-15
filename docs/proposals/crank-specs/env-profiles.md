# Crank Python Environment Profiles

## python-core
- Python 3.11
- stdlib, requests, pydantic
- No subprocess access
- CPU-only

## python-docs
- python-core +
- pandoc installed
- markdown, beautifulsoup4

## python-ml
- Python + numpy + torch (CPU or GPU build)
- Accelerator determined at worker startup
- Used for ML inference or heavy compute

## Notes for Agents
- No pip install allowed.
- Only use tools explicitly listed in the profile.
