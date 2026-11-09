"""Pure core: entity, errors, ports and clock."""

import re
import string
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final, Protocol

CODE_LENGTH: Final = 6
CODE_ALPHABET: Final = string.ascii_letters + string.digits
_CODE_RE: Final = re.compile(r"[A-Za-z0-9]{6}")


def is_valid_code(code: str) -> bool:
    return _CODE_RE.fullmatch(code) is not None


@dataclass(frozen=True, slots=True)
class Link:
    code: str
    url: str
    clicks: int
    created_at: datetime


class LinkNotFoundError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(f"link not found: {code}")
        self.code = code


class DuplicateCodeError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(f"duplicate code: {code}")
        self.code = code


class CodeGenerationError(Exception):
    def __init__(self, attempts: int) -> None:
        super().__init__(f"could not generate a unique code after {attempts} attempts")
        self.attempts = attempts


Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


class LinkRepository(Protocol):
    def add(self, link: Link) -> None: ...

    def get_by_code(self, code: str) -> Link | None: ...

    def increment_clicks(self, code: str) -> bool: ...


class CodeGenerator(Protocol):
    def generate(self) -> str: ...
