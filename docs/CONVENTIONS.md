# CONVENTIONS — {{project}}

> Written by the Architect with the LLD and approved by the owner. Every coder reads this
> before every task; the Tester enforces section 6 automatically, and the Reviewer
> enforces sections 2–5.

## 1. Stack-specific style
- Python: PEP 8 via ruff; type hints on every public function; Pydantic models at every I/O boundary.
- TypeScript: strict mode; no `any`; named exports; React function components + hooks.
- {{project-specific additions}}

## 2. Layering (dependencies point inward only)
```
api/routes  →  services  →  repositories / clients  →  models / domain
(HTTP only)    (business     (DB, HTTP, LLM, vector     (pure data,
               logic)         store; all I/O here)       no I/O)
```
- Routes never import repositories or clients directly.
- Services never import web-framework objects (Request, Response).
- Domain/models import nothing from the other layers.
- {{frontend equivalent: pages → components → hooks → api client}}

## 3. SOLID: what it means in this project

| Principle | Rule here |
|---|---|
| **S**ingle responsibility | One reason to change per class/module. No I/O mixed with business logic. Services named by capability (`IngestionService`), not `Manager`/`Utils`. |
| **O**pen/closed | Variation points listed in the LLD get an interface (Protocol/ABC); new providers are new classes, never new `elif` branches. |
| **L**iskov substitution | Implementations honour the interface: same input acceptance, same return types, no `NotImplementedError` stubs. |
| **I**nterface segregation | Small interfaces per client need; split any interface where clients use only part of it. |
| **D**ependency inversion | Services receive dependencies via constructor or framework injection (`Depends`); they never construct DB/HTTP/LLM clients themselves. Wiring happens in one composition root (`app/container.py` or `main.py`). |

**Where to abstract** (and where not): abstractions are required for external services
(DB, LLM, embeddings, vector store, third-party APIs) and the variation points named in
the LLD. Elsewhere, plain functions and concrete classes are fine. Don't add an interface
with a single implementation and no planned second one.

## 4. Limits
- Function ≤ 40 lines; cyclomatic complexity ≤ 10; parameters ≤ 5 (use a dataclass/model beyond that).
- File ≤ 300 lines; class ≤ 200 lines.
- No commented-out code, no `print` debugging (use the logger), no TODOs without a task ID.

## 5. Errors, logging, config, tests
- Errors: custom exception types per domain; map them to HTTP errors only in the route layer.
- Logging: structured (key=value or JSON), no secrets or personal data in logs.
- Config: all settings from env via a typed settings object (pydantic-settings / zod); no magic constants.
- Tests: Arrange-Act-Assert, one behaviour per test, names `test_<unit>_<condition>_<expected>`;
  external services faked through their interfaces, never patched deep inside code.

## 6. Automated checks (`scripts/check.sh` must pass; Tester runs it on every task)

| Check | Python | TypeScript |
|---|---|---|
| Lint + format | `ruff check` + `ruff format --check` (rules: E,F,W,I,N,UP,B,SIM,C90,PL,RUF) | `eslint` (typescript-eslint strict) + `prettier --check` |
| Types | `mypy --strict` (or pyright strict) | `tsc --noEmit` (strict) |
| Complexity / size | ruff `C901` (max 10), `PLR0913` (max 5 args), `PLR0915`; `radon cc -n C` | eslint `complexity: 10`, `max-lines-per-function: 40`, `max-params: 5` |
| Layer rules | `lint-imports` (import-linter contracts for section 2) | `depcruise` (dependency-cruiser rules for section 2) |
| Tests + coverage | `pytest --cov --cov-fail-under={{80}}` | `vitest run --coverage` |
