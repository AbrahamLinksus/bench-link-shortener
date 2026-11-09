# Small benchmark: link shortener API

## What it does
| Endpoint | Behaviour |
|---|---|
| `POST /links` with `{"url": "https://example.com/page"}` | `201` → `{"code": "aZ3k9Q", "short_url": "http://localhost:8000/aZ3k9Q"}`. Invalid URL → `422`. |
| `GET /{code}` | `307` redirect to the original URL and +1 click. Unknown code → `404`. |
| `GET /links/{code}/stats` | `200` → `{"url": "...", "clicks": 3, "created_at": "2026-11-09T10:00:00Z"}`. Unknown → `404`. |

- Codes: 6 characters, `[A-Za-z0-9]`, unique.
- Data is stored in SQLite and survives a restart.

## Stack (fixed)
Python 3.12+, FastAPI, SQLite via the standard library `sqlite3`, `uv` for the project,
`pytest` + `pytest-cov`, `ruff`, `mypy --strict`. Allowed extras: `uvicorn` (to run the app)
and `httpx` (for FastAPI's test client). No other packages.

## Quality bar
- Tests for every endpoint, including the error cases.
- Coverage ≥ 85%.
- `ruff check` and `mypy --strict` pass with no errors.
- Layered code: routes → service → repository (SQLite).
- `README.md` explains how to install, run and test it.
- `start.sh` as described below.

## How it's started
`./start.sh` in the project root installs what it needs (e.g. `uv sync`) and starts the API on
port 8000 (or `$PORT` if set). Data is kept in a local database file, so it survives a restart.

## Not included
Auth, custom codes, expiry, a web UI, deployment.
