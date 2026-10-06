"""T04: Pages vertical slice — admin-only, published pages in public nav."""
from __future__ import annotations

import re

from app.db import get_connection


def _csrf(client) -> str:
    html = client.get("/admin/pages/new").text
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, "no csrf token found on the new-Page form"
    return match.group(1)


def test_admin_can_create_edit_and_delete_a_page(client_as, tmp_path):
    admin = client_as("admin")
    response = admin.post("/admin/pages", data={
        "title": "The Guide", "slug": "guide", "body_md": "How to find full aid.",
        "nav_order": "1", "csrf_token": _csrf(admin),
    }, follow_redirects=False)
    assert response.status_code == 303

    conn = get_connection(tmp_path / "test.db")
    try:
        page_id = conn.execute(
            "SELECT id FROM content WHERE type='page' AND slug='guide'"
        ).fetchone()["id"]
    finally:
        conn.close()

    edit_html = admin.get(f"/admin/pages/{page_id}/edit").text
    token = re.search(r'name="csrf_token" value="([^"]+)"', edit_html).group(1)
    assert admin.post(f"/admin/pages/{page_id}", data={
        "title": "The Guide, revised", "slug": "guide", "body_md": "Updated.",
        "nav_order": "1", "csrf_token": token,
    }, follow_redirects=False).status_code == 303

    conn = get_connection(tmp_path / "test.db")
    try:
        row = conn.execute("SELECT * FROM content WHERE id=?", (page_id,)).fetchone()
    finally:
        conn.close()
    assert row["title"] == "The Guide, revised"

    assert admin.post(f"/admin/pages/{page_id}/delete",
                       data={"csrf_token": token}, follow_redirects=False).status_code == 303
    conn = get_connection(tmp_path / "test.db")
    try:
        assert conn.execute(
            "SELECT * FROM content WHERE id=?", (page_id,)
        ).fetchone() is None
    finally:
        conn.close()


def test_editor_gets_403_on_every_page_route(client_as, tmp_path):
    admin = client_as("admin")
    admin.post("/admin/pages", data={
        "title": "Work With Me", "slug": "work-with-me", "body_md": "x",
        "nav_order": "2", "csrf_token": _csrf(admin),
    })
    conn = get_connection(tmp_path / "test.db")
    try:
        page_id = conn.execute(
            "SELECT id FROM content WHERE slug='work-with-me'"
        ).fetchone()["id"]
    finally:
        conn.close()

    editor = client_as("editor")
    assert editor.get("/admin/pages").status_code == 403
    assert editor.get("/admin/pages/new").status_code == 403
    assert editor.get(f"/admin/pages/{page_id}/edit").status_code == 403
    assert editor.post("/admin/pages", data={
        "title": "x", "slug": "x", "body_md": "x", "nav_order": "0",
        "csrf_token": "whatever",
    }).status_code == 403
    assert editor.post(f"/admin/pages/{page_id}", data={
        "title": "x", "slug": "x", "body_md": "x", "nav_order": "0",
        "csrf_token": "whatever",
    }).status_code == 403
    assert editor.post(f"/admin/pages/{page_id}/publish",
                        data={"csrf_token": "whatever"}).status_code == 403
    assert editor.post(f"/admin/pages/{page_id}/unpublish",
                        data={"csrf_token": "whatever"}).status_code == 403
    assert editor.post(f"/admin/pages/{page_id}/delete",
                        data={"csrf_token": "whatever"}).status_code == 403


def test_published_page_appears_in_public_navigation(client_as):
    admin = client_as("admin")
    admin.post("/admin/pages", data={
        "title": "My Story", "slug": "my-story", "body_md": "Content here.",
        "nav_order": "0", "csrf_token": _csrf(admin),
    })
    list_html = admin.get("/admin/pages").text
    page_id = re.search(r"/admin/pages/(\d+)/edit", list_html).group(1)
    token = re.search(r'name="csrf_token" value="([^"]+)"', list_html).group(1)

    # Not yet published: shouldn't appear on the public home page.
    assert "My Story" not in admin.get("/").text

    admin.post(f"/admin/pages/{page_id}/publish", data={"csrf_token": token})

    home_html = admin.get("/").text
    assert "My Story" in home_html
    assert 'href="pages/my-story.html"' in home_html

    page_view = admin.get("/pages/my-story.html")
    assert page_view.status_code == 200
    assert "Content here." in page_view.text


def test_unpublished_page_is_not_viewable_on_the_public_route(client_as):
    admin = client_as("admin")
    admin.post("/admin/pages", data={
        "title": "Draft Page", "slug": "draft-page", "body_md": "x",
        "nav_order": "0", "csrf_token": _csrf(admin),
    })
    response = admin.get("/pages/draft-page.html")
    assert response.status_code == 404


def test_pages_persist_across_a_fresh_db_connection(client_as, tmp_path):
    admin = client_as("admin")
    admin.post("/admin/pages", data={
        "title": "Survives restart", "slug": "survives-restart-page", "body_md": "x",
        "nav_order": "0", "csrf_token": _csrf(admin),
    })
    conn = get_connection(tmp_path / "test.db")
    try:
        row = conn.execute(
            "SELECT * FROM content WHERE slug='survives-restart-page'"
        ).fetchone()
    finally:
        conn.close()
    assert row is not None


def test_anonymous_is_redirected_to_login_from_page_routes(client):
    response = client.get("/admin/pages", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_page_body_is_sanitized_on_the_public_route(client_as):
    admin = client_as("admin")
    admin.post("/admin/pages", data={
        "title": "XSS", "slug": "xss",
        "body_md": '<script>window.__xss=1</script><img src=x onerror="window.__xss=2">',
        "nav_order": "0", "csrf_token": _csrf(admin),
    })
    list_html = admin.get("/admin/pages").text
    page_id = re.search(r"/admin/pages/(\d+)/edit", list_html).group(1)
    token = re.search(r'name="csrf_token" value="([^"]+)"', list_html).group(1)
    admin.post(f"/admin/pages/{page_id}/publish", data={"csrf_token": token})

    response = admin.get("/pages/xss.html")
    assert response.status_code == 200
    html = response.text
    assert "<script>" not in html
    assert "onerror=" not in html
