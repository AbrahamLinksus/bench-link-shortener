#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v uv >/dev/null 2>&1; then
  echo "error: 'uv' is not installed. See README.md (Install) for instructions." >&2
  exit 1
fi
# Shell wins over .env (LLD §10.1): snapshot every exported variable, load .env,
# then put back any value that .env changed. .env therefore only fills unset variables.
if [[ -f .env ]]; then
  _dotenv_saved=()
  for _dotenv_name in $(compgen -e); do
    _dotenv_saved+=("$_dotenv_name" "${!_dotenv_name-}")
  done
  set -a
  . ./.env
  set +a
  for ((_dotenv_i = 0; _dotenv_i < ${#_dotenv_saved[@]}; _dotenv_i += 2)); do
    _dotenv_name="${_dotenv_saved[_dotenv_i]}"
    if [[ "${!_dotenv_name-}" != "${_dotenv_saved[_dotenv_i + 1]}" ]]; then
      export "$_dotenv_name=${_dotenv_saved[_dotenv_i + 1]}"
    fi
  done
  unset _dotenv_saved _dotenv_name _dotenv_i
fi
uv sync
exec uv run uvicorn link_shortener.main:create_app --factory --app-dir src \
  --host 0.0.0.0 --port "${PORT:-8000}"
