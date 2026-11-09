#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v uv >/dev/null 2>&1; then
  echo "error: 'uv' is not installed. See README.md (Install) for instructions." >&2
  exit 1
fi
if [[ -f .env ]]; then set -a; . ./.env; set +a; fi
uv sync
exec uv run uvicorn link_shortener.main:create_app --factory --app-dir src \
  --host 0.0.0.0 --port "${PORT:-8000}"
