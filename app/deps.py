"""FastAPI dependencies shared across route modules."""
from __future__ import annotations

import sqlite3
from typing import Iterator

from fastapi import Depends, HTTPException, Request

from app.db import get_connection
from app.security import SESSION_COOKIE, read_session_token


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    conn = get_connection(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()


def get_current_user(
    request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> sqlite3.Row | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    data = read_session_token(token)
    if not data:
        return None
    row = conn.execute(
        "SELECT * FROM users WHERE id = ? AND is_active = 1", (data["user_id"],)
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

    return dependency
