# SPEC — bench-link-shortener

> Written by the planner from the owner's answers, round by round. Approved before any design.
> Lines marked *(assumed)* were decided by the planner because the owner chose "decide for me"
> (or, in round 1, because docs/owner-spec.md left the point open and it was not material).
> Source of truth for requirements: `docs/owner-spec.md`.

## 1. Goal
A small, self-hosted HTTP API that turns long URLs into 6-character short codes, redirects
anyone who opens a short link to the original URL, and counts those clicks. It is for a
developer (the owner) who wants a minimal, well-tested, strictly typed FastAPI service that
runs locally with one command (`./start.sh`) and keeps its data in SQLite across restarts.
It also serves as a quality benchmark: layered code, full endpoint tests, ≥ 85% coverage,
clean `ruff` and `mypy --strict`.

## 2. Users
| User | What they want | How often |
|---|---|---|
| Link creator (API client, e.g. a script or `curl`) | Shorten a URL and get a short link back | On demand, low volume |
| Link visitor (any browser / HTTP client) | Open a short link and land on the original page | Every click |
| Owner / operator | Check click stats for a link; install, run and test the service locally | Occasionally |

## 3. User stories
| ID | As a… | I want to… | So that… | Acceptance (checkable) |
|---|---|---|---|---|
| US-01 | link creator | `POST /links` with `{"url": "https://example.com/page"}` | I get a short link to share | Response is `201` with JSON `{"code": "<6 chars [A-Za-z0-9]>", "short_url": "http://localhost:8000/<code>"}`; the code is stored |
| US-02 | link creator | get a clear rejection when I send an invalid URL | I know my input was wrong | Body missing `url`, non-string `url`, a value that is not an absolute `http`/`https` URL with a host, or longer than 2048 chars → `422`, nothing stored *(assumed: rules for "valid URL")* |
| US-03 | link visitor | open `GET /{code}` | I land on the original page | Response is `307` with `Location: <original url>`; the link's click count increases by exactly 1 |
| US-04 | link visitor | get a `404` for a code that doesn't exist | I know the link is wrong | `GET /unknwn` → `404` with JSON `{"detail": "Link not found"}`; no click recorded anywhere |
| US-05 | owner | `GET /links/{code}/stats` | I see how a link is doing | `200` with JSON `{"url": "...", "clicks": <int>, "created_at": "<ISO-8601 UTC, e.g. 2026-11-09T10:00:00Z>"}`; unknown code → `404` |
| US-06 | owner | have links and click counts survive a restart | I don't lose data | Create a link, click it twice, stop and restart via `./start.sh`, stats still show the same url and `clicks: 2` |
| US-07 | owner | start the service with `./start.sh` | I can run it with one command | From a fresh clone `./start.sh` installs deps (`uv sync`) and serves on port 8000, or `$PORT` if set |
| US-08 | owner | read install/run/test instructions in `README.md` | I can use and verify it without help | README covers install, run (`./start.sh`, `$PORT`), test (`pytest` with coverage), lint and type-check commands |

## 4. Main flows
### F-1 · Shorten a URL (US-01, US-02)
1. Client sends `POST /links` with JSON body `{"url": "<long url>"}`.
2. API validates the URL (absolute, scheme `http` or `https`, has a host, ≤ 2048 chars) *(assumed)*.
3. API generates a random 6-character code from `[A-Za-z0-9]`; if it already exists, it generates another (retry) until unique.
4. API stores code, original URL, clicks = 0, created_at = now (UTC).
5. API returns `201` with `code` and `short_url` (= the base URL the request was served on + `/` + code, e.g. `http://localhost:8000/aZ3k9Q`; with `PORT=9000` it is `http://localhost:9000/aZ3k9Q`) *(assumed: base URL taken from the incoming request)*.
- Errors / edge cases:
  - Invalid / missing / non-string URL, malformed JSON → `422` (FastAPI's standard validation error body) *(assumed: body format)*.
  - Same URL posted twice → two different codes, each with its own click count *(assumed: no de-duplication)*.
  - URL is stored exactly as submitted (no normalisation) *(assumed)*.

### F-2 · Follow a short link (US-03, US-04)
1. Visitor requests `GET /{code}`.
2. API looks up the code (case-sensitive: `aZ3k9Q` ≠ `az3k9q`).
3. If found: click count +1 (persisted), respond `307` with `Location` = original URL.
- Errors / edge cases:
  - Unknown code, or a path that isn't a valid 6-char code → `404` `{"detail": "Link not found"}`; no count changes.
  - Every request counts as a click, including repeat visits and bots *(assumed: no de-duplication or bot filtering)*.
  - `HEAD /{code}` is not required *(assumed)*.

### F-3 · View link stats (US-05)
1. Owner requests `GET /links/{code}/stats`.
2. API looks up the code; does not change the click count.
3. Returns `200` with `url`, `clicks`, `created_at` (UTC, ISO-8601, second precision, `Z` suffix) *(assumed: precision)*.
- Errors / edge cases: unknown code → `404` `{"detail": "Link not found"}`.

### F-4 · Run, restart and test the service (US-06, US-07, US-08)
1. Owner runs `./start.sh` in the project root.
2. Script runs `uv sync`, then starts the API with uvicorn on `0.0.0.0:${PORT:-8000}` *(assumed: bind address)*.
3. Data is kept in a local SQLite file in the project directory (git-ignored), created on first start *(assumed: location)*.
4. Stop (Ctrl+C) and run `./start.sh` again: all links and click counts are still there.
5. Owner runs tests / lint / type-check as described in README.
- Errors / edge cases: `uv` not installed → `start.sh` exits non-zero with a clear message pointing to the README *(assumed)*; port in use → uvicorn's own error, non-zero exit.

## 5. Inputs and outputs (concrete examples)
| Flow | Example input | Expected output |
|---|---|---|
| F-1 | `POST /links` `{"url": "https://example.com/page"}` | `201` `{"code": "aZ3k9Q", "short_url": "http://localhost:8000/aZ3k9Q"}` |
| F-1 | `POST /links` `{"url": "not a url"}` | `422` (validation error body) |
| F-1 | `POST /links` `{"url": "ftp://files.example.com/a.zip"}` | `422` *(assumed: only http/https)* |
| F-1 | `POST /links` `{}` | `422` |
| F-2 | `GET /aZ3k9Q` | `307`, `Location: https://example.com/page`; clicks 0 → 1 |
| F-2 | `GET /zzzzzz` (never created) | `404` `{"detail": "Link not found"}` |
| F-3 | `GET /links/aZ3k9Q/stats` after 3 clicks | `200` `{"url": "https://example.com/page", "clicks": 3, "created_at": "2026-11-09T10:00:00Z"}` |
| F-3 | `GET /links/zzzzzz/stats` | `404` `{"detail": "Link not found"}` |
| F-4 | `PORT=9000 ./start.sh` | API on port 9000; `POST /links` returns `short_url` starting `http://localhost:9000/` |

## 6. Data
- What is stored: one record per link: code (6 chars, unique, case-sensitive), original URL, click count (integer ≥ 0), created_at (UTC timestamp).
- Source: created only through `POST /links`; click count changes only through `GET /{code}`.
- Where: a single local SQLite file (standard library `sqlite3`), path configurable by env var with a project-local default; tests use a temporary / in-memory database *(assumed)*.
- Volume: small — up to roughly 10,000 links and low click volume on a single machine *(assumed)*. 62⁶ ≈ 56.8 billion possible codes, so collisions are rare and handled by retry.
- Retention: kept forever; no deletion or expiry (expiry is a non-goal).

## 7. Screens (UI projects)
none: API

## 8. Integrations
- none. No external services, accounts or keys. Only local packages: uvicorn (serve), httpx (test client).

## 9. Non-functional
- Scale / load: single process, single machine, low traffic; not a concern beyond correctness *(assumed)*.
- Latency: not a concern; local SQLite keeps responses well under 100 ms on a dev machine *(assumed)*.
- Concurrency: click increments must not be lost under concurrent requests to the same code (single atomic increment) *(assumed)*.
- Offline: runs fully offline once dependencies are installed.
- Security & privacy: no auth (non-goal); no personal data stored; SQL uses parameterised queries only; redirect targets restricted to http/https so `javascript:`/`data:` URLs can't be stored *(assumed)*.
- Cost limits: none — no paid services.
- Platforms/devices: Linux/macOS with Python 3.12+ and `uv`; any HTTP client.

## 10. Constraints
- Stack (fixed by owner): Python 3.12+, FastAPI, SQLite via stdlib `sqlite3`, `uv`, `pytest` + `pytest-cov`, `ruff`, `mypy --strict`. Allowed extras: `uvicorn`, `httpx`. No other packages.
- Architecture: layered routes → service → repository (SQLite).
- Quality: tests for every endpoint incl. error cases; coverage ≥ 85%; `ruff check` and `mypy --strict` clean.
- Deliverables: `README.md` (install, run, test), executable `start.sh` (installs + runs on `$PORT` or 8000).
- Deadline: none stated. Deployment target: local machine only (deployment is a non-goal).

## 11. Non-goals (explicitly out)
- Authentication / user accounts / API keys.
- Custom (vanity) codes chosen by the client.
- Link expiry, deletion or editing.
- A web UI of any kind.
- Deployment (Docker, cloud, CI/CD hosting).
- Analytics beyond a total click count (no per-click referrer, IP, geo or time series) *(assumed)*.
- Rate limiting and URL de-duplication *(assumed)*.

## 12. Definition of done
- [ ] `./start.sh` from a fresh clone installs deps and serves the API on port 8000 (and on `$PORT` when set).
- [ ] `curl -X POST localhost:8000/links -H 'content-type: application/json' -d '{"url":"https://example.com/page"}'` returns `201` with a 6-char code and `short_url`; an invalid URL returns `422`.
- [ ] `curl -i localhost:8000/<code>` returns `307` to the original URL, `GET /links/<code>/stats` shows the click count rising; unknown codes return `404` on both.
- [ ] After stopping and re-running `./start.sh`, previously created links still redirect and keep their click counts.
- [ ] `uv run pytest --cov` passes with coverage ≥ 85%, and `uv run ruff check .` and `uv run mypy --strict` report no errors.
- [ ] `README.md` explains install, run and test; code is layered routes → service → repository.

## Open questions
- none
