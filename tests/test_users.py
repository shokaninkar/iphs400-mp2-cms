"""T06: User management — admin creates users, changes roles, deactivates."""
from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.db import get_connection
from app.security import SESSION_COOKIE


def _csrf(client) -> str:
    html = client.get("/admin/users/new").text
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, "no csrf token found on the new-user form"
    return match.group(1)


def _user(tmp_path, email: str):
    conn = get_connection(tmp_path / "test.db")
    try:
        return conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    finally:
        conn.close()


def _create(admin, email="aigerim@example.test", password="draft-notes-pw",
            role="editor", token=None):
    return admin.post("/admin/users/new", data={
        "email": email, "password": password, "role": role,
        "csrf_token": token or _csrf(admin),
    }, follow_redirects=False)


def _login(app_client: TestClient, email: str, password: str):
    return app_client.post("/login", data={"email": email, "password": password},
                           follow_redirects=False)


def test_admin_can_create_a_user_who_can_then_log_in(client_as, tmp_path):
    admin = client_as("admin")
    response = _create(admin)
    assert response.status_code == 303

    row = _user(tmp_path, "aigerim@example.test")
    assert row["role"] == "editor"
    assert row["is_active"] == 1
    assert row["password_hash"].startswith("$argon2")
    assert "draft-notes-pw" not in row["password_hash"]

    assert "aigerim@example.test" in admin.get("/admin/users").text

    fresh = TestClient(admin.app)
    login = _login(fresh, "aigerim@example.test", "draft-notes-pw")
    assert login.status_code == 303
    assert SESSION_COOKIE in login.cookies


def test_admin_can_create_another_admin(client_as, tmp_path):
    admin = client_as("admin")
    assert _create(admin, email="second@example.test", role="admin").status_code == 303
    assert _user(tmp_path, "second@example.test")["role"] == "admin"


def test_admin_can_change_a_users_role(client_as, tmp_path):
    admin = client_as("admin")
    token = _csrf(admin)
    editor_id = _user(tmp_path, "editor@example.test")["id"]

    response = admin.post(f"/admin/users/{editor_id}/role",
                          data={"role": "admin", "csrf_token": token},
                          follow_redirects=False)
    assert response.status_code == 303
    assert _user(tmp_path, "editor@example.test")["role"] == "admin"


def test_role_change_takes_effect_on_an_existing_session(client_as, tmp_path):
    """The session cookie carries the role, but require_role reads it from the
    DB row, so a demoted admin loses access without logging out."""
    admin = client_as("admin")
    _create(admin, email="second@example.test", password="pw-second", role="admin")
    second = TestClient(admin.app)
    _login(second, "second@example.test", "pw-second")
    assert second.get("/admin/users").status_code == 200

    second_id = _user(tmp_path, "second@example.test")["id"]
    admin.post(f"/admin/users/{second_id}/role",
               data={"role": "editor", "csrf_token": _csrf(admin)})
    assert second.get("/admin/users").status_code == 403


def test_admin_can_deactivate_a_user_and_their_login_is_refused(client_as, tmp_path):
    admin = client_as("admin")
    editor_id = _user(tmp_path, "editor@example.test")["id"]

    response = admin.post(f"/admin/users/{editor_id}/deactivate",
                          data={"csrf_token": _csrf(admin)}, follow_redirects=False)
    assert response.status_code == 303
    assert _user(tmp_path, "editor@example.test")["is_active"] == 0

    fresh = TestClient(admin.app)
    login = _login(fresh, "editor@example.test", "test-editor-pw")
    assert login.status_code == 200
    assert SESSION_COOKIE not in login.cookies
    assert "Incorrect email or password." in login.text


def test_deactivation_ends_an_existing_session(client_as, tmp_path):
    editor = client_as("editor")
    admin = client_as("admin")
    assert editor.get("/admin").status_code == 200

    editor_id = _user(tmp_path, "editor@example.test")["id"]
    admin.post(f"/admin/users/{editor_id}/deactivate",
               data={"csrf_token": _csrf(admin)})

    response = editor.get("/admin", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_admin_cannot_demote_or_deactivate_themselves(client_as, tmp_path):
    admin = client_as("admin")
    token = _csrf(admin)
    admin_id = _user(tmp_path, "admin@example.test")["id"]

    assert admin.post(f"/admin/users/{admin_id}/role",
                      data={"role": "editor", "csrf_token": token}).status_code == 400
    assert admin.post(f"/admin/users/{admin_id}/deactivate",
                      data={"csrf_token": token}).status_code == 400
    row = _user(tmp_path, "admin@example.test")
    assert (row["role"], row["is_active"]) == ("admin", 1)


def test_duplicate_email_rerenders_the_form_with_an_error(client_as, tmp_path):
    admin = client_as("admin")
    token = _csrf(admin)
    response = _create(admin, email="editor@example.test", token=token)
    assert response.status_code == 409
    assert "already has an account" in response.text
    assert f'name="csrf_token" value="{token}"' in response.text
    assert 'value="editor@example.test"' in response.text
    assert "draft-notes-pw" not in response.text


def test_unknown_role_is_rejected(client_as, tmp_path):
    admin = client_as("admin")
    token = _csrf(admin)
    assert _create(admin, email="x@example.test", role="owner",
                   token=token).status_code == 422
    assert _user(tmp_path, "x@example.test") is None

    editor_id = _user(tmp_path, "editor@example.test")["id"]
    assert admin.post(f"/admin/users/{editor_id}/role",
                      data={"role": "owner", "csrf_token": token}).status_code == 422
    assert _user(tmp_path, "editor@example.test")["role"] == "editor"


def test_user_management_requires_csrf(client_as, tmp_path):
    admin = client_as("admin")
    editor_id = _user(tmp_path, "editor@example.test")["id"]
    assert admin.post("/admin/users/new", data={
        "email": "x@example.test", "password": "pw", "role": "editor",
    }).status_code == 403
    assert admin.post(f"/admin/users/{editor_id}/role",
                      data={"role": "admin", "csrf_token": "wrong"}).status_code == 403
    assert admin.post(f"/admin/users/{editor_id}/deactivate",
                      data={}).status_code == 403
    assert _user(tmp_path, "x@example.test") is None
    row = _user(tmp_path, "editor@example.test")
    assert (row["role"], row["is_active"]) == ("editor", 1)


def test_unknown_user_id_is_404(client_as):
    admin = client_as("admin")
    token = _csrf(admin)
    assert admin.post("/admin/users/9999/role",
                      data={"role": "admin", "csrf_token": token}).status_code == 404
    assert admin.post("/admin/users/9999/deactivate",
                      data={"csrf_token": token}).status_code == 404


def test_editor_gets_403_on_every_user_management_route(client_as, tmp_path):
    """Uses the editor's own valid CSRF token, so only require_role can 403."""
    editor = client_as("editor")
    admin_id = _user(tmp_path, "admin@example.test")["id"]
    html = editor.get("/admin/notes/new").text
    token = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    assert editor.get("/admin/users").status_code == 403
    assert editor.get("/admin/users/new").status_code == 403
    # No redirect-following: a 303 to /admin/users would 403 there and mask
    # a missing role check on the POST itself.
    assert editor.post("/admin/users/new", data={
        "email": "x@example.test", "password": "pw", "role": "admin",
        "csrf_token": token,
    }, follow_redirects=False).status_code == 403
    assert editor.post(f"/admin/users/{admin_id}/role",
                       data={"role": "editor", "csrf_token": token},
                       follow_redirects=False).status_code == 403
    assert editor.post(f"/admin/users/{admin_id}/deactivate",
                       data={"csrf_token": token},
                       follow_redirects=False).status_code == 403
    assert _user(tmp_path, "x@example.test") is None


def test_anonymous_is_redirected_to_login_from_user_routes(client):
    responses = [
        client.get("/admin/users", follow_redirects=False),
        client.get("/admin/users/new", follow_redirects=False),
        client.post("/admin/users/new", data={
            "email": "x@example.test", "password": "pw", "role": "admin",
        }, follow_redirects=False),
        client.post("/admin/users/1/role", data={"role": "editor"},
                    follow_redirects=False),
        client.post("/admin/users/1/deactivate", follow_redirects=False),
    ]
    for response in responses:
        url = response.request.url.path
        assert response.status_code == 303, url
        assert response.headers["location"] == "/login", url


def test_admin_home_links_to_user_management(client_as):
    assert 'href="admin/users"' in client_as("admin").get("/admin").text
    assert "admin/users" not in client_as("editor").get("/admin").text


def test_user_templates_use_relative_urls(client_as):
    """Checker: no href="/..." or action="/..." in HTML."""
    admin = client_as("admin")
    for html in (admin.get("/admin/users").text, admin.get("/admin/users/new").text):
        assert 'href="/' not in html
        assert 'action="/' not in html
