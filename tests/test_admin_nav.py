"""T11: admin nav, logout button, success messages (#11)."""
from __future__ import annotations

import re


def _token(client, path="/admin/notes/new") -> str:
    return re.search(r'name="csrf_token" value="([^"]+)"', client.get(path).text).group(1)


def test_admin_screens_have_nav_and_a_logout_form(client_as):
    admin = client_as("admin")
    html = admin.get("/admin/content").text
    for label in ("Dashboard", "Content", "Notes", "Pages", "Users", "Log out"):
        assert label in html, label
    assert re.search(r'<form method="post" action="[^"/][^"]*logout"', html)
    assert 'href="/' not in html and 'action="/' not in html


def test_editor_nav_hides_admin_only_links(client_as):
    html = client_as("editor").get("/admin").text
    nav = html.split('<nav aria-label="Admin">')[1].split("</nav>")[0]
    assert "Pages" not in nav and "Users" not in nav and "Log out" in nav


def test_logout_requires_csrf_and_then_logs_out(client_as):
    admin = client_as("admin")
    assert admin.post("/logout", follow_redirects=False).status_code == 403
    assert admin.post("/logout", data={"csrf_token": "wrong"},
                      follow_redirects=False).status_code == 403
    token = _token(admin)
    response = admin.post("/logout", data={"csrf_token": token}, follow_redirects=False)
    assert response.status_code == 303 and response.headers["location"] == "/login"
    assert admin.get("/admin", follow_redirects=False).status_code == 303


def test_saving_a_note_shows_a_success_message(client_as):
    admin = client_as("admin")
    response = admin.post("/admin/notes", data={
        "title": "Hi", "slug": "hi", "body_md": "x", "csrf_token": _token(admin)})
    assert response.status_code == 200
    assert 'role="status"' in response.text and "Saved." in response.text


def test_publishing_a_page_shows_a_success_message(client_as):
    admin = client_as("admin")
    token = _token(admin, "/admin/pages/new")
    admin.post("/admin/pages", data={"title": "About", "slug": "about", "body_md": "x",
                                     "nav_order": "1", "csrf_token": token})
    response = admin.post("/admin/pages/1/publish", data={"csrf_token": token})
    assert "Published." in response.text


def test_unknown_message_key_is_ignored(client_as):
    html = client_as("admin").get("/admin/notes?done=<script>").text
    assert 'role="status"' not in html


def test_unpublish_and_delete_show_success_messages(client_as):
    admin = client_as("admin")
    token = _token(admin)
    admin.post("/admin/notes", data={"title": "Hi", "slug": "hi", "body_md": "x",
                                     "csrf_token": token})
    admin.post("/admin/notes/1/publish", data={"csrf_token": token})
    assert "Unpublished." in admin.post("/admin/notes/1/unpublish",
                                        data={"csrf_token": token}).text
    assert "Deleted." in admin.post("/admin/notes/1/delete", data={"csrf_token": token}).text
