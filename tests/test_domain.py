from datetime import UTC, datetime

import pytest

from link_shortener.domain import (
    CodeGenerationError,
    DuplicateCodeError,
    Link,
    LinkNotFoundError,
    is_valid_code,
    utc_now,
)


@pytest.mark.parametrize("code", ["aZ3k9Q", "000000", "ABCDEF", "abcdef"])
def test_is_valid_code_accepts_six_alphanumerics(code: str) -> None:
    assert is_valid_code(code)


@pytest.mark.parametrize("code", ["", "abcde", "abcdefg", "abc-12", "abc 12", "abcdé1", "abcde\n"])
def test_is_valid_code_rejects_bad_codes(code: str) -> None:
    assert not is_valid_code(code)


def test_utc_now_is_utc_without_microseconds() -> None:
    now = utc_now()
    assert now.microsecond == 0
    assert now.utcoffset() is not None
    assert now.tzinfo is UTC


def test_link_is_immutable() -> None:
    link = Link("aZ3k9Q", "https://e.com", 0, datetime(2026, 11, 9, tzinfo=UTC))
    with pytest.raises(AttributeError):
        link.clicks = 5  # type: ignore[misc]


def test_errors_keep_their_payload() -> None:
    assert LinkNotFoundError("abc").code == "abc"
    assert DuplicateCodeError("abc").code == "abc"
    assert CodeGenerationError(10).attempts == 10
