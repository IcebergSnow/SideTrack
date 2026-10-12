from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from google_auth_oauthlib.flow import Flow
import pytest

from sidetrack import app as web
from sidetrack import export

ORIGIN = "http://localhost:8000"
HEADERS = {"Origin": ORIGIN, "X-SideTrack": "1"}
RECOMMENDATIONS = {
    "seed": {"video_id": "fJ9rUzIMcZQ", "title": "Test seed", "artists": ["Artist"], "url": "https://youtu.be/fJ9rUzIMcZQ"},
    "tracks": [{"video_id": "abcdefghijk"}, {"video_id": "lmnopqrstuv"}],
    "note": "",
}


class RequestStub:
    def __init__(self, action):
        self.action = action

    def execute(self, num_retries):
        assert num_retries == 0
        return self.action()


class YouTubeStub:
    """Test-only API boundary. Never imported by application code."""
    def __init__(self, fail_at=None):
        self.calls = []
        self.fail_at = fail_at
        self.kind = None
        self.closed = False

    def playlists(self):
        self.kind = "playlist"
        return self

    def playlistItems(self):
        self.kind = "item"
        return self

    def insert(self, **kwargs):
        self.calls.append((self.kind, kwargs))
        def execute():
            if len(self.calls) == self.fail_at:
                raise TimeoutError("test-only simulated timeout")
            return {"id": "PL_test" if self.kind == "playlist" else "item_test"}
        return RequestStub(execute)

    def close(self):
        self.closed = True


def test_official_api_creates_private_playlist_and_ordered_items(monkeypatch):
    youtube = YouTubeStub()
    monkeypatch.setattr(export, "youtube_client", lambda _: youtube)
    progress = []
    result = export.export_playlist(object(), RECOMMENDATIONS, lambda *args: progress.append(args))
    assert result["status"] == "complete"
    assert youtube.calls[0][1]["body"]["status"] == {"privacyStatus": "private"}
    assert [call[1]["body"]["snippet"]["resourceId"]["videoId"] for call in youtube.calls[1:]] == ["abcdefghijk", "lmnopqrstuv"]
    assert progress == [("PL_test", 0), ("PL_test", 1), ("PL_test", 2)]
    assert youtube.closed


@pytest.mark.parametrize("fail_at,status,count", [(1, "failed", 0), (3, "partial", 1)])
def test_ambiguous_failures_are_not_retried_or_reported_as_success(monkeypatch, fail_at, status, count):
    youtube = YouTubeStub(fail_at)
    monkeypatch.setattr(export, "youtube_client", lambda _: youtube)
    progress = []
    result = export.export_playlist(object(), RECOMMENDATIONS, lambda *args: progress.append(args))
    assert result["status"] == status
    assert len(youtube.calls) == fail_at
    if count:
        assert progress[-1] == ("PL_test", count)
        assert "last request may also have succeeded" in result["message"]
    else:
        assert "playlist may already exist" in result["message"]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(web, "recommend", lambda _: RECOMMENDATIONS)
    settings = export.Settings("test-client", "test-secret")
    with TestClient(web.create_app(settings), base_url=ORIGIN) as client:
        client.get("/api/session")
        yield client


def generate(client):
    return client.post("/api/recommend", json={"url": "https://youtu.be/fJ9rUzIMcZQ"}, headers=HEADERS)


def authorize(client):
    assert generate(client).status_code == 200
    result = client.post("/api/export", headers=HEADERS)
    assert result.status_code == 200
    return parse_qs(urlparse(result.json()["authorization_url"]).query)


def test_no_login_for_recommendations_and_no_export_without_configuration(monkeypatch):
    monkeypatch.setattr(web, "recommend", lambda _: RECOMMENDATIONS)
    with TestClient(web.create_app(export.Settings()), base_url=ORIGIN) as client:
        response = client.get("/api/session")
        assert "HttpOnly" in response.headers["set-cookie"]
        assert "SameSite=lax" in response.headers["set-cookie"]
        assert generate(client).status_code == 200
        response = client.post("/api/export", headers=HEADERS)
        assert response.status_code == 503
        assert "GOOGLE_CLIENT_ID" in response.json()["detail"]


def test_oauth_has_pkce_state_minimal_scope_and_no_offline_access(client):
    params = authorize(client)
    assert params["access_type"] == ["online"]
    assert params["scope"] == [export.SCOPE]
    assert params["code_challenge_method"] == ["S256"]
    assert params["code_challenge"]
    assert params["state"]
    assert params["redirect_uri"] == [ORIGIN + "/oauth/callback"]
    snapshot = client.get("/api/session").json()
    assert "test-secret" not in str(snapshot)
    assert params["state"][0] not in str(snapshot)


def test_cross_origin_missing_header_and_empty_export_rejected(client):
    assert client.post("/api/export", headers=HEADERS).status_code == 409
    assert client.post("/api/recommend", json={"url": "x"}).status_code == 403
    assert client.post("/api/export", headers={**HEADERS, "Origin": "https://evil.test"}).status_code == 403


def test_state_mismatch_denial_and_replay(client):
    params = authorize(client)
    response = client.get("/oauth/callback?code=test&state=wrong", follow_redirects=False)
    assert response.headers["location"] == "/?auth_error=state"
    assert client.get("/api/session").json()["export"]["status"] == "authorizing"
    assert client.get("/oauth/callback?code=test&state=é", follow_redirects=False).headers["location"] == "/?auth_error=state"
    callback = f"/oauth/callback?error=access_denied&state={params['state'][0]}"
    assert client.get(callback, follow_redirects=False).headers["location"] == "/"
    assert client.get("/api/session").json()["export"]["status"] == "failed"
    assert client.get(callback, follow_redirects=False).headers["location"] == "/?auth_error=state"


def test_callback_exports_once_and_returns_link_without_tokens(client, monkeypatch):
    youtube = YouTubeStub()
    monkeypatch.setattr(export, "youtube_client", lambda _: youtube)
    def fetch_token(flow, **kwargs):
        assert kwargs == {"code": "test-code", "timeout": 15}
        flow.oauth2session.token = {"access_token": "test-only-token", "token_type": "Bearer", "scope": export.SCOPE, "expires_at": 2000000000}
    monkeypatch.setattr(Flow, "fetch_token", fetch_token)
    params = authorize(client)
    callback = f"/oauth/callback?code=test-code&state={params['state'][0]}"
    client.get(callback)
    response = client.get("/api/session")
    assert response.json()["export"]["status"] == "complete"
    assert response.json()["export"]["playlist_url"] == "https://www.youtube.com/playlist?list=PL_test"
    assert "test-only-token" not in response.text
    client.get(callback)
    client.post("/api/export", headers=HEADERS)
    assert len(youtube.calls) == 3


def test_sessions_are_isolated_and_regenerating_invalidates_oauth(client):
    params = authorize(client)
    with TestClient(client.app, base_url=ORIGIN) as other:
        assert other.get("/api/session").json()["recommendations"] is None
        response = other.get(f"/oauth/callback?code=x&state={params['state'][0]}", follow_redirects=False)
        assert response.headers["location"] == "/?auth_error=state"
    generate(client)
    response = client.get(f"/oauth/callback?code=x&state={params['state'][0]}", follow_redirects=False)
    assert response.headers["location"] == "/?auth_error=state"


def test_oauth_expires_and_remote_http_is_rejected(client, monkeypatch):
    params = authorize(client)
    now = web.time.monotonic()
    monkeypatch.setattr(web.time, "monotonic", lambda: now + web.OAUTH_TTL + 1)
    response = client.get(f"/oauth/callback?code=x&state={params['state'][0]}", follow_redirects=False)
    assert response.headers["location"] == "/?auth_error=state"
    assert client.get("/api/session").json()["export"]["status"] == "failed"
    with pytest.raises(ValueError):
        export.Settings(redirect_uri="http://example.com/oauth/callback")
