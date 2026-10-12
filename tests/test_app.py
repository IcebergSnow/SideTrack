import importlib

import pytest
from fastapi.testclient import TestClient

from sidetrack.recommendations import RecommendationError

web = importlib.import_module("sidetrack.app")


def test_generate_is_independent_of_cookies_and_server_instance(monkeypatch):
    calls = []

    def recommend(url):
        calls.append(url)
        return {"seed": {"video_id": url}, "tracks": [], "note": "test-only response"}

    monkeypatch.setattr(web, "recommend", recommend)
    for url in ["https://youtu.be/fJ9rUzIMcZQ", "https://youtu.be/kJQP7kiw5Fk"]:
        with TestClient(web.create_app(), base_url="https://preview.example") as client:
            response = client.post("/api/recommend", json={"url": url})
            assert response.status_code == 200
            assert response.json()["seed"]["video_id"] == url
            assert "set-cookie" not in response.headers
            assert not client.cookies
    assert len(calls) == 2


@pytest.mark.parametrize("status", [404, 422, 502, 504])
def test_recommendation_errors_reach_the_browser(monkeypatch, status):
    def fail(url):
        raise RecommendationError("Useful upstream failure message", status)

    monkeypatch.setattr(web, "recommend", fail)
    with TestClient(web.create_app()) as client:
        response = client.post("/api/recommend", json={"url": "https://youtu.be/fJ9rUzIMcZQ"})
    assert response.status_code == status
    assert response.json() == {"detail": "Useful upstream failure message"}


@pytest.mark.parametrize("body", [{}, {"url": ""}, {"url": "x" * 2049}, {"url": None}])
def test_invalid_request_body_is_rejected_before_upstream(monkeypatch, body):
    def unexpected(url):
        pytest.fail("Invalid requests must not call YouTube Music")

    monkeypatch.setattr(web, "recommend", unexpected)
    with TestClient(web.create_app()) as client:
        response = client.post("/api/recommend", json=body)
    assert response.status_code == 422
    assert "valid YouTube song URL" in response.json()["detail"]


def test_invalid_link_has_readable_error():
    with TestClient(web.create_app()) as client:
        response = client.post("/api/recommend", json={"url": "https://example.com/song"})
    assert response.status_code == 400
    assert "single song" in response.json()["detail"]


def test_entrypoint_serves_frontend_without_auth_routes():
    from app import app

    with TestClient(app) as client:
        for path in ["/", "/static/app.js", "/static/downloads.mjs", "/static/style.css"]:
            response = client.get(path)
            assert response.status_code == 200
            assert "set-cookie" not in response.headers
            assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
        assert "javascript" in client.get("/static/downloads.mjs").headers["content-type"]
        assert client.get("/api/session").status_code == 404
        assert client.get("/oauth/callback").status_code == 404
        assert client.post("/api/export", json={}).status_code == 404
