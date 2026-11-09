import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from link_shortener.db import connect, init_schema


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
