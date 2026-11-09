"""Application settings read from the environment."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Self

DB_PATH_ENV: Final = "LINKS_DB_PATH"
DEFAULT_DB_PATH: Final = Path("links.db")


@dataclass(frozen=True, slots=True)
class Settings:
    db_path: Path

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Self:
        """Build settings; missing or blank LINKS_DB_PATH falls back to the default."""
        env = os.environ if environ is None else environ
        raw = env.get(DB_PATH_ENV, "").strip()
        return cls(db_path=Path(raw) if raw else DEFAULT_DB_PATH)
