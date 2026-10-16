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

    # The editor's real token, and no redirect-following: with a fake token
    # verify_csrf would 403 on its own and mask a missing role check.
    editor = client_as("editor")
    token = re.search(r'name="csrf_token" value="([^"]+)"',
                      editor.get("/admin/notes/new").text).group(1)
    for path in ["/admin/pages", "/admin/pages/new", f"/admin/pages/{page_id}/edit"]:
        assert editor.get(path, follow_redirects=False).status_code == 403, path
    form = {"title": "x", "slug": "x", "body_md": "x", "nav_order": "0",
            "csrf_token": token}
    for path in ["/admin/pages", f"/admin/pages/{page_id}"]:
        assert editor.post(path, data=form, follow_redirects=False).status_code == 403, path
    for action in ["publish", "unpublish", "delete"]:
        assert editor.post(f"/admin/pages/{page_id}/{action}", data={"csrf_token": token},
                           follow_redirects=False).status_code == 403, action


def test_published_page_appears_in_public_navigation(client_as):
    admin = client_as("admin")
    admin.post("/admin/pages", data={
        "title": "My Story", "slug": "my-story", "body_md": "Content here.",
        "nav_order": "0", "csrf_token": _csrf(admin),
    })
    list_html = admin.get("/admin/pages").text
    page_id = re.search(r"pages/(\d+)/edit", list_html).group(1)
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
    page_id = re.search(r"pages/(\d+)/edit", list_html).group(1)
    token = re.search(r'name="csrf_token" value="([^"]+)"', list_html).group(1)
    admin.post(f"/admin/pages/{page_id}/publish", data={"csrf_token": token})

    response = admin.get("/pages/xss.html")
    assert response.status_code == 200
    html = response.text
    assert "<script>" not in html
    assert "onerror=" not in html


def test_duplicate_page_slug_rerenders_the_form_with_an_error(client_as, tmp_path):
    admin = client_as("admin")
    token = _csrf(admin)
    for slug in ("story", "guide"):
        admin.post("/admin/pages", data={
            "title": slug, "slug": slug, "body_md": "x", "nav_order": "0",
            "csrf_token": token,
        })

    created = admin.post("/admin/pages", data={
        "title": "Copy", "slug": "story", "body_md": "kept", "nav_order": "3",
        "csrf_token": token,
    }, follow_redirects=False)
    assert created.status_code == 409
    assert "already uses that slug" in created.text
    assert f'name="csrf_token" value="{token}"' in created.text
    assert 'value="Copy"' in created.text

    conn = get_connection(tmp_path / "test.db")
    try:
        guide_id = conn.execute(
            "SELECT id FROM content WHERE type='page' AND slug='guide'"
        ).fetchone()["id"]
    finally:
        conn.close()
    edited = admin.post(f"/admin/pages/{guide_id}", data={
        "title": "Renamed", "slug": "story", "body_md": "x", "nav_order": "0",
        "csrf_token": token,
    }, follow_redirects=False)
    assert edited.status_code == 409
    assert "already uses that slug" in edited.text
    assert f'action="{guide_id}"' in edited.text

    conn = get_connection(tmp_path / "test.db")
    try:
        rows = conn.execute(
            "SELECT title, slug FROM content WHERE type='page' ORDER BY id"
        ).fetchall()
    finally:
        conn.close()
    assert [(r["title"], r["slug"]) for r in rows] == [
        ("story", "story"), ("guide", "guide"),
    ]


def test_unsafe_page_slug_is_rejected_on_the_form(client_as, tmp_path):
    """T07 review: same slug rule as Notes; an unsafe slug never reaches the DB."""
    admin = client_as("admin")
    token = _csrf(admin)
    response = admin.post("/admin/pages", data={
        "title": "Bad", "slug": "Work With Me", "body_md": "x", "nav_order": "1",
        "csrf_token": token,
    }, follow_redirects=False)
    assert response.status_code == 422
    assert "Slug must be lowercase" in response.text
    conn = get_connection(tmp_path / "test.db")
    try:
        assert conn.execute("SELECT COUNT(*) FROM content").fetchone()[0] == 0
    finally:
        conn.close()
