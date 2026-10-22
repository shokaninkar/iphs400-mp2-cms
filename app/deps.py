"""FastAPI dependencies shared across route modules."""
from __future__ import annotations

import sqlite3
from typing import Iterator

from fastapi import Depends, Form, HTTPException, Request

from app.db import get_connection
from app.security import SESSION_COOKIE, read_session_token


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    conn = get_connection(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()


def get_session(request: Request) -> dict | None:
    """Decode the signed session cookie (no DB lookup). Carries user_id, role,
    and the per-login csrf token (app/security.py:create_session_token)."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    return read_session_token(token)


def get_current_user(
    conn: sqlite3.Connection = Depends(get_db),
    session: dict | None = Depends(get_session),
) -> sqlite3.Row | None:
    if not session:
        return None
    row = conn.execute(
        "SELECT * FROM users WHERE id = ? AND is_active = 1", (session["user_id"],)
    ).fetchone()
    return row


def require_role(*roles: str):
    """FastAPI dependency factory: anonymous -> redirect to login, wrong role
    -> 403. Two different failure modes on purpose (T02 acceptance criteria)."""

    def dependency(
        user: sqlite3.Row | None = Depends(get_current_user),
    ) -> sqlite3.Row:
        if user is None:
            raise HTTPException(status_code=303, headers={"Location": "/login"})
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    # S1: the marker tests/test_access_matrix.py reads off the router to find
    # every admin-only route without a hand-written list.
    dependency.roles = roles
    return dependency


def verify_csrf(
    csrf_token: str | None = Form(None),
    session: dict | None = Depends(get_session),
) -> None:
    """Every authenticated, state-changing form depends on this (D2). Login is
    the one documented exception (T01/CONTEXT.md) — it has no prior session.

    csrf_token is optional at the Form level so a missing field 403s (this
    check) rather than 422s (FastAPI's own required-field validation, which
    would run before this dependency's logic gets a say)."""
    if not session or not csrf_token or csrf_token != session.get("csrf"):
        raise HTTPException(status_code=403, detail="Invalid or missing CSRF token")
