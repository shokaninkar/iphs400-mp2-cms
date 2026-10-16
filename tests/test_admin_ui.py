"""T10: admin stylesheet and a friendly 403 page (#10)."""
from __future__ import annotations


def test_editor_sees_an_html_403_page_with_a_way_back(client_as):
    response = client_as("editor").get("/admin/users", follow_redirects=False)
    assert response.status_code == 403
    assert response.headers["content-type"].startswith("text/html")
    assert "have access" in response.text
    # Relative link back to the dashboard (no root-absolute href).
    assert 'href="../admin"' in response.text
    assert 'href="/' not in response.text


def test_anonymous_admin_request_still_redirects_to_login(client):
    response = client.get("/admin/users", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_not_found_is_unchanged(client):
    response = client.get("/pages/no-such-page.html")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_admin_screens_carry_the_admin_stylesheet(client_as):
    admin = client_as("admin")
    for path in ("/admin", "/admin/content", "/admin/notes/new", "/admin/users"):
        assert 'id="admin-css"' in admin.get(path).text, path


def test_login_screen_is_styled_too(client):
    assert 'id="admin-css"' in client.get("/login").text


def test_public_preview_does_not_get_the_admin_stylesheet(client):
    assert 'id="admin-css"' not in client.get("/").text


def test_each_known_403_reason_has_its_own_message():
    """Pins the `detail` strings app/deps.py and app/routes/notes.py raise, so a
    reworded detail can't silently fall back to the generic message."""
    import inspect

    from app import deps, main
    from app.routes import notes

    raised = inspect.getsource(deps) + inspect.getsource(notes)
    for detail in main.FORBIDDEN_MESSAGES:
        assert f'detail="{detail}"' in raised, detail


def test_editor_editing_someone_elses_note_gets_the_specific_message(client_as):
    admin = client_as("admin")
    page = admin.get("/admin/notes/new").text
    token = page.split('name="csrf_token" value="')[1].split('"')[0]
    admin.post("/admin/notes", data={"title": "Admin note", "slug": "admin-note",
                                     "body_md": "x", "csrf_token": token})
    response = client_as("editor").get("/admin/notes/1/edit")
    assert response.status_code == 403
    assert "only edit Notes you wrote" in response.text
