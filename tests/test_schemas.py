import json

import pytest
from pydantic import ValidationError

from link_shortener.schemas import CreateLinkRequest, LinkStats
from tests.fakes import FIXED_NOW


@pytest.mark.parametrize(
    "url", ["http://example.com", "https://Example.com/Path?q=1#f", "HTTP://host:8080"]
)
def test_valid_unchanged(url: str) -> None:
    assert CreateLinkRequest(url=url).url == url


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/x",
        "javascript:alert(1)",
        "not a url",
        "http://",
        "https:///path",
        "http://exa mple.com",
        "http://a.com/\n",
        "",
        "http://" + "a" * 2042,
        "http://host:99999",
        "http://[::1",
    ],
)
def test_invalid_rejected(url: str) -> None:
    with pytest.raises(ValidationError):
        CreateLinkRequest(url=url)


def test_length_boundary() -> None:
    url = "http://" + "a" * 2041
    assert len(url) == 2048
    assert CreateLinkRequest(url=url).url == url
    with pytest.raises(ValidationError):
        CreateLinkRequest(url=url + "a")


def test_non_string_rejected() -> None:
    with pytest.raises(ValidationError):
        CreateLinkRequest.model_validate({"url": 123})


def test_stats_created_at_format() -> None:
    stats = LinkStats(url="https://a.com", clicks=3, created_at=FIXED_NOW)
    assert json.loads(stats.model_dump_json())["created_at"] == "2026-11-09T10:00:00Z"


@pytest.mark.parametrize(
    "url", ["http://[::1]:8080/x", "https://[2001:db8::1]/", "http://host:65535", "HTTPS://A.com"]
)
def test_ipv6_ports_uppercase_scheme(url: str) -> None:
    assert CreateLinkRequest(url=url).url == url
