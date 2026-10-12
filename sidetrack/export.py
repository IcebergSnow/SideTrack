"""Google OAuth and writes through the official YouTube Data API only."""

from dataclasses import dataclass
import json
import os
from urllib.parse import urlparse

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_httplib2 import AuthorizedHttp
import httplib2

SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"


@dataclass(frozen=True)
class Settings:
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = "http://localhost:8000/oauth/callback"

    def __post_init__(self):
        parsed = urlparse(self.redirect_uri)
        local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if (
            not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path != "/oauth/callback"
            or not (parsed.scheme == "https" or (local and parsed.scheme == "http"))
        ):
            raise ValueError("GOOGLE_REDIRECT_URI must use HTTPS (HTTP is allowed on localhost) and end in /oauth/callback.")

    @property
    def ready(self) -> bool:
        return bool(self.client_id and self.client_secret)

    @property
    def origin(self) -> str:
        parsed = urlparse(self.redirect_uri)
        return f"{parsed.scheme}://{parsed.netloc}"

    @classmethod
    def from_env(cls):
        return cls(
            client_id=os.getenv("GOOGLE_CLIENT_ID", "").strip(),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET", "").strip(),
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/oauth/callback").strip(),
        )


def oauth_flow(settings: Settings) -> Flow:
    return Flow.from_client_config(
        {"web": {
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.redirect_uri],
        }},
        scopes=[SCOPE],
        redirect_uri=settings.redirect_uri,
        autogenerate_code_verifier=True,
    )


def youtube_client(credentials):
    return build(
        "youtube", "v3",
        http=AuthorizedHttp(credentials, http=httplib2.Http(timeout=15)),
        cache_discovery=False,
        static_discovery=True,
    )


def api_error_message(exc: Exception) -> str:
    if isinstance(exc, HttpError):
        try:
            reason = json.loads(exc.content)["error"]["errors"][0]["reason"]
        except (ValueError, KeyError, IndexError, TypeError):
            reason = ""
        if reason in {"quotaExceeded", "dailyLimitExceeded"}:
            return "The Google project's YouTube API quota is exhausted. Try again after the quota resets."
        if reason in {"youtubeSignupRequired", "channelNotFound"}:
            return "This Google account needs a YouTube channel. Create one on YouTube, then try again."
        if reason in {"accessNotConfigured", "serviceDisabled"}:
            return "Enable YouTube Data API v3 in the Google Cloud project, then try again."
        if exc.resp.status in {401, 403}:
            return "YouTube denied access. Check that you granted the requested YouTube permission and that the API is enabled."
        if reason in {"videoNotFound", "invalidVideoId", "playlistOperationUnsupported"}:
            return "YouTube could not add one of these videos. It may have become unavailable."
    return "YouTube export was interrupted. Check your connection and account, then try again."


def export_playlist(credentials, recommendations: dict, progress) -> dict:
    """Never retry writes automatically: a timeout may have committed the write."""
    playlist_id = None
    added = 0
    youtube = None
    try:
        youtube = youtube_client(credentials)
        seed = recommendations["seed"]
        created = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": ("SideTrack · " + seed["title"])[:150],
                    "description": f"A detour from {seed['title']} — {', '.join(seed['artists'])}.\nInspired by {seed['url']}\nMade with SideTrack.",
                },
                "status": {"privacyStatus": "private"},
            },
        ).execute(num_retries=0)
        playlist_id = created["id"]
        progress(playlist_id, added)
        for track in recommendations["tracks"]:
            youtube.playlistItems().insert(
                part="snippet",
                body={"snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": track["video_id"]},
                }},
            ).execute(num_retries=0)
            added += 1
            progress(playlist_id, added)
        return {"status": "complete", "message": f"All {added} songs are in your private YouTube playlist."}
    except Exception as exc:
        message = api_error_message(exc)
        if playlist_id:
            message += f" {added} additions were confirmed. Open the partial playlist to review it; the last request may also have succeeded."
        else:
            message += " If the request timed out, check your YouTube library before retrying: a playlist may already exist."
        return {"status": "partial" if playlist_id else "failed", "message": message}
    finally:
        if youtube is not None:
            try:
                youtube.close()
            except Exception:
                pass
