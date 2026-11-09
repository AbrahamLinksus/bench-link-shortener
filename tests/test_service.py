import pytest

from link_shortener.domain import CodeGenerationError, LinkNotFoundError
from link_shortener.service import LinkService
from tests.fakes import FIXED_NOW, InMemoryLinkRepository, SequenceCodeGenerator, fixed_clock


def make(codes: list[str]) -> tuple[LinkService, InMemoryLinkRepository]:
    repo = InMemoryLinkRepository()
    return LinkService(repo, SequenceCodeGenerator(codes), fixed_clock), repo


def test_create_stamps_clock_and_zero_clicks() -> None:
    service, _ = make(["aaaaaa"])
    link = service.create_link("https://example.com")
    assert (link.code, link.clicks, link.created_at) == ("aaaaaa", 0, FIXED_NOW)


def test_collision_retries() -> None:
    service, _ = make(["aaaaaa", "aaaaaa", "bbbbbb"])
    service.create_link("https://a.com")
    assert service.create_link("https://b.com").code == "bbbbbb"


def test_exhaustion() -> None:
    service, _ = make(["aaaaaa"] * 11)
    service.create_link("https://a.com")
    with pytest.raises(CodeGenerationError):
        service.create_link("https://b.com")


def test_resolve_increments_once() -> None:
    service, repo = make(["aaaaaa"])
    service.create_link("https://a.com")
    assert service.resolve_and_count("aaaaaa") == "https://a.com"
    assert service.get_stats("aaaaaa").clicks == 1
    assert repo.increment_calls == 1


@pytest.mark.parametrize("code", ["zzzzzz", "abc", "aaaaa!", "AAAAAA"])
def test_bad_code_not_found_no_increment(code: str) -> None:
    service, repo = make(["aaaaaa"])
    service.create_link("https://a.com")
    with pytest.raises(LinkNotFoundError):
        service.resolve_and_count(code)
    with pytest.raises(LinkNotFoundError):
        service.get_stats(code)
    assert repo.increment_calls == 0


def test_stats_do_not_count() -> None:
    service, _ = make(["aaaaaa"])
    service.create_link("https://a.com")
    service.get_stats("aaaaaa")
    assert service.get_stats("aaaaaa").clicks == 0


def test_retry_boundary_tenth_attempt_succeeds() -> None:
    service, _ = make(["aaaaaa"] + ["aaaaaa"] * 9 + ["bbbbbb"])
    service.create_link("https://a.com")
    assert service.create_link("https://b.com").code == "bbbbbb"


def test_exhaustion_consumes_exactly_ten_codes() -> None:
    codes = SequenceCodeGenerator(["aaaaaa"] * 11 + ["bbbbbb"])
    service = LinkService(InMemoryLinkRepository(), codes, fixed_clock)
    service.create_link("https://a.com")
    with pytest.raises(CodeGenerationError):
        service.create_link("https://b.com")
    assert codes.generate() == "bbbbbb"
