"""HTTP request/response models."""

from datetime import UTC, datetime
from typing import Annotated, Final
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_serializer, field_validator

MAX_URL_LENGTH: Final = 2048
ALLOWED_SCHEMES: Final = frozenset({"http", "https"})
_TIMESTAMP_FORMAT: Final = "%Y-%m-%dT%H:%M:%SZ"


def _has_forbidden_char(value: str) -> bool:
    return any(ch <= " " or ch == "\x7f" for ch in value)


def _validate_http_url(value: str) -> None:
    try:
        parts = urlsplit(value)
        _ = parts.port
    except ValueError as err:
        raise ValueError("url is malformed") from err
    if parts.scheme.lower() not in ALLOWED_SCHEMES:
        raise ValueError("url scheme must be http or https")
    if not parts.hostname:
        raise ValueError("url must include a host")


class CreateLinkRequest(BaseModel):
    url: Annotated[str, Field(strict=True, min_length=1, max_length=MAX_URL_LENGTH)]

    @field_validator("url")
    @classmethod
    def _check_url(cls, value: str) -> str:
        if _has_forbidden_char(value):
            raise ValueError("url must not contain whitespace or control characters")
        _validate_http_url(value)
        return value


class CreateLinkResponse(BaseModel):
    code: str
    short_url: str


class LinkStats(BaseModel):
    url: str
    clicks: int
    created_at: datetime

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime) -> str:
        return value.astimezone(UTC).strftime(_TIMESTAMP_FORMAT)
