"""SQLite connection and schema."""

import sqlite3
from pathlib import Path
from typing import Final

BUSY_TIMEOUT_SECONDS: Final = 5.0

SCHEMA_SQL: Final = """
CREATE TABLE IF NOT EXISTS links (
    code       TEXT    PRIMARY KEY NOT NULL,
    url        TEXT    NOT NULL,
    clicks     INTEGER NOT NULL DEFAULT 0 CHECK (clicks >= 0),
    created_at TEXT    NOT NULL
)
"""


def connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(
        db_path, isolation_level=None, check_same_thread=False, timeout=BUSY_TIMEOUT_SECONDS
    )


def init_schema(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(db_path)
    try:
        connection.execute(SCHEMA_SQL)
    finally:
        connection.close()
