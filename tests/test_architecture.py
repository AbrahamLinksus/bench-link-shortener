import ast
from pathlib import Path

import pytest

PKG = "link_shortener"
SRC = Path(__file__).resolve().parent.parent / "src" / PKG
FRAMEWORK = {"fastapi", "starlette", "pydantic"}
ALL = {"config", "domain", "codes", "db", "repository", "service", "schemas", "routes", "main"}

# module -> (allowed internal modules, forbidden imports)
CONTRACTS: dict[str, tuple[set[str], set[str]]] = {
    "config": (set(), FRAMEWORK | {"sqlite3"}),
    "domain": (set(), FRAMEWORK | {"sqlite3"}),
    "codes": ({"domain"}, FRAMEWORK | {"sqlite3"}),
    "db": (set(), FRAMEWORK),
    "repository": ({"domain"}, FRAMEWORK),
    "service": ({"domain"}, FRAMEWORK | {"sqlite3"}),
    "schemas": (set(), {"fastapi", "starlette", "sqlite3"}),
    "routes": (
        {"domain", "service", "schemas"},
        {"sqlite3"} | {f"{PKG}.{m}" for m in ("repository", "db", "codes", "config", "main")},
    ),
    "main": (ALL, set()),
}


def _imports(path: Path) -> tuple[set[str], set[str]]:
    """Return (internal module names, all absolute dotted import names)."""
    internal: set[str] = set()
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                internal.add("<relative>")
            names.add(base)
            if base == PKG:
                names.update(f"{PKG}.{alias.name}" for alias in node.names)
    for name in names:
        if name.startswith(f"{PKG}."):
            internal.add(name.split(".")[1])
    return internal, names


def test_architecture_contract_covers_every_module() -> None:
    modules = {p.stem for p in SRC.glob("*.py") if p.stem != "__init__"}
    assert modules == set(CONTRACTS)


@pytest.mark.parametrize("module", sorted(CONTRACTS))
def test_architecture_module_imports_respect_layer_map(module: str) -> None:
    allowed, forbidden = CONTRACTS[module]
    internal, names = _imports(SRC / f"{module}.py")
    assert internal <= allowed, f"{module} imports {internal - allowed}"
    for name in names:
        for bad in forbidden:
            assert name != bad and not name.startswith(f"{bad}."), f"{module} imports {name}"


def test_architecture_checker_detects_a_violation(tmp_path: Path) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text("import sqlite3\nfrom link_shortener import service\n")
    internal, names = _imports(bad)
    assert "service" in internal
    assert "sqlite3" in names
