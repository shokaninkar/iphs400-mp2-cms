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
from app.content import nav_items, published_notes, published_one, published_pages
from app.db import init_db
from app.deps import get_db, require_role
from app.routes import auth, notes, pages, users
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

    # Live preview of the public site. Same queries, templates and relative
    # URL shape as `cms publish` (app/publish.py), so preview == export.
    def _public(request: Request, conn: sqlite3.Connection, template: str,
                root: str, **ctx):
        return templates.TemplateResponse(
            request, template,
            {"site_title": settings.SITE_TITLE,
             "nav": nav_items(published_pages(conn)), "root": root, **ctx},
        )

    @app.get("/")
    def public_home(request: Request, conn: sqlite3.Connection = Depends(get_db)):
        return _public(request, conn, "public/home.html", "",
                       title=settings.SITE_TITLE, notes=published_notes(conn))

    @app.get("/notes/index.html")
    def public_notes(request: Request, conn: sqlite3.Connection = Depends(get_db)):
        return _public(request, conn, "public/notes_index.html", "../",
                       title="Notes", notes=published_notes(conn))

    @app.get("/pages/{slug}.html")
    def public_page(
        slug: str, request: Request, conn: sqlite3.Connection = Depends(get_db)
    ):
        page = published_one(conn, "page", slug)
        if page is None:
            raise HTTPException(status_code=404)
        return _public(request, conn, "public/page.html", "../",
                       title=page["title"], page=page)

    @app.get("/notes/{slug}.html")
    def public_note(
        slug: str, request: Request, conn: sqlite3.Connection = Depends(get_db)
    ):
        note = published_one(conn, "note", slug)
        if note is None:
            raise HTTPException(status_code=404)
        return _public(request, conn, "public/note.html", "../",
                       title=note["title"], note=note)

    app.include_router(auth.router)
    app.include_router(notes.router)
    app.include_router(pages.router)
    app.include_router(users.router)
    return app


app = create_app()
