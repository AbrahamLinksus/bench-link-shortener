import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

URL = "https://example.com/page"
NOT_FOUND = {"detail": "Link not found"}


def _create_with_letters(client: TestClient) -> str:
    for _ in range(50):
        code = str(client.post("/links", json={"url": URL}).json()["code"])
        if code.swapcase() != code:
            return code
    raise AssertionError("no code with letters in 50 tries")


def test_create_link_many_posts_yield_unique_codes(client: TestClient) -> None:
    codes = {client.post("/links", json={"url": URL}).json()["code"] for _ in range(300)}

    assert len(codes) == 300


def test_follow_link_seven_char_path_returns_404(client: TestClient) -> None:
    code = str(client.post("/links", json={"url": URL}).json()["code"])

    response = client.get(f"/{code}x")

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


def test_get_stats_wrong_case_code_returns_404(client: TestClient) -> None:
    code = _create_with_letters(client)

    response = client.get(f"/links/{code.swapcase()}/stats")

    assert response.status_code == 404
    assert response.json() == NOT_FOUND


def test_follow_link_wrong_case_records_no_click(client: TestClient) -> None:
    code = _create_with_letters(client)

    assert client.get(f"/{code.swapcase()}").status_code == 404
    assert client.get(f"/links/{code}/stats").json()["clicks"] == 0


@pytest.mark.parametrize("path", ["/zzzzzz", "/abc", "/links"])
def test_follow_link_404_records_no_click_on_existing_link(
    client: TestClient, db_path: Path, path: str
) -> None:
    code = str(client.post("/links", json={"url": URL}).json()["code"])

    client.get(path)

    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("SELECT clicks FROM links WHERE code=?", (code,)).fetchone() == (0,)
    finally:
        conn.close()


def test_create_link_non_json_body_and_wrong_type_return_422(client: TestClient) -> None:
    assert client.post("/links", json={"url": 5}).status_code == 422
    assert client.post("/links", json=["x"]).status_code == 422
