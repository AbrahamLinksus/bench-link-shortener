"""Composition root: builds the FastAPI app."""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import partial
from pathlib import Path

from fastapi import FastAPI

from link_shortener.codes import RandomCodeGenerator
from link_shortener.config import Settings
from link_shortener.db import connect, init_schema
from link_shortener.domain import utc_now
from link_shortener.repository import SqliteLinkRepository
from link_shortener.routes import SERVICE_PROVIDER_KEY, router
from link_shortener.service import LinkService


@contextmanager
def _service_scope(db_path: Path) -> Iterator[LinkService]:
    connection = connect(db_path)
    try:
        yield LinkService(SqliteLinkRepository(connection), RandomCodeGenerator(), utc_now)
    finally:
        connection.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = Settings.from_env() if settings is None else settings
    init_schema(settings.db_path)
    app = FastAPI(title="bench-link-shortener")
    setattr(app.state, SERVICE_PROVIDER_KEY, partial(_service_scope, settings.db_path))
    app.include_router(router)
    return app
