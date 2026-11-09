import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from link_shortener.config import Settings
from link_shortener.db import connect, init_schema
from link_shortener.main import create_app


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "links.db"


@pytest.fixture
def connection(db_path: Path) -> Iterator[sqlite3.Connection]:
    init_schema(db_path)
    conn = connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def client(db_path: Path) -> Iterator[TestClient]:
    app = create_app(Settings(db_path))
    with TestClient(app, base_url="http://localhost:9000", follow_redirects=False) as c:
        yield c
