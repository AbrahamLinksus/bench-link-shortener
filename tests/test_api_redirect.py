import pytest
from fastapi.testclient import TestClient

URL = "https://example.com/page"
NOT_FOUND = {"detail": "Link not found"}


def _create(client: TestClient) -> str:
    return str(client.post("/links", json={"url": URL}).json()["code"])


def _clicks(client: TestClient, code: str) -> int:
    return int(client.get(f"/links/{code}/stats").json()["clicks"])


def test_follow_link_known_code_redirects_307_and_counts_clicks(client: TestClient) -> None:
    code = _create(client)
    assert _clicks(client, code) == 0

    first = client.get(f"/{code}")
    assert (first.status_code, first.headers["location"]) == (307, URL)
    assert _clicks(client, code) == 1

    client.get(f"/{code}")
    assert _clicks(client, code) == 2


def test_follow_link_unknown_code_returns_404(client: TestClient) -> None:
    response = client.get("/zzzzzz")

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


@pytest.mark.parametrize("path", ["/abc", "/links"])
def test_follow_link_non_code_path_returns_404(client: TestClient, path: str) -> None:
    response = client.get(path)

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


def test_follow_link_wrong_case_returns_404_without_click(client: TestClient) -> None:
    code = _create(client)
    swapped = code.swapcase()
    if swapped == code:
        pytest.skip("code has no letters")

    response = client.get(f"/{swapped}")

    assert response.status_code == 404
    assert _clicks(client, code) == 0
