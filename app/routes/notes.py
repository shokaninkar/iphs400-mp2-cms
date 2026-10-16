"""T03: Notes (inkadmissions' name for admissions-tips/blog posts, CONTEXT.md).

Editors create/edit their own Notes as drafts only. Only admin publishes,
unpublishes, or deletes. Every state-changing route here requires CSRF
(the first content type to need it — see CONTEXT.md on why /login is exempt).
"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.db import is_duplicate_slug
from app.deps import get_db, get_session, require_role, verify_csrf
from app.templating import templates

router = APIRouter(prefix="/admin/notes")

DUPLICATE_SLUG = "Another Note already uses that slug. Choose a different one."


def _duplicate_slug_form(
    request: Request, note: sqlite3.Row | None, form: dict, csrf_token: str
):
    """Re-render the Note form after a UNIQUE(type, slug) violation."""
    return templates.TemplateResponse(
        request, "admin/note_form.html",
        {"note": note, "form": form, "error": DUPLICATE_SLUG, "csrf_token": csrf_token},
        status_code=409,
    )


def _visible_notes(conn: sqlite3.Connection, user: sqlite3.Row) -> list[sqlite3.Row]:
    if user["role"] == "admin":
        return conn.execute(
            "SELECT * FROM content WHERE type='note' ORDER BY updated_at DESC"
        ).fetchall()
    return conn.execute(
        "SELECT * FROM content WHERE type='note' AND author_id=? "
        "ORDER BY updated_at DESC",
        (user["id"],),
    ).fetchall()


def _get_note_or_404(conn: sqlite3.Connection, note_id: int) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM content WHERE id=? AND type='note'", (note_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404)
    return row


def _ensure_owner_or_admin(user: sqlite3.Row, note: sqlite3.Row) -> None:
    if user["role"] != "admin" and note["author_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not your Note")


@router.get("")
def list_notes(
    request: Request,
    user: sqlite3.Row = Depends(require_role("admin", "editor")),
    conn: sqlite3.Connection = Depends(get_db),
    session: dict = Depends(get_session),
):
    notes = _visible_notes(conn, user)
    return templates.TemplateResponse(
        request, "admin/notes_list.html",
        {"notes": notes, "user": user, "csrf_token": session["csrf"]},
    )


@router.get("/new")
def new_note_form(
    request: Request,
    user: sqlite3.Row = Depends(require_role("admin", "editor")),
    session: dict = Depends(get_session),
):
    return templates.TemplateResponse(
        request, "admin/note_form.html", {"note": None, "csrf_token": session["csrf"]}
    )


@router.post("")
def create_note(
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    body_md: str = Form(""),
    user: sqlite3.Row = Depends(require_role("admin", "editor")),
    conn: sqlite3.Connection = Depends(get_db),
    session: dict = Depends(get_session),
    _csrf: None = Depends(verify_csrf),
):
    try:
        conn.execute(
            "INSERT INTO content (type, title, slug, body_md, status, author_id) "
            "VALUES ('note', ?, ?, ?, 'draft', ?)",
            (title, slug, body_md, user["id"]),
        )
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        if not is_duplicate_slug(exc):
            raise
        form = {"title": title, "slug": slug, "body_md": body_md}
        return _duplicate_slug_form(request, None, form, session["csrf"])
    conn.commit()
    return RedirectResponse(url="/admin/notes", status_code=303)


@router.get("/{note_id}/edit")
def edit_note_form(
    note_id: int,
    request: Request,
    user: sqlite3.Row = Depends(require_role("admin", "editor")),
    conn: sqlite3.Connection = Depends(get_db),
    session: dict = Depends(get_session),
):
    note = _get_note_or_404(conn, note_id)
    _ensure_owner_or_admin(user, note)
    return templates.TemplateResponse(
        request, "admin/note_form.html", {"note": note, "csrf_token": session["csrf"]}
    )


@router.post("/{note_id}")
def update_note(
    note_id: int,
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    body_md: str = Form(""),
    user: sqlite3.Row = Depends(require_role("admin", "editor")),
    conn: sqlite3.Connection = Depends(get_db),
    session: dict = Depends(get_session),
    _csrf: None = Depends(verify_csrf),
):
    note = _get_note_or_404(conn, note_id)
    _ensure_owner_or_admin(user, note)
    try:
        conn.execute(
            "UPDATE content SET title=?, slug=?, body_md=?, "
            "updated_at=datetime('now') WHERE id=?",
            (title, slug, body_md, note_id),
        )
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        if not is_duplicate_slug(exc):
            raise
        form = {"title": title, "slug": slug, "body_md": body_md}
        return _duplicate_slug_form(request, note, form, session["csrf"])
    conn.commit()
    return RedirectResponse(url="/admin/notes", status_code=303)


@router.post("/{note_id}/publish")
def publish_note(
    note_id: int,
    user: sqlite3.Row = Depends(require_role("admin")),
    conn: sqlite3.Connection = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
):
    _get_note_or_404(conn, note_id)
    conn.execute(
        "UPDATE content SET status='published', updated_at=datetime('now') WHERE id=?",
        (note_id,),
    )
    conn.commit()
    return RedirectResponse(url="/admin/notes", status_code=303)


@router.post("/{note_id}/unpublish")
def unpublish_note(
    note_id: int,
    user: sqlite3.Row = Depends(require_role("admin")),
    conn: sqlite3.Connection = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
):
    _get_note_or_404(conn, note_id)
    conn.execute(
        "UPDATE content SET status='draft', updated_at=datetime('now') WHERE id=?",
        (note_id,),
    )
    conn.commit()
    return RedirectResponse(url="/admin/notes", status_code=303)


@router.post("/{note_id}/delete")
def delete_note(
    note_id: int,
    user: sqlite3.Row = Depends(require_role("admin")),
    conn: sqlite3.Connection = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
):
    _get_note_or_404(conn, note_id)
    conn.execute("DELETE FROM content WHERE id=?", (note_id,))
    conn.commit()
    return RedirectResponse(url="/admin/notes", status_code=303)
