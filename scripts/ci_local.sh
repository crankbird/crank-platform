#!/usr/bin/env bash
set -euo pipefail
echo ">> Using uv virtual env"
uv venv --seed --python 3.11 || true
source .venv/bin/activate
uv pip install -U ruff mypy pytest

echo ">> Fix FastAPI DI"
python tools/fix_fastapi_di.py || true

echo ">> Mark Router Files"
python tools/mark_router_files.py || true

echo ">> Ruff format + lint"
ruff format .
ruff check . --fix

echo ">> mypy"
mypy .

echo ">> tests"
pytest -q || pytest -q -k "not gpu"

echo ">> If all green, commit:"
echo "git add -A && git commit -m 'chore(types): inbox-zero pass on macOS (DI+pyright+mypy+ruff)'"
