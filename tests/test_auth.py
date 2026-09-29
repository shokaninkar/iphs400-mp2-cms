"""T01: login, logout, password hashing."""
from __future__ import annotations

from app.db import get_connection


def test_correct_login_redirects_to_admin_and_sets_cookie(client):
    response = client.post(
        "/login",
        data={"email": "admin@example.test", "password": "test-admin-pw"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin"
    assert "cms_session" in response.cookies


def test_wrong_password_is_rejected_with_a_message(client):
    response = client.post(
        "/login",
        data={"email": "admin@example.test", "password": "not-the-password"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "incorrect" in response.text.lower()
    assert "cms_session" not in response.cookies


def test_unknown_email_is_rejected_with_the_same_message(client):
    response = client.post(
        "/login",
        data={"email": "nobody@example.test", "password": "whatever"},
    )
    assert response.status_code == 200
    assert "incorrect" in response.text.lower()


def test_logout_clears_the_session_cookie(client_as):
    c = client_as("admin")
    response = c.post("/logout", follow_redirects=False)
    assert response.status_code == 303
    set_cookie = response.headers.get("set-cookie", "")
    assert "cms_session=" in set_cookie
    assert "Max-Age=0" in set_cookie or "max-age=0" in set_cookie.lower()


def test_passwords_are_stored_as_argon2_hashes(client, tmp_path):
    db_path = tmp_path / "test.db"
    # `client` fixture already seeded this path; read it back directly.
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            ("admin@example.test",),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row["password_hash"].startswith("$argon2")
