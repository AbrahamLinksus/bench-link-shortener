import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import Thread

import pytest

from link_shortener.db import connect, init_schema
from link_shortener.domain import DuplicateCodeError, Link
from link_shortener.repository import SqliteLinkRepository

CREATED = datetime(2026, 11, 9, 10, 0, 0, tzinfo=UTC)


def make_link(code: str = "aZ3k9Q") -> Link:
    return Link(code=code, url="https://example.com/a?b=1", clicks=0, created_at=CREATED)


def test_repository_add_then_get_round_trips_link(connection: sqlite3.Connection) -> None:
    repo = SqliteLinkRepository(connection)
    repo.add(make_link())
    assert repo.get_by_code("aZ3k9Q") == make_link()


def test_repository_get_unknown_returns_none(connection: sqlite3.Connection) -> None:
    assert SqliteLinkRepository(connection).get_by_code("nope00") is None


def test_repository_add_duplicate_raises(connection: sqlite3.Connection) -> None:
    repo = SqliteLinkRepository(connection)
    repo.add(make_link())
    with pytest.raises(DuplicateCodeError):
        repo.add(make_link())


def test_repository_lookup_is_case_sensitive(connection: sqlite3.Connection) -> None:
    repo = SqliteLinkRepository(connection)
    repo.add(make_link("aZ3k9Q"))
    assert repo.get_by_code("az3k9q") is None


def test_repository_increment_known_and_unknown(connection: sqlite3.Connection) -> None:
    repo = SqliteLinkRepository(connection)
    repo.add(make_link())
    assert repo.increment_clicks("aZ3k9Q") is True
    assert repo.increment_clicks("zzzzzz") is False
    link = repo.get_by_code("aZ3k9Q")
    assert link is not None
    assert link.clicks == 1


def test_repository_concurrent_increments_lose_no_clicks(db_path: Path) -> None:
    init_schema(db_path)
    setup = connect(db_path)
    SqliteLinkRepository(setup).add(make_link())

    def work() -> None:
        conn = connect(db_path)
        try:
            repo = SqliteLinkRepository(conn)
            for _ in range(25):
                repo.increment_clicks("aZ3k9Q")
        finally:
            conn.close()

    threads = [Thread(target=work) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    link = SqliteLinkRepository(setup).get_by_code("aZ3k9Q")
    setup.close()
    assert link is not None
    assert link.clicks == 200


def test_repository_reopen_file_keeps_link_and_clicks(db_path: Path) -> None:
    init_schema(db_path)
    first = connect(db_path)
    repo = SqliteLinkRepository(first)
    repo.add(make_link())
    repo.increment_clicks("aZ3k9Q")
    repo.increment_clicks("aZ3k9Q")
    first.close()
    second = connect(db_path)
    link = SqliteLinkRepository(second).get_by_code("aZ3k9Q")
    second.close()
    assert link == Link("aZ3k9Q", "https://example.com/a?b=1", 2, CREATED)


def test_repository_timestamp_is_stored_as_utc_z_string(connection: sqlite3.Connection) -> None:
    SqliteLinkRepository(connection).add(make_link())
    row = connection.execute("SELECT created_at FROM links").fetchone()
    assert row == ("2026-11-09T10:00:00Z",)


def test_repository_round_trip_returns_aware_utc(connection: sqlite3.Connection) -> None:
    repo = SqliteLinkRepository(connection)
    repo.add(make_link())
    link = repo.get_by_code("aZ3k9Q")
    assert link is not None
    assert link.created_at == CREATED
    assert link.created_at.tzinfo is UTC


def test_repository_unknown_increment_changes_nothing(connection: sqlite3.Connection) -> None:
    repo = SqliteLinkRepository(connection)
    repo.add(make_link())
    assert repo.increment_clicks("zzzzzz") is False
    link = repo.get_by_code("aZ3k9Q")
    assert link is not None
    assert link.clicks == 0


def test_repository_duplicate_keeps_original(connection: sqlite3.Connection) -> None:
    repo = SqliteLinkRepository(connection)
    repo.add(make_link())
    with pytest.raises(DuplicateCodeError) as info:
        repo.add(Link("aZ3k9Q", "https://other.example", 0, CREATED))
    assert info.value.code == "aZ3k9Q"
    assert repo.get_by_code("aZ3k9Q") == make_link()


def test_repository_codes_differing_only_by_case_coexist(connection: sqlite3.Connection) -> None:
    repo = SqliteLinkRepository(connection)
    repo.add(make_link("aZ3k9Q"))
    repo.add(make_link("az3k9q"))
    assert repo.increment_clicks("az3k9q") is True
    upper = repo.get_by_code("aZ3k9Q")
    assert upper is not None
    assert upper.clicks == 0


def test_repository_sql_injection_code_is_inert(connection: sqlite3.Connection) -> None:
    repo = SqliteLinkRepository(connection)
    repo.add(make_link())
    assert repo.get_by_code("' OR '1'='1") is None
    assert repo.increment_clicks("x' OR '1'='1") is False
