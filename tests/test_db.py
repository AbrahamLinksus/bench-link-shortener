import sqlite3
from pathlib import Path
from threading import Thread

import pytest

from link_shortener.db import connect, init_schema


def _tables(path: Path) -> list[tuple[str]]:
    conn = connect(path)
    try:
        return conn.execute("SELECT name FROM sqlite_master WHERE name = 'links'").fetchall()
    finally:
        conn.close()


def test_init_schema_creates_table(db_path: Path) -> None:
    init_schema(db_path)
    assert _tables(db_path) == [("links",)]


def test_init_schema_creates_parent_directory(tmp_path: Path) -> None:
    path = tmp_path / "a" / "b" / "links.db"
    init_schema(path)
    assert _tables(path) == [("links",)]


def test_init_schema_is_idempotent_and_keeps_data(db_path: Path) -> None:
    init_schema(db_path)
    conn = connect(db_path)
    conn.execute("INSERT INTO links VALUES ('aZ3k9Q', 'u', 0, 't')")
    conn.close()
    init_schema(db_path)
    conn = connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM links").fetchone() == (1,)
    conn.close()


def test_connect_is_autocommit(db_path: Path) -> None:
    init_schema(db_path)
    conn = connect(db_path)
    assert conn.isolation_level is None
    conn.close()


def test_connection_usable_from_another_thread(connection: sqlite3.Connection) -> None:
    result: list[object] = []
    t = Thread(target=lambda: result.append(connection.execute("SELECT 1").fetchone()))
    t.start()
    t.join()
    assert result == [(1,)]


def test_negative_clicks_rejected(connection: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("INSERT INTO links VALUES ('aZ3k9Q', 'u', -1, 't')")


def test_unwritable_path_fails_loudly(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("x")
    with pytest.raises(OSError):
        init_schema(blocker / "links.db")
