"""T01: login, logout. Passwords are argon2-hashed (D1); sessions are a signed
cookie (app/security.py), not a server-side store.

Login is deliberately exempt from CSRF (see CONTEXT.md): there is no prior
session for a forged request to ride on, and `tests/conftest.py`'s
`client_as` fixture — the backbone of every role-based test in later tickets —
logs in without a token. CSRF is enforced starting with the first
authenticated, state-changing form (T03 onward).
"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app import settings
from app.deps import get_db
from app.security import (
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    create_session_token,
    verify_password,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES))


@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(request, "admin/login.html", {"error": None})


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    conn: sqlite3.Connection = Depends(get_db),
):
    user = conn.execute(
        "SELECT * FROM users WHERE email = ? AND is_active = 1", (email,)
    ).fetchone()

    if user is None or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse(
            request,
            "admin/login.html",
            {"error": "Incorrect email or password."},
            status_code=200,
        )

    token = create_session_token(user["id"], user["role"])
    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie(
        SESSION_COOKIE, token, max_age=SESSION_MAX_AGE, httponly=True, samesite="lax"
    )
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response
