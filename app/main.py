"""The FastAPI application.

T00 (already done): the admin console answers at /admin and the public site
answers at /. That is the whole skeleton — it exists so you can prove the stack
runs before you build anything on it.

Add your routes in their own modules (app/routes/posts.py and so on) and include
them here. Keep this file small.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.templating import Jinja2Templates

from app import settings
from app.db import init_db
from app.deps import require_role
from app.routes import auth

templates = Jinja2Templates(directory=str(settings.TEMPLATES))


def create_app(db_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="IPHS 400 MP2 CMS")
    app.state.db_path = db_path or settings.DATABASE_PATH
    init_db(app.state.db_path)

    @app.get("/admin")
    def admin_home(
        request: Request,
        user=Depends(require_role("admin", "editor")),
    ):
        return templates.TemplateResponse(
            request, "admin/hello.html", {"title": "Admin", "user": user}
        )

    @app.get("/")
    def public_home(request: Request):
        return templates.TemplateResponse(
            request, "public/home.html",
            {"title": settings.SITE_TITLE, "items": []},
        )

    app.include_router(auth.router)
    # Your ticket work plugs in here, e.g.
    #   from app.routes import posts
    #   app.include_router(posts.router)
    return app


app = create_app()
