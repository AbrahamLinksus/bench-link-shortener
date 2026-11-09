"""SQLite implementation of the LinkRepository port."""

import sqlite3
from datetime import UTC, datetime
from typing import Final

from link_shortener.domain import DuplicateCodeError, Link

TIMESTAMP_FORMAT: Final = "%Y-%m-%dT%H:%M:%SZ"


def _to_row_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).strftime(TIMESTAMP_FORMAT)


def _from_row_timestamp(value: str) -> datetime:
    return datetime.strptime(value, TIMESTAMP_FORMAT).replace(tzinfo=UTC)


def _row_to_link(row: tuple[object, ...]) -> Link:
    code, url, clicks, created_at = row
    if not (
        isinstance(code, str)
        and isinstance(url, str)
        and isinstance(clicks, int)
        and isinstance(created_at, str)
    ):
        raise TypeError("unexpected column types in links row")
    return Link(code=code, url=url, clicks=clicks, created_at=_from_row_timestamp(created_at))


class SqliteLinkRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, link: Link) -> None:
        try:
            self._connection.execute(
                "INSERT INTO links (code, url, clicks, created_at) VALUES (?, ?, ?, ?)",
                (link.code, link.url, link.clicks, _to_row_timestamp(link.created_at)),
            )
        except sqlite3.IntegrityError as err:
            raise DuplicateCodeError(link.code) from err

    def get_by_code(self, code: str) -> Link | None:
        row = self._connection.execute(
            "SELECT code, url, clicks, created_at FROM links WHERE code = ?", (code,)
        ).fetchone()
        return None if row is None else _row_to_link(tuple(row))

    def increment_clicks(self, code: str) -> bool:
        cursor = self._connection.execute(
            "UPDATE links SET clicks = clicks + 1 WHERE code = ?", (code,)
        )
        return cursor.rowcount == 1
