"""A single-process proof of concept. Browser sessions live only in memory."""

from dataclasses import dataclass, field
from pathlib import Path
import secrets
import threading
import time

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .export import SCOPE, Settings, export_playlist, oauth_flow
from .recommendations import RecommendationError, recommend

ROOT = Path(__file__).resolve().parent.parent
COOKIE = "sidetrack_session"
SESSION_TTL = 3600
OAUTH_TTL = 600


@dataclass
class BrowserSession:
    expires: float = field(default_factory=lambda: time.monotonic() + SESSION_TTL)
    recommendations: dict | None = None
    generating: bool = False
    status: str = "idle"
    message: str = ""
    playlist_id: str | None = None
    added: int = 0
    flow: object | None = None
    oauth_state: str | None = None
    oauth_expires: float = 0

    def clear_oauth(self):
        self.flow = None
        self.oauth_state = None
        self.oauth_expires = 0


class GenerateBody(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        load_dotenv(ROOT / ".env")
        settings = Settings.from_env()
    app = FastAPI(title="SideTrack", docs_url=None, redoc_url=None)
    sessions: dict[str, BrowserSession] = {}
    lock = threading.RLock()

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.update({
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'self'; img-src 'self' https://i.ytimg.com; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
        })
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, exc):
        return JSONResponse({"detail": "Paste a valid YouTube song URL (up to 2,048 characters)."}, status_code=422)

    def current(request: Request, response: Response | None = None) -> BrowserSession:
        with lock:
            now = time.monotonic()
            for key in list(sessions):
                value = sessions[key]
                if value.expires < now and value.status != "exporting" and not value.generating:
                    del sessions[key]
            session_id = request.cookies.get(COOKIE, "")
            session = sessions.get(session_id)
            if session is None:
                if response is None:
                    raise HTTPException(400, "This session expired. Reload SideTrack and generate a playlist again.")
                if len(sessions) >= 200:
                    raise HTTPException(503, "SideTrack is busy. Please try again later.")
                session_id = secrets.token_urlsafe(32)
                session = sessions[session_id] = BrowserSession()
            if response is not None:
                response.set_cookie(COOKIE, session_id, httponly=True, secure=settings.origin.startswith("https://"), samesite="lax", max_age=SESSION_TTL)
            session.expires = now + SESSION_TTL
            if session.status == "authorizing" and session.oauth_expires < now:
                session.clear_oauth()
                session.status = "failed"
                session.message = "Google sign-in expired. Click Export to try again."
            return session

    def check_origin(request: Request):
        if request.headers.get("origin") != settings.origin or request.headers.get("x-sidetrack") != "1":
            raise HTTPException(403, f"Open SideTrack at {settings.origin} and try again.")

    def snapshot(session: BrowserSession):
        return {
            "recommendations": session.recommendations,
            "generating": session.generating,
            "oauth_ready": settings.ready,
            "export": {
                "status": session.status, "message": session.message, "added": session.added,
                "playlist_url": f"https://www.youtube.com/playlist?list={session.playlist_id}" if session.playlist_id else None,
            },
        }

    @app.get("/")
    def index():
        return FileResponse(ROOT / "static" / "index.html")

    @app.get("/api/session")
    def get_session(request: Request, response: Response):
        session = current(request, response)
        with lock:
            return snapshot(session)

    @app.post("/api/recommend")
    def generate(body: GenerateBody, request: Request):
        check_origin(request)
        session = current(request)
        with lock:
            if session.generating or session.status == "exporting":
                raise HTTPException(409, "Wait for the current request to finish.")
            session.generating = True
            session.clear_oauth()
            session.status = "idle"
            session.message = ""
            session.playlist_id = None
            session.added = 0
            session.recommendations = None
        try:
            result = recommend(body.url)
            with lock:
                session.recommendations = result
            return result
        except RecommendationError as exc:
            raise HTTPException(exc.status, str(exc)) from exc
        finally:
            with lock:
                session.generating = False

    @app.post("/api/export")
    def start_export(request: Request):
        check_origin(request)
        session = current(request)
        if not settings.ready:
            raise HTTPException(503, "Export needs Google OAuth credentials. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env, then restart SideTrack.")
        with lock:
            if session.generating or not session.recommendations:
                raise HTTPException(409, "Generate recommendations before exporting.")
            if session.status in {"exporting", "complete", "partial"}:
                return {"export": snapshot(session)["export"]}
            # Reuse a pending authorization rather than invalidate another tab's state.
            if session.status == "authorizing":
                raise HTTPException(409, "Google sign-in is already open. Finish it, or generate again to start over.")
            flow = oauth_flow(settings)
            auth_url, state = flow.authorization_url(access_type="online", prompt="select_account consent")
            session.flow = flow
            session.oauth_state = state
            session.oauth_expires = time.monotonic() + OAUTH_TTL
            session.status = "authorizing"
            session.message = "Finish Google sign-in to export your playlist."
            return {"authorization_url": auth_url}

    def do_export(session: BrowserSession, credentials, recommendations: dict):
        def progress(playlist_id: str, added: int):
            with lock:
                session.playlist_id = playlist_id
                session.added = added

        result = export_playlist(credentials, recommendations, progress)
        with lock:
            session.status = result["status"]
            session.message = result["message"]
        # Credentials are not put in the session, on disk, or in the browser.

    @app.get("/oauth/callback")
    def oauth_callback(request: Request, background_tasks: BackgroundTasks):
        try:
            session = current(request)
        except HTTPException:
            return RedirectResponse("/?auth_error=session", status_code=303)
        state = request.query_params.get("state", "")
        with lock:
            if session.status != "authorizing" or not session.oauth_state or not secrets.compare_digest(state.encode(), session.oauth_state.encode()):
                return RedirectResponse("/?auth_error=state", status_code=303)
            flow = session.flow
            session.clear_oauth()  # Consume state even on cancellation; callback replay cannot export twice.
            if request.query_params.get("error"):
                session.status = "failed"
                session.message = "Google sign-in was cancelled or permission was denied. Your recommendations are still here."
                return RedirectResponse("/", status_code=303)
            code = request.query_params.get("code")
            if not code:
                session.status = "failed"
                session.message = "Google didn't return an authorization code. Please try Export again."
                return RedirectResponse("/", status_code=303)
            session.status = "exporting"
            session.message = "Creating your private YouTube playlist…"
            recommendations = session.recommendations
        try:
            # Passing code (rather than the HTTP callback URL) keeps HTTPS enforcement
            # enabled globally while permitting Google's registered localhost callback.
            flow.fetch_token(code=code, timeout=15)
            granted = flow.credentials.granted_scopes
            if granted is not None and SCOPE not in granted:
                raise ValueError("YouTube permission not granted")
            background_tasks.add_task(do_export, session, flow.credentials, recommendations)
        except Exception:
            with lock:
                session.status = "failed"
                session.message = "Google authorization couldn't be completed. Grant YouTube access, check the OAuth configuration, and try Export again."
        return RedirectResponse("/", status_code=303)

    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    return app


app = create_app()
