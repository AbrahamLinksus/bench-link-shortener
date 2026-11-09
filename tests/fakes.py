"""Test doubles implementing the domain ports."""

from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime
from typing import Final

from link_shortener.domain import DuplicateCodeError, Link

FIXED_NOW: Final = datetime(2026, 11, 9, 10, 0, 0, tzinfo=UTC)


def fixed_clock() -> datetime:
    return FIXED_NOW


class InMemoryLinkRepository:
    def __init__(self) -> None:
        self._links: dict[str, Link] = {}
        self.increment_calls = 0

    def add(self, link: Link) -> None:
        if link.code in self._links:
            raise DuplicateCodeError(link.code)
        self._links[link.code] = link

    def get_by_code(self, code: str) -> Link | None:
        return self._links.get(code)

    def increment_clicks(self, code: str) -> bool:
        link = self._links.get(code)
        if link is None:
            return False
        self.increment_calls += 1
        self._links[code] = replace(link, clicks=link.clicks + 1)
        return True


class SequenceCodeGenerator:
    def __init__(self, codes: Sequence[str]) -> None:
        self._codes = iter(codes)

    def generate(self) -> str:
        return next(self._codes)
