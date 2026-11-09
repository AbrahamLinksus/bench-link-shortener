"""Domain logic: create links, resolve-and-count, stats."""

import logging
from datetime import UTC
from typing import Final

from link_shortener.domain import (
    Clock,
    CodeGenerationError,
    CodeGenerator,
    DuplicateCodeError,
    Link,
    LinkNotFoundError,
    LinkRepository,
    is_valid_code,
)

DEFAULT_MAX_ATTEMPTS: Final = 10

logger = logging.getLogger(__name__)


class LinkService:
    def __init__(
        self,
        repository: LinkRepository,
        code_generator: CodeGenerator,
        clock: Clock,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> None:
        self._repository = repository
        self._code_generator = code_generator
        self._clock = clock
        self._max_attempts = max_attempts

    def create_link(self, url: str) -> Link:
        now = self._clock().astimezone(UTC).replace(microsecond=0)
        for attempt in range(1, self._max_attempts + 1):
            link = Link(code=self._code_generator.generate(), url=url, clicks=0, created_at=now)
            try:
                self._repository.add(link)
            except DuplicateCodeError:
                logger.warning("code_collision code=%s attempt=%d", link.code, attempt)
                continue
            logger.info("link_created code=%s", link.code)
            return link
        raise CodeGenerationError(self._max_attempts)

    def resolve_and_count(self, code: str) -> str:
        if not is_valid_code(code) or not self._repository.increment_clicks(code):
            raise LinkNotFoundError(code)
        return self.get_stats(code).url

    def get_stats(self, code: str) -> Link:
        if not is_valid_code(code):
            raise LinkNotFoundError(code)
        link = self._repository.get_by_code(code)
        if link is None:
            raise LinkNotFoundError(code)
        return link
