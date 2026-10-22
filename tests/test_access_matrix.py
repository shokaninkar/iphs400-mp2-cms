"""MP2plus S1: direct-URL access matrix.

Every admin-only route is read from the app's router, not typed by hand: a
route is admin-only when one of its dependencies is `require_role("admin")`,
which carries `roles == ("admin",)` (app/deps.py). A new route marked the same
way is covered with no edit here.

For each route and method: the editor gets 403 or a redirect, and an anonymous
visitor is redirected to /login. Path parameters are filled with the id of a
seeded item, so a route refuses on role rather than 404 or 422.
"""
from __future__ import annotations

import re

from fastapi import Depends
from fastapi.routing import APIRoute, iter_route_contexts
from fastapi.testclient import TestClient

from app.db import get_connection, init_db
from app.deps import require_role
from app.main import create_app
from conftest import _seed_demo_users

ADMIN_ONLY = ("admin",)


def _is_admin_only(dependant) -> bool:
    for dep in dependant.dependencies:
        if getattr(dep.call, "roles", None) == ADMIN_ONLY or _is_admin_only(dep):
            return True
    return False


def admin_only_routes(app) -> list[tuple[str, str]]:
    # FastAPI 0.141 keeps each include_router() as one lazy entry in
    # app.routes; iter_route_contexts() expands them, with full paths.
    return sorted(
        (method, ctx.path)
        for ctx in iter_route_contexts(app.routes)
        if isinstance(ctx.original_route, APIRoute)
        and _is_admin_only(ctx.original_route.dependant)
        for method in ctx.methods
    )


def _seed_content(db_path) -> dict[str, int]:
    """One Note and one Page, plus the editor's user id, keyed by the path
    parameter names the admin routes use."""
    conn = get_connection(db_path)
    try:
        admin_id = conn.execute(
            "SELECT id FROM users WHERE role = 'admin'").fetchone()["id"]
        editor_id = conn.execute(
            "SELECT id FROM users WHERE role = 'editor'").fetchone()["id"]
        ids = {"user_id": editor_id}
        for kind in ("note", "page"):
            cur = conn.execute(
                "INSERT INTO content (type, title, slug, author_id) "
                "VALUES (?, ?, ?, ?)",
                (kind, f"Seeded {kind}", f"seeded-{kind}", admin_id),
            )
            ids[f"{kind}_id"] = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    return ids


def _fill(path: str, ids: dict[str, int]) -> str:
    # An unknown parameter falls back to the admin's id (1), which exists.
    return re.sub(r"\{(\w+)\}", lambda m: str(ids.get(m.group(1), 1)), path)


def _csrf(client) -> str:
    return re.search(r'name="csrf_token" value="([^"]+)"',
                     client.get("/admin").text).group(1)


def _request(client, method, url, data=None):
    return client.request(method, url, data=data, follow_redirects=False)


def test_admin_only_routes_are_found_from_the_router(tmp_path):
    routes = admin_only_routes(create_app(db_path=tmp_path / "test.db"))

    # Spot checks that the marker reaches every module with admin-only routes.
    assert ("GET", "/admin/users") in routes
    assert ("POST", "/admin/pages") in routes
    assert ("POST", "/admin/notes/{note_id}/publish") in routes
    # Shared routes (admin + editor) are not admin-only.
    assert ("GET", "/admin") not in routes
    assert ("GET", "/admin/notes") not in routes


def test_a_new_admin_only_route_is_found_without_editing_this_test(tmp_path):
    app = create_app(db_path=tmp_path / "test.db")

    @app.get("/admin/__scratch_admin_only")
    def scratch(_user=Depends(require_role("admin"))):
        return {"ok": True}

    assert ("GET", "/admin/__scratch_admin_only") in admin_only_routes(app)


def test_editor_is_refused_on_every_admin_only_route(client_as, tmp_path):
    editor = client_as("editor")
    ids = _seed_content(tmp_path / "test.db")
    token = _csrf(editor)
    routes = admin_only_routes(editor.app)
    assert routes, "no admin-only routes found"

    failures = []
    for method, path in routes:
        data = {"csrf_token": token} if method == "POST" else None
        response = _request(editor, method, _fill(path, ids), data)
        if not (response.status_code == 403 or 300 <= response.status_code < 400):
            failures.append(f"{method} {path} -> {response.status_code}")
    assert not failures, failures


def test_anonymous_is_redirected_to_login_on_every_admin_only_route(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    _seed_demo_users(db_path)
    ids = _seed_content(db_path)
    anonymous = TestClient(create_app(db_path=db_path))
    routes = admin_only_routes(anonymous.app)
    assert routes, "no admin-only routes found"

    failures = []
    for method, path in routes:
        response = _request(anonymous, method, _fill(path, ids))
        if not (response.status_code in (302, 303)
                and response.headers.get("location") == "/login"):
            failures.append(f"{method} {path} -> {response.status_code}")
    assert not failures, failures
