"""The FastAPI application.

T00 (already done): the admin console answers at /admin and the public site
answers at /. That is the whole skeleton — it exists so you can prove the stack
runs before you build anything on it.

Add your routes in their own modules (app/routes/posts.py and so on) and include
them here. Keep this file small.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request

from app import settings
from app.db import init_db
from app.deps import get_db, require_role
from app.routes import auth, notes, pages
from app.templating import templates


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
    def public_home(request: Request, conn: sqlite3.Connection = Depends(get_db)):
        nav_pages = conn.execute(
            "SELECT title, slug FROM content WHERE type='page' AND status='published' "
            "ORDER BY nav_order, title"
        ).fetchall()
        # Same URL shape `cms publish` will write (T07): relative, .html suffix.
        items = [{"title": p["title"], "href": f"pages/{p['slug']}.html"} for p in nav_pages]
        return templates.TemplateResponse(
            request, "public/home.html",
            {"title": settings.SITE_TITLE, "items": items},
        )

    @app.get("/pages/{slug}.html")
    def public_page(
        slug: str, request: Request, conn: sqlite3.Connection = Depends(get_db)
    ):
        page = conn.execute(
            "SELECT * FROM content WHERE type='page' AND slug=? AND status='published'",
            (slug,),
        ).fetchone()
        if page is None:
            raise HTTPException(status_code=404)
        return templates.TemplateResponse(
            request, "public/page.html",
            {"title": page["title"], "page": page,
             "css_path": "../style.css", "home_path": "../index.html"},
        )

    app.include_router(auth.router)
    app.include_router(notes.router)
    app.include_router(pages.router)
    return app


app = create_app()
