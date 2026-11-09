# Codebase walkthrough — bench-link-shortener

> A guided tour so the owner can understand, own and explain this code. Written at handover
> by the architect. Line numbers refer to the code at main ad2e64a; `LLD §n` points at
> `docs/LLD.md`.

## 1. Read these first (in order)
1. `src/link_shortener/domain.py`: the vocabulary of the whole app in about 60 lines — `Link`, the
   code rule `is_valid_code`, the three errors, and the two ports (`LinkRepository`,
   `CodeGenerator`) plus `Clock`. Everything else either implements or uses these.
2. `src/link_shortener/service.py`: all business rules in one class, `LinkService` — collision
   retry in `create_link`, the "count then read" logic in `resolve_and_count`, and `get_stats`.
   It only knows the ports, never SQL or HTTP.
3. `src/link_shortener/main.py`: the composition root. `create_app` builds settings, creates the
   table and stores a per-request provider (`_service_scope`) on `app.state`. This is where
   the concrete classes meet.
4. `src/link_shortener/routes.py`: the three endpoints and `get_link_service`, the FastAPI
   dependency that pulls a `LinkService` out of the provider. Shows how HTTP is kept thin.
5. `src/link_shortener/repository.py`: the only SQL for links; note the single atomic
   `UPDATE … clicks = clicks + 1` and the strict row mapping in `_row_to_link`.
6. `src/link_shortener/schemas.py`: URL validation rules (why `422` happens).
7. `tests/fakes.py` and `tests/conftest.py`: how tests swap collaborators and get a fresh
   SQLite file per test.
8. `start.sh`: how the app is launched and how `.env` and the shell environment are merged.

## 2. Follow one request end to end
Trace `GET /{code}` (a visitor following a short link) — the flow that touches every layer.

**Before any request: startup**
1. `start.sh:27-28` runs `exec uv run uvicorn link_shortener.main:create_app --factory --app-dir src --host 0.0.0.0 --port "${PORT:-8000}"`.
   `--factory` tells uvicorn to call `create_app()` instead of importing a module-level `app`.
2. `main.py:29` — `Settings.from_env()` (`config.py:18-22`) reads `LINKS_DB_PATH`, defaulting to `links.db`.
3. `main.py:30` — `init_schema(settings.db_path)` (`db.py:25-31`) creates the parent directory and runs `SCHEMA_SQL`.
4. `main.py:32` — stores `partial(_service_scope, settings.db_path)` on `app.state` under the
   name `routes.SERVICE_PROVIDER_KEY` (`"link_service_provider"`, `routes.py:15`).
5. `main.py:33` — `app.include_router(router)`. The router declares `POST /links`, then
   `GET /links/{code}/stats`, then the catch-all `GET /{code}` last (`routes.py:31`, `:39`, `:48`).

**The request: `GET /aZ3k9Q`**
1. FastAPI matches `@router.get("/{code}", status_code=307, …)` at `routes.py:48`. Before it
   calls `follow_link`, it resolves the `service: LinkServiceDep` parameter
   (`LinkServiceDep` = `Annotated[LinkService, Depends(get_link_service)]`, `routes.py:28`).
2. `get_link_service` (`routes.py:22-25`) reads the provider from `request.app.state` and
   enters it with `with provider() as service:` (`routes.py:24`) — **hand-off to the
   composition root**.
3. `_service_scope` (`main.py:19-25`) opens a fresh connection with `connect(db_path)`
   (`main.py:21` → `db.py:19-22`: autocommit, `check_same_thread=False`, 5 s busy timeout) and
   yields `LinkService(SqliteLinkRepository(connection), RandomCodeGenerator(), utc_now)`
   (`main.py:23`). The `yield` at `routes.py:25` hands that service to the endpoint.
4. `follow_link` (`routes.py:49-54`) calls `service.resolve_and_count(code)` at `routes.py:51`
   — **hand-off to the service layer**.
5. `LinkService.resolve_and_count` (`service.py:49-52`), line 50:
   - `is_valid_code(code)` (`domain.py:15-16`, regex `[A-Za-z0-9]{6}`). Invalid → raise
     `LinkNotFoundError` without touching the database.
   - otherwise `self._repository.increment_clicks(code)` — **hand-off to the repository
     through the `LinkRepository` port**.
6. `SqliteLinkRepository.increment_clicks` (`repository.py:51-55`) runs
   `UPDATE links SET clicks = clicks + 1 WHERE code = ?` and returns `cursor.rowcount == 1`.
   Because the connection is autocommit, this single statement is its own transaction, so
   concurrent clicks are never lost. `False` (unknown code) → the service raises
   `LinkNotFoundError` (`service.py:51`).
7. `service.py:52` — `self.get_stats(code).url`: `get_stats` (`service.py:54-60`) calls
   `self._repository.get_by_code(code)` (`repository.py:45-49`), which runs a parameterised
   `SELECT` and maps the tuple to a `Link` in `_row_to_link` (`repository.py:20-29`, timestamp
   parsed by `_from_row_timestamp`, `repository.py:16-17`).
8. Back in `follow_link`: success → `RedirectResponse(url, status_code=307)` (`routes.py:54`);
   `LinkNotFoundError` → `raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL) from err`
   (`routes.py:52-53`), giving `{"detail": "Link not found"}`.
9. After the response, FastAPI resumes the `get_link_service` generator, the `with` block in
   `routes.py:24` exits, and `_service_scope`'s `finally` closes the connection (`main.py:25`).

The `POST /links` path is the same shape: body validated by `CreateLinkRequest` (`schemas.py:30-39`),
then `routes.py:35` → `LinkService.create_link` (`service.py:36-47`) → `RandomCodeGenerator.generate`
(`codes.py:9-10`) → `SqliteLinkRepository.add` (`repository.py:36-43`); `short_url` is built
from `request.base_url` at `routes.py:36`.

## 3. How the layers fit
| Layer | Module(s) | May depend on |
|---|---|---|
| HTTP | `routes.py`, `schemas.py` | routes → `service`, `schemas`, `domain`; schemas → nothing in the package |
| Business logic | `service.py` | `domain` only |
| Core | `domain.py` | nothing (stdlib) |
| Adapters (implement the ports) | `repository.py`, `codes.py` | `domain` |
| Infrastructure leaves | `db.py`, `config.py` | nothing in the package |
| Composition root | `main.py` | everything |

- Dependencies point **inward** to `domain.py`. `service.py` never imports `sqlite3`, FastAPI or
  Pydantic; `routes.py` never imports `repository`, `db`, `codes`, `config` or `main`.
- `repository.py` and `codes.py` implement the Protocols **structurally** — they don't import or
  subclass them; mypy checks the match where `main.py:23` passes them to `LinkService`.
- **Wiring happens in one place**: `main._service_scope` builds the object graph per request
  and `main.create_app` registers it on `app.state`. Routes reach it only through
  `get_link_service`, so `routes.py` stays free of concrete classes.
- The rules are enforced, not just documented: `tests/test_architecture.py` parses every module
  with `ast` and checks it against the `CONTRACTS` dict (LLD §0.3). Adding a new module without
  a contract fails `test_architecture_contract_covers_every_module`.

## 4. How to extend it
| I want to… | Touch these files | Pattern to copy |
|---|---|---|
| add an endpoint | `src/link_shortener/routes.py` (new function on `router`, declared **before** `GET /{code}`), `schemas.py` (request/response models), `service.py` (new method if there is logic), `tests/test_api_<name>.py` | `routes.get_stats` (sync `def`, `LinkServiceDep`, map `LinkNotFoundError` → 404 with `from err`); tests use the `client` fixture from `tests/conftest.py` |
| add a screen | none — the project is API only (SPEC §7, no UI) | — |
| swap a provider (e.g. DB) | new module, e.g. `src/link_shortener/<name>_repository.py`, implementing `add` / `get_by_code` / `increment_clicks`; change the construction in `main._service_scope`; add the module to `CONTRACTS` in `tests/test_architecture.py` | `repository.SqliteLinkRepository` (raise `DuplicateCodeError` on clash, return `bool` from `increment_clicks`); `tests/fakes.py::InMemoryLinkRepository` is a second, minimal implementation |
| change how codes are generated | new class with `generate() -> str` in `codes.py` (or a new module + contract), wired in `main._service_scope` | `codes.RandomCodeGenerator`; `tests/fakes.py::SequenceCodeGenerator` for deterministic tests |
| add a setting | `config.py` (`Settings` field + `from_env`), `.env.example`, README Configuration; read it in `main.create_app` | `Settings.from_env` handling of `LINKS_DB_PATH` (strip, blank → default) |
| add a column | `db.SCHEMA_SQL`, `repository.py` SQL + `_row_to_link`, `domain.Link` | No migrations exist (`CREATE TABLE IF NOT EXISTS`); existing files need a migration — treat as a change request |

Any new package is a Tier 1 decision (CONVENTIONS §1).

## 5. Tests
- **Where:** `tests/` (14 `test_*.py` modules, 115 tests at handover). One file per module for
  unit tests (`test_config.py`, `test_domain.py`, `test_codes.py`, `test_db.py`,
  `test_repository.py`, `test_service.py`, `test_schemas.py`), one per endpoint for HTTP tests
  (`test_api_create.py`, `test_api_redirect.py`, `test_api_stats.py`) plus
  `test_api_edge.py`, `test_persistence.py` (restart = two `create_app` on one file),
  `test_architecture.py` (layer contracts) and `test_start_script.py` (`.env` precedence).
- **Fixtures** (`tests/conftest.py`): `db_path` (`tmp_path / "links.db"`), `connection`
  (schema + open connection, closed after), `client` (`TestClient(create_app(Settings(db_path)),
  base_url="http://localhost:9000", follow_redirects=False)`). Every test gets its own SQLite
  file; nothing touches the real `links.db`.
- **How fakes are injected:** no patching. `tests/fakes.py` provides `InMemoryLinkRepository`,
  `SequenceCodeGenerator` and `fixed_clock`, which satisfy the domain ports; tests pass them to
  the `LinkService` constructor (see `make()` in `tests/test_service.py`). HTTP tests instead
  pass a `Settings` with a temp path to `create_app`.
- **`start.sh` test:** `tests/test_start_script.py` copies `start.sh` into `tmp_path`, puts a
  stub `uv` first on `PATH` that prints its arguments and environment, and runs the copy with an
  explicit environment — no server, no network.
- **Run:**
  - everything with the gate: `scripts/check.sh`
  - all tests: `uv run pytest`
  - one file: `uv run pytest tests/test_service.py -q`
  - one test: `uv run pytest tests/test_service.py::test_collision_retries -q`
  - one parametrised case: `uv run pytest "tests/test_architecture.py::test_architecture_module_imports_respect_layer_map[routes]"`

## 6. Talking points
**Three interesting design decisions**
1. **Per-request connection provider on `app.state`** (`main._service_scope`,
   `routes.get_link_service`). Each request gets its own autocommit SQLite connection, so there
   is no shared connection and no lock, and routes never import infrastructure. Trade-off: a
   connection open per request (cheap for SQLite) and a `cast` in `get_link_service` because
   `app.state` is untyped.
2. **Validity check in the service instead of a path pattern.** `{code}` is a plain `str`, and
   `LinkService` rejects invalid codes with `LinkNotFoundError`, so `/abc` returns `404` as SPEC
   asks (a FastAPI `pattern` would return `422`). Trade-off: the rule lives in `domain.py`, not
   in the OpenAPI schema.
3. **Architecture rules as a plain pytest test** (`tests/test_architecture.py`). The owner's
   package list excluded import-linter, so the layer map is an `ast` walk with a `CONTRACTS`
   dict, including a self-test and a "every module has a contract" check. Trade-off: less
   expressive than import-linter, but zero dependencies and it runs inside the normal suite.

**One problem hit during the build and how it was solved**
`start.sh` originally (T-04) sourced `.env` after the caller's environment, so a `.env` copied
from `.env.example` (`PORT=8000`) silently overrode `PORT=9000 ./start.sh`, breaking SPEC US-07.
Change request CR-1 (D-13) fixed it generically: snapshot every exported variable with
`compgen -e`, source `.env`, then restore any value `.env` changed (`start.sh:10-25`). Values
are kept in an array rather than re-`eval`ed, so spaces, quotes and `$` survive, and it stays
bash 3.2 compatible for macOS. `tests/test_start_script.py` proves it with a stub `uv` in under a
second. Remaining edge cases are listed in `docs/ARCHITECTURE.md` §8.

**What I'd do next with more time**
- Close the accepted `start.sh` gaps: fail loudly when `compgen` is missing, add the
  set-but-empty `PORT` test, and say "exported" in the README.
- Replace the deprecated httpx-based `TestClient` transport once an approved alternative exists
  (Tier 1), and rename the short test names to `test_<unit>_<condition>_<expected>`.
- Add a tiny migration mechanism (e.g. `PRAGMA user_version`) before the schema ever changes.
- Map `CodeGenerationError` to a clear `503` instead of a bare 500.
