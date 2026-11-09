import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from link_shortener.config import Settings
from link_shortener.main import create_app

URL = "https://example.com/page"


def test_restart_keeps_link_and_clicks(db_path: Path) -> None:
    with TestClient(create_app(Settings(db_path)), follow_redirects=False) as app_a:
        code = app_a.post("/links", json={"url": URL}).json()["code"]
        app_a.get(f"/{code}")
        app_a.get(f"/{code}")

    with TestClient(create_app(Settings(db_path)), follow_redirects=False) as app_b:
        stats = app_b.get(f"/links/{code}/stats").json()
        redirect = app_b.get(f"/{code}")

    assert stats["clicks"] == 2
    assert stats["url"] == URL
    assert (redirect.status_code, redirect.headers["location"]) == (307, URL)


def test_import_main_creates_no_database_file(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import link_shortener.main as m; assert not hasattr(m, 'app')"],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "links.db").exists()
