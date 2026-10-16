"""T06: user management — admin only; editor gets 403 on every route here.

Deactivating sets users.is_active = 0. Both login (app/routes/auth.py) and
every authenticated request (app/deps.py:get_current_user) filter on
is_active = 1, so a deactivated user is refused at login and loses any open
session on the next request. require_role reads the role from the DB row, not
the cookie, so a role change also takes effect immediately.

An admin cannot change their own role or deactivate themselves: with a single
admin, that would lock everyone out of user management.

Templates use relative URLs (checker: no root-absolute paths). The new-user
form posts back to its own URL, /admin/users/new, so a re-rendered form keeps
working.
"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.db import is_duplicate_email
from app.deps import get_db, get_session, require_role, verify_csrf
from app.security import hash_password
from app.templating import templates

router = APIRouter(prefix="/admin/users")

ROLES = ("admin", "editor")
DUPLICATE_EMAIL = "That email already has an account."
BAD_ROLE = "Role must be admin or editor."


def _get_user_or_404(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404)
    return row


def _refuse_self(current: sqlite3.Row, target: sqlite3.Row) -> None:
    if current["id"] == target["id"]:
        raise HTTPException(
            status_code=400,
            detail="You cannot change your own role or deactivate yourself.",
        )


def _new_user_form(request: Request, csrf_token: str, form: dict | None = None,
          error: str | None = None, status_code: int = 200):
    """The password is never echoed back into the form."""
    return templates.TemplateResponse(
        request, "admin/user_form.html",
        {"form": form or {}, "roles": ROLES, "error": error, "csrf_token": csrf_token},
        status_code=status_code,
    )


@router.get("")
def list_users(
    request: Request,
    user: sqlite3.Row = Depends(require_role("admin")),
    conn: sqlite3.Connection = Depends(get_db),
    session: dict = Depends(get_session),
):
    users = conn.execute(
        "SELECT id, email, role, is_active, created_at FROM users ORDER BY email"
    ).fetchall()
    return templates.TemplateResponse(
        request, "admin/users_list.html",
        {"users": users, "roles": ROLES, "current_user": user,
         "csrf_token": session["csrf"]},
    )


@router.get("/new")
def new_user_form(
    request: Request,
    user: sqlite3.Row = Depends(require_role("admin")),
    session: dict = Depends(get_session),
):
    return _new_user_form(request, session["csrf"])


@router.post("/new")
def create_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    user: sqlite3.Row = Depends(require_role("admin")),
    conn: sqlite3.Connection = Depends(get_db),
    session: dict = Depends(get_session),
    _csrf: None = Depends(verify_csrf),
):
    email = email.strip()
    form = {"email": email, "role": role}
    if role not in ROLES:
        return _new_user_form(request, session["csrf"], form, BAD_ROLE, 422)
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (email, hash_password(password), role),
        )
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        if not is_duplicate_email(exc):
            raise
        return _new_user_form(request, session["csrf"], form, DUPLICATE_EMAIL, 409)
    conn.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/{user_id}/role")
def change_role(
    user_id: int,
    role: str = Form(...),
    user: sqlite3.Row = Depends(require_role("admin")),
    conn: sqlite3.Connection = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
):
    target = _get_user_or_404(conn, user_id)
    _refuse_self(user, target)
    if role not in ROLES:
        raise HTTPException(status_code=422, detail=BAD_ROLE)
    conn.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
    conn.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    user: sqlite3.Row = Depends(require_role("admin")),
    conn: sqlite3.Connection = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
):
    target = _get_user_or_404(conn, user_id)
    _refuse_self(user, target)
    conn.execute("UPDATE users SET is_active=0 WHERE id=?", (user_id,))
    conn.commit()
    return RedirectResponse(url="/admin/users", status_code=303)
