"""T04: Pages (Story/Guide/Work With Me, CONTEXT.md) — admin-only, appear in
public navigation once published. Unlike Notes, there's no "own draft" concept:
admin does everything, editor is blocked from every route here."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.db import is_duplicate_slug
from app.deps import get_db, get_session, require_role, verify_csrf
from app.templating import templates

router = APIRouter(prefix="/admin/pages")

DUPLICATE_SLUG = "Another Page already uses that slug. Choose a different one."


def _duplicate_slug_form(
    request: Request, page: sqlite3.Row | None, form: dict, csrf_token: str
):
    """Re-render the Page form after a UNIQUE(type, slug) violation."""
    return templates.TemplateResponse(
        request, "admin/page_form.html",
        {"page": page, "form": form, "error": DUPLICATE_SLUG, "csrf_token": csrf_token},
        status_code=409,
    )


def _get_page_or_404(conn: sqlite3.Connection, page_id: int) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM content WHERE id=? AND type='page'", (page_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404)
    return row


@router.get("")
def list_pages(
    request: Request,
    user: sqlite3.Row = Depends(require_role("admin")),
    conn: sqlite3.Connection = Depends(get_db),
    session: dict = Depends(get_session),
):
    pages = conn.execute(
        "SELECT * FROM content WHERE type='page' ORDER BY nav_order, title"
    ).fetchall()
    return templates.TemplateResponse(
        request, "admin/pages_list.html", {"pages": pages, "csrf_token": session["csrf"]}
    )


@router.get("/new")
def new_page_form(
    request: Request,
    user: sqlite3.Row = Depends(require_role("admin")),
    session: dict = Depends(get_session),
):
    return templates.TemplateResponse(
        request, "admin/page_form.html", {"page": None, "csrf_token": session["csrf"]}
    )


@router.post("")
def create_page(
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    body_md: str = Form(""),
    nav_order: int = Form(0),
    user: sqlite3.Row = Depends(require_role("admin")),
    conn: sqlite3.Connection = Depends(get_db),
    session: dict = Depends(get_session),
    _csrf: None = Depends(verify_csrf),
):
    try:
        conn.execute(
            "INSERT INTO content (type, title, slug, body_md, status, author_id, "
            "nav_order) VALUES ('page', ?, ?, ?, 'draft', ?, ?)",
            (title, slug, body_md, user["id"], nav_order),
        )
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        if not is_duplicate_slug(exc):
            raise
        form = {"title": title, "slug": slug, "body_md": body_md, "nav_order": nav_order}
        return _duplicate_slug_form(request, None, form, session["csrf"])
    conn.commit()
    return RedirectResponse(url="/admin/pages", status_code=303)


@router.get("/{page_id}/edit")
def edit_page_form(
    page_id: int,
    request: Request,
    user: sqlite3.Row = Depends(require_role("admin")),
    conn: sqlite3.Connection = Depends(get_db),
    session: dict = Depends(get_session),
):
    page = _get_page_or_404(conn, page_id)
    return templates.TemplateResponse(
        request, "admin/page_form.html", {"page": page, "csrf_token": session["csrf"]}
    )


@router.post("/{page_id}")
def update_page(
    page_id: int,
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    body_md: str = Form(""),
    nav_order: int = Form(0),
    user: sqlite3.Row = Depends(require_role("admin")),
    conn: sqlite3.Connection = Depends(get_db),
    session: dict = Depends(get_session),
    _csrf: None = Depends(verify_csrf),
):
    page = _get_page_or_404(conn, page_id)
    try:
        conn.execute(
            "UPDATE content SET title=?, slug=?, body_md=?, nav_order=?, "
            "updated_at=datetime('now') WHERE id=?",
            (title, slug, body_md, nav_order, page_id),
        )
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        if not is_duplicate_slug(exc):
            raise
        form = {"title": title, "slug": slug, "body_md": body_md, "nav_order": nav_order}
        return _duplicate_slug_form(request, page, form, session["csrf"])
    conn.commit()
    return RedirectResponse(url="/admin/pages", status_code=303)


@router.post("/{page_id}/publish")
def publish_page(
    page_id: int,
    user: sqlite3.Row = Depends(require_role("admin")),
    conn: sqlite3.Connection = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
):
    _get_page_or_404(conn, page_id)
    conn.execute(
        "UPDATE content SET status='published', updated_at=datetime('now') WHERE id=?",
        (page_id,),
    )
    conn.commit()
    return RedirectResponse(url="/admin/pages", status_code=303)


@router.post("/{page_id}/unpublish")
def unpublish_page(
    page_id: int,
    user: sqlite3.Row = Depends(require_role("admin")),
    conn: sqlite3.Connection = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
):
    _get_page_or_404(conn, page_id)
    conn.execute(
        "UPDATE content SET status='draft', updated_at=datetime('now') WHERE id=?",
        (page_id,),
    )
    conn.commit()
    return RedirectResponse(url="/admin/pages", status_code=303)


@router.post("/{page_id}/delete")
def delete_page(
    page_id: int,
    user: sqlite3.Row = Depends(require_role("admin")),
    conn: sqlite3.Connection = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
):
    _get_page_or_404(conn, page_id)
    conn.execute("DELETE FROM content WHERE id=?", (page_id,))
    conn.commit()
    return RedirectResponse(url="/admin/pages", status_code=303)
