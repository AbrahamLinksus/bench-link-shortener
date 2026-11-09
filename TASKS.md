# TASKS — bench-link-shortener

Status: Backlog → In progress → Review → Needs you → Done

`Context:` lists exactly what the task's agents need to read: spec stories, LLD sections
(by number) and file globs. The Orchestrator builds every brief's `Read:` field from it.

Every task: backend-coder writes the code, tester writes the tests listed in LLD §11.1 for
that task's modules, and the task ends with `scripts/check.sh` passing (ruff, format,
`mypy --strict`, pytest with coverage ≥ 85%). Package versions are the ones in `uv.lock`
(env-setup); LLD §0.4 was re-checked against it at M2 and matches.

## M1 · Working API (shorten, redirect, stats, persistence)
Outcome: all three endpoints behave as in SPEC §5 under TestClient, data survives a new app
instance on the same file, and the layer contracts are enforced by a test.
(Merges HLD M1–M3.)

### T-01 · Core and persistence: config, domain, code generator, db, repository
- Owner: backend-coder (tests: tester)
- Depends on: —
- Context: SPEC US-03, US-04, US-06 · LLD §0.2, §0.3, §1, §2, §3, §4, §5, §11.1 (rows test_config … test_repository, test_architecture), §11.2 (`db_path`, `connection` fixtures only), §11.3 · files: src/link_shortener/{config,domain,codes,db,repository}.py, tests/*, pyproject.toml
- Status: Done
- Acceptance criteria:
  - [x] `tests/test_smoke.py` is deleted; `config.py`, `domain.py`, `codes.py`, `db.py`, `repository.py` implement the signatures in LLD §1.1, §2.1, §3.1, §4.1, §5.1 (other modules stay empty).
  - [x] `test_repository.py` passes, including add/get round trip with `created_at`, duplicate → `DuplicateCodeError`, case-sensitive lookup, and the concurrency test (8 threads × 25 increments → `clicks == 200`).
  - [x] Reopening the same SQLite file with a new connection returns the stored link and click count (test passes).
  - [x] `tests/test_architecture.py` has one parametrised test per module in the LLD §0.3 table, and all of them pass.
  - [x] `scripts/check.sh` exits 0 with coverage ≥ 85%.
- Result: approved 2026-11-09 · main ba78ad4 · 97.9% cov, 56 tests · review 0C/0M/3 minor

### T-02 · Domain logic and HTTP models: service and schemas
- Owner: backend-coder (tests: tester)
- Depends on: T-01
- Context: SPEC US-01, US-02, US-03, US-04, US-05 · LLD §2.1, §6, §7, §11.1 (rows test_service, test_schemas), §11.2 (`tests/fakes.py`) · files: src/link_shortener/{domain,service,schemas}.py, tests/fakes.py, tests/test_service.py, tests/test_schemas.py
- Status: Done
- Acceptance criteria:
  - [x] `tests/fakes.py` provides `InMemoryLinkRepository`, `SequenceCodeGenerator`, `FIXED_NOW` / `fixed_clock` (LLD §11.2), with no patching of production modules.
  - [x] `test_service.py` passes: with `SequenceCodeGenerator(["aaaaaa","aaaaaa","bbbbbb"])` a second link gets `bbbbbb`; 10 collisions → `CodeGenerationError`; `resolve_and_count` increments exactly once; invalid or unknown code → `LinkNotFoundError` with no increment; `get_stats` leaves clicks unchanged.
  - [x] `test_schemas.py` passes for every LLD §7.5 rule: valid http/https URL returned unchanged; `ftp://…`, `javascript:…`, `not a url`, `http://`, embedded space, 2049 chars, `123`, `http://host:99999` → `ValidationError`.
  - [x] `LinkStats` serialises `created_at` as `2026-11-09T10:00:00Z` (test passes).
  - [x] `scripts/check.sh` exits 0 with coverage ≥ 85%.
- Result: approved 2026-11-09 · main 273771e · 98.9% cov, 88 tests · review 0C/0M/3 minor

### T-03 · Endpoints and app factory: routes, main, API and persistence tests
- Owner: backend-coder (tests: tester)
- Depends on: T-02
- Context: SPEC US-01, US-02, US-03, US-04, US-05, US-06, §5 · LLD §6.1, §7.1, §8, §9, §11.1 (rows test_api_create, test_api_redirect, test_api_stats, test_persistence), §11.2 · files: src/link_shortener/{routes,main,service,schemas}.py, tests/conftest.py, tests/test_api_*.py, tests/test_persistence.py
- Status: Done
- Acceptance criteria:
  - [x] `POST /links` `{"url": "https://example.com/page"}` → `201` with a 6-char `[A-Za-z0-9]` code and `short_url` built from the request base URL (TestClient `base_url="http://localhost:9000"` → `http://localhost:9000/<code>`); `{}`, `not a url`, `ftp://…`, malformed JSON → `422` and nothing stored.
  - [x] `GET /{code}` → `307` with `Location` = original URL (`follow_redirects=False`) and clicks 0 → 1 → 2; unknown 6-char code, `/abc` and `/links` → `404 {"detail": "Link not found"}` with no click recorded.
  - [x] `GET /links/{code}/stats` → `200 {"url", "clicks", "created_at": "YYYY-MM-DDTHH:MM:SSZ"}` without changing clicks; unknown code → `404 {"detail": "Link not found"}`.
  - [x] `test_persistence.py`: app A creates a link and clicks it twice, then a new `create_app` on the same file reports `clicks: 2` and the redirect still works. Importing `link_shortener.main` creates no `links.db` (there is no module-level `app`).
  - [x] Every SPEC §5 row (except the `./start.sh` one) has at least one passing test; `scripts/check.sh` exits 0 with coverage ≥ 85%; a TestClient run of the §5 examples is captured to `.results/T-03/`.
- Result: approved 2026-11-09 · main add20ec · 99% cov, 111 tests · review 0C/0M/5 minor

## M2 · Run and ship
Outcome: the owner starts the service with `./start.sh` on 8000 or `$PORT`, a restart keeps
data, and every SPEC §12 box can be ticked (README is written in the milestone-end docs step).
(HLD M4.)

### T-04 · One-command start: start.sh and run checks
- Owner: backend-coder (tests: tester)
- Depends on: T-03
- Context: SPEC US-06, US-07, F-4, §12 · LLD §0.5, §9.1, §10.1, §10.4 · files: start.sh, .env.example, .gitignore
- Status: Done
- Acceptance criteria:
  - [x] `start.sh` matches LLD §10.1, is executable (`ls -l` shows `x`), and `./start.sh` serves on port 8000: a `curl` POST returns `201` with `short_url` starting `http://localhost:8000/` (captured to `.results/T-04/`).
  - [x] `PORT=9000 ./start.sh` serves on 9000 and `short_url` starts with `http://localhost:9000/`.
  - [x] Create a link, `curl` it twice, stop (Ctrl+C / kill), rerun `./start.sh`: stats show the same `url` and `clicks: 2`; `git status` shows `links.db` as ignored, not untracked.
  - [x] With `uv` absent from `PATH`, `./start.sh` exits non-zero and prints the message pointing to README.md.
  - [x] `scripts/check.sh` exits 0 with coverage ≥ 85%, and no server process is left running.
- Result: approved 2026-11-09 · main 92a72c0 · 99.18% cov, 111 tests · review 0C/0M/0 minor

### M2-docs · Milestone M2 as-built sync + README
- Status: Done
- Result: approved 2026-11-09 · main 9b961b0 · LLD header/§0.2/§0.4/§10.1/§10.4 synced · README rewritten for ./start.sh

### T-04b · Shell environment wins over .env in start.sh (CR-1 / D-13)
- Owner: backend-coder (tests: tester)
- Depends on: T-04, M2-docs
- Context: SPEC US-07, F-4, §5 (F-4 row), §12 · LLD §0.5, §10.1, §10.4, §10.5, §11.1 (row test_start_script), §11.5 · files: start.sh, .env.example, tests/test_start_script.py, README.md
- Status: Done
- Acceptance criteria:
  - [x] `start.sh` matches LLD §10.1 (only the `.env` block replaced; `uv` check, `uv sync` and `exec uv run uvicorn …` unchanged) and is still executable (`ls -l` shows `x`).
  - [x] Run check in a temporary directory, never in the worktree: copy the project into a temp dir (e.g. `cp -r` of the worktree without `.venv/`, or `start.sh` copied plus `src/`, `pyproject.toml`, `uv.lock`, `.python-version` symlinked) and `cp .env.example .env` there (`PORT=8000`). From that copy, `PORT=9000 ./start.sh` serves on 9000 and a `curl` POST returns `short_url` starting `http://localhost:9000/`; plain `./start.sh` serves on 8000. Both runs are captured to `.results/T-04b/`, no server is left running, and the worktree still has no `.env` (`ls -a` shows none).
  - [x] `tests/test_start_script.py` has the three LLD §11.5 tests (shell overrides `.env` incl. the byte-for-byte `LINKS_DB_PATH`, `.env` fills unset vars, no `.env` → `--port 8000`), and all of them pass. The shell-overrides test fails when run against the pre-CR-1 `start.sh` (temp copy of `git show main:start.sh`; output captured).
  - [x] README (edited by backend-coder): `grep -nE "Known edge case|override values you set in the shell" README.md` prints nothing, and Run has a one-line precedence note (command line → `.env` → default) per LLD §10.5.
  - [x] With `uv` absent from `PATH`, `./start.sh` still exits non-zero with the README message. `scripts/check.sh` exits 0 with coverage ≥ 85%.
- Result: approved 2026-11-09 · main ad2e64a · 115 tests, 99.18% cov · review 0C/0M/4 minor (in handover notes)

## Change requests
### CR-1 · Shell environment wins over .env in start.sh
- Status: Approved 2026-11-09 · built as T-04b (main ad2e64a) · Done
- Problem: start.sh sources `.env` after the shell environment, so `PORT` / `LINKS_DB_PATH` in `.env` override `PORT=9000 ./start.sh`, contrary to SPEC US-07 / F-4 ("`$PORT` if set").
- Wanted: values set on the command line win; `.env` only fills in unset ones. Update LLD §10.1, add a cheap automated check, remove the README "Known edge case" caveat.

## Handover
- Status: Done
- Result: approved 2026-11-09 · main 4baaa7d · CI green (run 42630616905) · doc path check 0C/1M/4m → M + 2 minors fixed
