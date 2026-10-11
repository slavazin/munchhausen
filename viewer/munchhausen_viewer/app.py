"""Viewer (SPEC § 17): FastAPI + SSE + one static page. Reads through the engine's Store port only.

Panes (M4): decision store · fire ticker · curves (side pane) · injection control · `why`.
Every pane is fed by change streams and can be driven by the replay scrubber (`idx`).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

STATIC = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(title="Munchhausen")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    # M4: /events (SSE over Store.watch on fires, decisions, rounds), /why/{id}, /decisions?arm=, /inject
    return app


app = create_app()
