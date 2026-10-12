"""Stateless recommendation API and a small, build-free frontend."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .recommendations import RecommendationError, recommend

ROOT = Path(__file__).resolve().parent.parent


class GenerateBody(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


def create_app() -> FastAPI:
    app = FastAPI(title="SideTrack", docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.update({
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
        })
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, exc):
        return JSONResponse({"detail": "Paste a valid YouTube song URL (up to 2,048 characters)."}, status_code=422)

    @app.get("/")
    def index():
        return FileResponse(ROOT / "static" / "index.html")

    @app.post("/api/recommend")
    def generate(body: GenerateBody):
        try:
            return recommend(body.url)
        except RecommendationError as exc:
            raise HTTPException(exc.status, str(exc)) from exc

    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    return app


app = create_app()
