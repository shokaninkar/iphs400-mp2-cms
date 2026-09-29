"""Shared test fixtures.

`client` gives you the app. `client_as(role)` gives you a client that is logged
in as a seeded user of that role — it works as soon as your login route exists,
so access-control tests stay one line:

    def test_editor_cannot_manage_users(client_as):
        assert client_as("editor").get("/admin/users").status_code in (302, 403)

Each test gets its own on-disk SQLite DB under tmp_path, seeded with the two
demo users below, so tests never see another test's data or the developer's
real cms.db.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db import get_connection, init_db, seed_user
from app.main import create_app

# Matches scripts/seed_demo.py. Passwords come from the environment there; in
# tests they are fixed and meaningless.
DEMO_USERS = {
    "admin": {"email": "admin@example.test", "password": "test-admin-pw"},
    "editor": {"email": "editor@example.test", "password": "test-editor-pw"},
}


def _seed_demo_users(db_path) -> None:
    conn = get_connection(db_path)
    try:
        for role, info in DEMO_USERS.items():
            seed_user(conn, info["email"], info["password"], role)
    finally:
        conn.close()


@pytest.fixture
def client(tmp_path) -> TestClient:
    db_path = tmp_path / "test.db"
    init_db(db_path)
    _seed_demo_users(db_path)
    return TestClient(create_app(db_path=db_path))


@pytest.fixture
def client_as(tmp_path):
    """Return a factory: client_as("editor") -> a logged-in TestClient."""
    db_path = tmp_path / "test.db"
    init_db(db_path)
    _seed_demo_users(db_path)

    def _login(role: str) -> TestClient:
        user = DEMO_USERS[role]
        c = TestClient(create_app(db_path=db_path))
        response = c.post("/login", data={"email": user["email"],
                                          "password": user["password"]},
                          follow_redirects=False)
        if response.status_code == 404:
            pytest.skip("No /login route yet — build the login ticket first.")
        assert response.status_code in (200, 302, 303), (
            f"Login as {role} failed with {response.status_code}")
        return c

    return _login
