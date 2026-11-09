import re

from fastapi.testclient import TestClient

URL = "https://example.com/page"


def test_get_stats_known_code_returns_body_without_counting(client: TestClient) -> None:
    code = client.post("/links", json={"url": URL}).json()["code"]

    first = client.get(f"/links/{code}/stats")
    second = client.get(f"/links/{code}/stats")

    body = first.json()
    assert first.status_code == 200
    assert set(body) == {"url", "clicks", "created_at"}
    assert body["url"] == URL
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", body["created_at"])
    assert second.json()["clicks"] == 0


def test_get_stats_after_clicks_reports_count(client: TestClient) -> None:
    code = client.post("/links", json={"url": URL}).json()["code"]
    for _ in range(3):
        client.get(f"/{code}")

    assert client.get(f"/links/{code}/stats").json()["clicks"] == 3


def test_get_stats_unknown_code_returns_404(client: TestClient) -> None:
    response = client.get("/links/zzzzzz/stats")

    assert response.status_code == 404
    assert response.json() == {"detail": "Link not found"}
