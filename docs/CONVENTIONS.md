# CONVENTIONS — bench-link-shortener

> Written by the Architect with the LLD and approved by the owner. Every coder reads this
> before every task; the Tester enforces section 6 automatically, and the Reviewer
> enforces sections 2–5. Section references (§n) point at `docs/LLD.md`.

## 1. Stack-specific style
- Python 3.12+, PEP 8 via ruff (`line-length = 100`), formatted with `ruff format`.
- Type hints on **every** function (public and private) and test; `mypy --strict` clean. No `Any` leaking out of a function, no `# type: ignore` without an error code and a one-line reason.
- Modern syntax: `X | None`, built-in generics (`list[str]`), `collections.abc` for `Callable` / `Iterator` / `Mapping`, `typing.Final` for module constants, `Protocol` for ports.
- Pydantic models only at the HTTP boundary (§7). Inside the app use frozen `dataclass(slots=True)` (`Link`, `Settings`).
- FastAPI: sync `def` endpoints; dependencies via `Annotated[T, Depends(...)]`, never `= Depends()` defaults; no module-level `app` (factory only, §9).
- SQL: parameterised (`?`) only, written only in `repository.py` / `db.py`. No f-strings or `%` in SQL.
- Only the packages in LLD §0.4. **No new runtime or dev package** without the owner's approval (Tier 1).
- Names: modules lowercase nouns (`service.py`), classes by capability (`LinkService`, `SqliteLinkRepository`), exceptions end in `Error`.

## 2. Layering (dependencies point inward only)
```
routes (§8)  →  service (§6)  →  domain (§2: Link, errors, Protocols, clock)
(HTTP only)     (business         ▲
                 logic)           │ implements ports
                     repository (§5, all SQL)   codes (§3)
schemas (§7): HTTP models, used only by routes.   config (§1), db (§4): leaves.
main (§9): the only composition root.
```
- Routes never import `repository`, `db`, `codes`, `config` or `sqlite3`; they get a `LinkService` via `get_link_service` (§8).
- The service never imports FastAPI, Starlette, Pydantic or `sqlite3`; it only knows the §2 Protocols.
- `domain` imports nothing from the package and no framework or I/O module.
- `repository` never knows about HTTP (no FastAPI / Pydantic).
- The exact allowed / forbidden imports per module are the table in LLD §0.3, enforced by `tests/test_architecture.py`.
- Frontend: none (API only).

## 3. SOLID: what it means in this project

| Principle | Rule here |
|---|---|
| **S**ingle responsibility | One module per concern exactly as LLD §0.2. No I/O in `service` / `domain`; no business rules in `routes` / `repository`. |
| **O**pen/closed | The variation points are `LinkRepository` and `CodeGenerator` (Protocols in §2) and `Clock` (callable). New storage or code strategies are new classes, never `if` branches in the service. |
| **L**iskov substitution | `SqliteLinkRepository`, `RandomCodeGenerator` and the test fakes honour the Protocols exactly: `add` raises `DuplicateCodeError` on clash, `increment_clicks` returns `bool`, `get_by_code` returns `None` when missing. |
| **I**nterface segregation | Ports stay this small (3 methods / 1 method). Don't add methods a caller doesn't use. |
| **D**ependency inversion | `LinkService` receives repository, generator and clock in its constructor; it never opens connections or calls `secrets` / `datetime.now` itself. All wiring lives in `main.py` (§9). |

**Where to abstract** (and where not): only the three variation points above. `config`,
`db`, `schemas` and `routes` are plain functions / concrete classes. Don't add an interface
with a single implementation and no planned second one (the test fake counts as the second).

## 4. Limits
- Function ≤ 40 lines; cyclomatic complexity ≤ 10; parameters ≤ 5 (use a dataclass beyond that).
- File ≤ 300 lines; class ≤ 200 lines.
- No commented-out code, no `print` (use `logging.getLogger(__name__)`), no TODOs without a task ID.

## 5. Errors, logging, config, tests
- Errors: domain exceptions live in `domain.py` (`LinkNotFoundError`, `DuplicateCodeError`, `CodeGenerationError`). Translate `sqlite3.IntegrityError` → `DuplicateCodeError` in the repository. Map to HTTP (`404 {"detail": "Link not found"}`) **only** in routes, with `raise … from err`. Never catch bare `Exception`.
- Logging: stdlib `logging`, `key=value` messages (`"link_created code=%s"`), lazy `%` args. Never log URLs or request bodies.
- Config: all settings from env through `Settings.from_env()` (§1), a frozen dataclass (pydantic-settings is not allowed). No magic constants: name them `Final` at module top (`CODE_LENGTH`, `MAX_URL_LENGTH`, `NOT_FOUND_DETAIL`).
- Tests: Arrange-Act-Assert, one behaviour per test, names `test_<unit>_<condition>_<expected>`. Each test uses its own `tmp_path` SQLite file. Collaborators are faked through the §2 Protocols (`tests/fakes.py`), never patched inside production modules. Redirect tests use `follow_redirects=False`. Every SPEC §5 row has at least one test.

## 6. Automated checks (`scripts/check.sh` must pass; Tester runs it on every task)

| Check | Command (Python only) |
|---|---|
| Lint | `uv run ruff check .` (rules: E,F,W,I,N,UP,B,SIM,C90,PL,RUF) |
| Format | `uv run ruff format --check .` |
| Types | `uv run mypy --strict` (paths from `[tool.mypy] files`) |
| Complexity / size | ruff `C901` (max 10), `PLR0913` (max 5 args), `PLR0911/0912/0915`. (radon is not allowed by the owner's package list.) |
| Layer rules | `tests/test_architecture.py` (stdlib `ast`, contracts in LLD §0.3) — runs inside pytest. (import-linter is not allowed.) |
| Tests + coverage | `uv run pytest -q --cov=link_shortener --cov-report=term-missing --cov-fail-under=85`; with `CHECK_NO_COVERAGE=1` → `uv run pytest -q` |
