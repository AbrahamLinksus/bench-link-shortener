import re
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

URL = "https://example.com/page"


def _count_rows(db_path: Path) -> int:
    conn = sqlite3.connect(db_path)
    try:
        return int(conn.execute("SELECT COUNT(*) FROM links").fetchone()[0])
    finally:
        conn.close()


def test_create_link_valid_url_returns_201_with_code_and_short_url(client: TestClient) -> None:
    response = client.post("/links", json={"url": URL})

    body = response.json()
    assert response.status_code == 201
    assert re.fullmatch(r"[A-Za-z0-9]{6}", body["code"])
    assert body["short_url"] == f"http://localhost:9000/{body['code']}"


@pytest.mark.parametrize(
    "payload", [{}, {"url": "not a url"}, {"url": "ftp://files.example.com/a.zip"}]
)
def test_create_link_invalid_payload_returns_422_and_stores_nothing(
    client: TestClient, db_path: Path, payload: dict[str, str]
) -> None:
    response = client.post("/links", json=payload)

    assert response.status_code == 422
    assert _count_rows(db_path) == 0


def test_create_link_malformed_json_returns_422_and_stores_nothing(
    client: TestClient, db_path: Path
) -> None:
    response = client.post(
        "/links", content=b"{not json", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422
    assert _count_rows(db_path) == 0
