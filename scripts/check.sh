#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict
if [[ "${CHECK_NO_COVERAGE:-0}" == "1" ]]; then
  uv run pytest -q
else
  uv run pytest -q --cov=link_shortener --cov-report=term-missing --cov-fail-under=85
fi
