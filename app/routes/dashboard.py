"""T05: admin console UX — dashboard counts, the filterable content list, and
the editor's Markdown preview.

Editors see only their own Notes here, the same rows /admin/notes shows them,
so a count never promises something they can't open (decided in the T05
session). Pages never appear for editors.
"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse

from app.deps import get_db, require_role, verify_csrf
from app.markdown import render_markdown
from app.templating import templates

router = APIRouter(prefix="/admin")

TYPES = ("page", "note")
STATUSES = ("draft", "published")


def _visibility_clause(user: sqlite3.Row) -> tuple[str, list, tuple[str, ...]]:
    """WHERE fragment + params for the content this user may see, and the
    content types they can filter by. Callers append fragments with f-strings:
    only these constant fragments, never a value — values go in params."""
    if user["role"] == "admin":
        return "1=1", [], TYPES
    return "type='note' AND author_id=?", [user["id"]], ("note",)


@router.get("")
def dashboard(
    request: Request,
    user: sqlite3.Row = Depends(require_role("admin", "editor")),
    conn: sqlite3.Connection = Depends(get_db),
):
    where, params, types = _visibility_clause(user)
    counts = {(t, s): 0 for t in TYPES for s in STATUSES}
    for row in conn.execute(
        f"SELECT type, status, COUNT(*) AS n FROM content WHERE {where} "
        "GROUP BY type, status", params,
    ):
        counts[(row["type"], row["status"])] = row["n"]
    return templates.TemplateResponse(
        request, "admin/dashboard.html",
        {"title": "Dashboard", "user": user, "counts": counts, "types": types,
         "statuses": STATUSES},
    )


@router.get("/content")
def content_list(
    request: Request,
    type_: str = Query("", alias="type"),
    status: str = "",
    user: sqlite3.Row = Depends(require_role("admin", "editor")),
    conn: sqlite3.Connection = Depends(get_db),
):
    # Unknown values (including the "All" option's "") mean "no filter".
    type_ = type_ if type_ in TYPES else ""
    status_ = status if status in STATUSES else ""
    where, params, types = _visibility_clause(user)
    if type_:
        where += " AND type=?"
        params.append(type_)
    if status_:
        where += " AND status=?"
        params.append(status_)
    rows = conn.execute(
        f"SELECT * FROM content WHERE {where} ORDER BY updated_at DESC, id DESC", params
    ).fetchall()
    return templates.TemplateResponse(
        request, "admin/content_list.html",
        {"title": "Content", "user": user, "rows": rows, "type": type_,
         "status": status_, "types": types,
         "statuses": STATUSES},
    )


@router.post("/preview", response_class=HTMLResponse)
def preview(
    body_md: str = Form(""),
    _user: sqlite3.Row = Depends(require_role("admin", "editor")),
    _csrf: None = Depends(verify_csrf),
):
    """Sanitized HTML for the editor's live preview pane. Not state-changing,
    but CSRF-checked anyway so no other site can use it as a rendering oracle
    with the user's cookie."""
    return HTMLResponse(render_markdown(body_md))
