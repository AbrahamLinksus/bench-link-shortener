"""HTTP layer: maps requests to LinkService calls."""

from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from typing import Annotated, Final, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from link_shortener.domain import LinkNotFoundError
from link_shortener.schemas import CreateLinkRequest, CreateLinkResponse, LinkStats
from link_shortener.service import LinkService

NOT_FOUND_DETAIL: Final = "Link not found"
SERVICE_PROVIDER_KEY: Final = "link_service_provider"

ServiceProvider = Callable[[], AbstractContextManager[LinkService]]

router = APIRouter()


def get_link_service(request: Request) -> Iterator[LinkService]:
    provider = cast(ServiceProvider, getattr(request.app.state, SERVICE_PROVIDER_KEY))
    with provider() as service:
        yield service


LinkServiceDep = Annotated[LinkService, Depends(get_link_service)]


@router.post("/links", status_code=201, response_model=CreateLinkResponse)
def create_link(
    body: CreateLinkRequest, request: Request, service: LinkServiceDep
) -> CreateLinkResponse:
    link = service.create_link(body.url)
    return CreateLinkResponse(code=link.code, short_url=f"{request.base_url}{link.code}")


@router.get("/links/{code}/stats", response_model=LinkStats)
def get_stats(code: str, service: LinkServiceDep) -> LinkStats:
    try:
        link = service.get_stats(code)
    except LinkNotFoundError as err:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL) from err
    return LinkStats(url=link.url, clicks=link.clicks, created_at=link.created_at)


@router.get("/{code}", status_code=307, response_class=RedirectResponse)
def follow_link(code: str, service: LinkServiceDep) -> RedirectResponse:
    try:
        url = service.resolve_and_count(code)
    except LinkNotFoundError as err:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL) from err
    return RedirectResponse(url, status_code=307)
