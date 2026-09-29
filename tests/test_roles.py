"""T02: role-based access control.

/admin itself is shared (admin + editor both land on the dashboard); the
require_role() dependency also needs to prove it can lock a route down to a
single role, which no real route needs yet (Pages/Users arrive in T04/T06) —
so this test mounts a throwaway admin-only probe route on its own app
instance to exercise that path now, rather than waiting on a later ticket.
"""
from __future__ import annotations

from fastapi import Depends
from fastapi.testclient import TestClient

from app.db import init_db
from app.deps import require_role
from app.main import create_app
from conftest import DEMO_USERS, _seed_demo_users


def test_anonymous_is_redirected_to_login(client):
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_admin_can_reach_the_shared_dashboard(client_as):
    assert client_as("admin").get("/admin").status_code == 200


def test_editor_can_reach_the_shared_dashboard(client_as):
    assert client_as("editor").get("/admin").status_code == 200


def _client_with_admin_only_probe(tmp_path, role: str) -> TestClient:
    db_path = tmp_path / "test.db"
    init_db(db_path)
    _seed_demo_users(db_path)
    app = create_app(db_path=db_path)

    @app.get("/admin/__probe_admin_only")
    def _probe(user=Depends(require_role("admin"))):
        return {"ok": True}

    client = TestClient(app)
    user = DEMO_USERS[role]
    client.post("/login", data={"email": user["email"], "password": user["password"]})
    return client


def test_editor_gets_403_on_an_admin_only_route(tmp_path):
    client = _client_with_admin_only_probe(tmp_path, "editor")
    assert client.get("/admin/__probe_admin_only").status_code == 403


def test_admin_passes_an_admin_only_route(tmp_path):
    client = _client_with_admin_only_probe(tmp_path, "admin")
    assert client.get("/admin/__probe_admin_only").status_code == 200
