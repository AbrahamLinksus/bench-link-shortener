"""start.sh environment precedence (LLD §10.1 / §11.5): shell wins over .env."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")

STUB_UV = """#!/bin/sh
if [ "$1" = "sync" ]; then exit 0; fi
printf 'ARGS=%s\\n' "$*"
env
"""


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    shutil.copy(PROJECT_ROOT / "start.sh", tmp_path / "start.sh")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "uv"
    stub.write_text(STUB_UV)
    stub.chmod(0o755)
    return tmp_path


def run_start(sandbox: Path, dotenv: str | None, env: dict[str, str]) -> tuple[str, dict[str, str]]:
    if dotenv is not None:
        (sandbox / ".env").write_text(dotenv)
    result = subprocess.run(
        ["bash", str(sandbox / "start.sh")],
        env={
            "PATH": f"{sandbox / 'bin'}{os.pathsep}{os.environ['PATH']}",
            "HOME": str(sandbox),
            **env,
        },
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    args = ""
    child_env: dict[str, str] = {}
    for line in result.stdout.split("\n"):
        if line.startswith("ARGS="):
            args = line
        elif "=" in line:
            key, _, value = line.partition("=")
            child_env[key] = value
    return args, child_env


def test_start_script_shell_env_set_overrides_dotenv(sandbox: Path) -> None:
    shell_db = "shell dir/$x'y.db"
    args, env = run_start(
        sandbox,
        "PORT=8000\nLINKS_DB_PATH=dotenv.db\nCR1_EXTRA=dotenv\n",
        {"PORT": "9000", "LINKS_DB_PATH": shell_db, "CR1_EXTRA": "shell"},
    )
    assert args.endswith("--port 9000")
    assert env["LINKS_DB_PATH"] == shell_db
    assert env["CR1_EXTRA"] == "shell"


def test_start_script_shell_env_unset_uses_dotenv(sandbox: Path) -> None:
    args, env = run_start(
        sandbox,
        "PORT=8123\nLINKS_DB_PATH=dotenv.db\nCR1_DOTENV_ONLY=yes\n",
        {},
    )
    assert args.endswith("--port 8123")
    assert env["LINKS_DB_PATH"] == "dotenv.db"
    assert env["CR1_DOTENV_ONLY"] == "yes"


def test_start_script_without_dotenv_uses_default_port(sandbox: Path) -> None:
    args, env = run_start(sandbox, None, {})
    assert args.endswith("--port 8000")
    assert "LINKS_DB_PATH" not in env


def test_start_script_helper_variables_not_leaked(sandbox: Path) -> None:
    _, env = run_start(sandbox, "PORT=8000\n", {"PORT": "9000"})
    assert not [key for key in env if key.startswith("_dotenv_")]
