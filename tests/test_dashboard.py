"""T05: admin console UX — dashboard counts, filterable content list, editor preview."""
from __future__ import annotations

import re

from app.db import get_connection


def _csrf(client) -> str:
    html = client.get("/admin/notes/new").text
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, "no csrf token found on the new-Note form"
    return match.group(1)


def _seed(db_path) -> None:
    """Two Pages and four Notes; the editor wrote two of the Notes."""
    conn = get_connection(db_path)
    try:
        ids = {r["role"]: r["id"] for r in conn.execute("SELECT id, role FROM users")}
        rows = [
            ("page", "The Guide", "guide", "published", ids["admin"]),
            ("page", "Work With Me", "work-with-me", "draft", ids["admin"]),
            ("note", "Need-blind vs need-aware", "need-blind", "published", ids["admin"]),
            ("note", "Kenyon worked example", "kenyon", "draft", ids["admin"]),
            ("note", "Editor draft one", "editor-one", "draft", ids["editor"]),
            ("note", "Editor published", "editor-pub", "published", ids["editor"]),
        ]
        conn.executemany(
            "INSERT INTO content (type, title, slug, status, author_id) "
            "VALUES (?, ?, ?, ?, ?)", rows,
        )
        conn.commit()
    finally:
        conn.close()


def _count(html: str, type_: str, status: str) -> str:
    match = re.search(rf'data-count="{type_}-{status}">(\d+)<', html)
    assert match, f"no {type_}-{status} count on the dashboard"
    return match.group(1)


# --- Dashboard counts ------------------------------------------------------

def test_admin_dashboard_counts_pages_and_notes_by_status(client_as, tmp_path):
    admin = client_as("admin")
    _seed(tmp_path / "test.db")
    html = admin.get("/admin").text
    assert _count(html, "page", "draft") == "1"
    assert _count(html, "page", "published") == "1"
    assert _count(html, "note", "draft") == "2"
    assert _count(html, "note", "published") == "2"


def test_editor_dashboard_counts_only_their_own_notes(client_as, tmp_path):
    editor = client_as("editor")
    _seed(tmp_path / "test.db")
    html = editor.get("/admin").text
    assert _count(html, "note", "draft") == "1"
    assert _count(html, "note", "published") == "1"
    assert 'data-count="page-' not in html


def test_dashboard_redirects_anonymous_to_login(client):
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


# --- Content list filters --------------------------------------------------

def test_content_list_shows_everything_to_admin_by_default(client_as, tmp_path):
    admin = client_as("admin")
    _seed(tmp_path / "test.db")
    html = admin.get("/admin/content").text
    for title in ["The Guide", "Work With Me", "Kenyon worked example", "Editor draft one"]:
        assert title in html


def test_content_list_filters_by_status(client_as, tmp_path):
    admin = client_as("admin")
    _seed(tmp_path / "test.db")
    html = admin.get("/admin/content?status=draft").text
    assert "Work With Me" in html
    assert "Kenyon worked example" in html
    assert "The Guide" not in html
    assert "Need-blind vs need-aware" not in html


def test_content_list_filters_by_type(client_as, tmp_path):
    admin = client_as("admin")
    _seed(tmp_path / "test.db")
    html = admin.get("/admin/content?type=page").text
    assert "The Guide" in html
    assert "Work With Me" in html
    assert "Kenyon worked example" not in html


def test_content_list_combines_type_and_status(client_as, tmp_path):
    admin = client_as("admin")
    _seed(tmp_path / "test.db")
    html = admin.get("/admin/content?type=note&status=published").text
    assert "Need-blind vs need-aware" in html
    assert "Editor published" in html
    assert "Kenyon worked example" not in html
    assert "The Guide" not in html


def test_content_list_ignores_unknown_filter_values(client_as, tmp_path):
    """The "All" option submits an empty value; junk is treated the same way."""
    admin = client_as("admin")
    _seed(tmp_path / "test.db")
    for query in ["?type=&status=", "?type=bogus&status=x' OR 1=1--"]:
        response = admin.get("/admin/content" + query)
        assert response.status_code == 200
        assert "The Guide" in response.text
        assert "Kenyon worked example" in response.text


def test_editor_content_list_shows_only_their_own_notes(client_as, tmp_path):
    editor = client_as("editor")
    _seed(tmp_path / "test.db")
    for query in ["", "?type=page", "?type=note"]:
        html = editor.get("/admin/content" + query).text
        assert "The Guide" not in html
        assert "Kenyon worked example" not in html
    html = editor.get("/admin/content?type=note").text
    assert "Editor draft one" in html
    assert "Editor published" in html


def test_content_list_redirects_anonymous_to_login(client):
    response = client.get("/admin/content", follow_redirects=False)
    assert response.status_code == 303


# --- Markdown preview ------------------------------------------------------

def test_preview_renders_markdown(client_as):
    editor = client_as("editor")
    response = editor.post("/admin/preview", data={
        "body_md": "# Full aid\n\n**need-aware**", "csrf_token": _csrf(editor),
    })
    assert response.status_code == 200
    assert "<h1>Full aid</h1>" in response.text
    assert "<strong>need-aware</strong>" in response.text


def test_preview_sanitizes_script_and_event_handlers(client_as):
    """D4: nothing in the preview may execute."""
    admin = client_as("admin")
    response = admin.post("/admin/preview", data={
        "body_md": '<script>alert(1)</script>\n\n<img src=x onerror="alert(2)">',
        "csrf_token": _csrf(admin),
    })
    assert response.status_code == 200
    assert "<script" not in response.text
    assert "onerror" not in response.text


def test_preview_requires_csrf(client_as):
    editor = client_as("editor")
    response = editor.post("/admin/preview", data={"body_md": "x", "csrf_token": "nope"})
    assert response.status_code == 403


def test_preview_requires_login(client):
    response = client.post("/admin/preview", data={"body_md": "x"},
                           follow_redirects=False)
    assert response.status_code == 303


def test_editor_form_preview_of_a_saved_body_is_sanitized(client_as, tmp_path):
    """D4 on the server-rendered pane: save through the real form, reopen it."""
    editor = client_as("editor")
    body = '## Kenyon\n\n<script>alert(1)</script>\n\n<img src=x onerror="alert(2)">'
    assert editor.post("/admin/notes", data={
        "title": "Kenyon", "slug": "kenyon", "body_md": body, "csrf_token": _csrf(editor),
    }, follow_redirects=False).status_code == 303
    conn = get_connection(tmp_path / "test.db")
    try:
        note_id = conn.execute("SELECT id FROM content WHERE slug='kenyon'").fetchone()["id"]
    finally:
        conn.close()
    html = editor.get(f"/admin/notes/{note_id}/edit").text
    preview = re.search(r'<div id="preview"[^>]*>(.*?)</div>', html, re.S)
    assert preview, "no preview pane on the edit form"
    assert "<h2>Kenyon</h2>" in preview.group(1)
    assert "<script" not in preview.group(1)
    assert "onerror" not in preview.group(1)
    # The textarea echoes the raw body, so it must arrive escaped.
    assert "<script>alert(1)</script>" not in html


def test_admin_screens_link_back_to_the_dashboard(client_as):
    html = client_as("admin").get("/admin/notes/new").text
    assert 'class="brand" href="../../admin"' in html
    assert "style.css" not in html


# --- Relative links (CLAUDE.md hard constraint; checker) -------------------

ADMIN_SCREENS = ["/admin", "/admin/content", "/admin/notes", "/admin/notes/new",
                 "/admin/pages", "/admin/pages/new"]


def test_admin_screens_have_no_root_absolute_links(client_as, tmp_path):
    admin = client_as("admin")
    _seed(tmp_path / "test.db")
    for path in ADMIN_SCREENS:
        html = admin.get(path).text
        assert not re.search(r'(href|action|src)="/', html), path


def test_edit_form_action_resolves_after_error_rerender(client_as, tmp_path):
    """A duplicate-slug error re-renders the edit form at /admin/notes/<id>
    (one level shallower than /edit); its action must still point there."""
    admin = client_as("admin")
    _seed(tmp_path / "test.db")
    conn = get_connection(tmp_path / "test.db")
    try:
        note_id = conn.execute("SELECT id FROM content WHERE slug='kenyon'").fetchone()["id"]
    finally:
        conn.close()
    edit = admin.get(f"/admin/notes/{note_id}/edit").text
    assert f'action="../{note_id}"' in edit
    rerender = admin.post(f"/admin/notes/{note_id}", data={
        "title": "x", "slug": "need-blind", "body_md": "", "csrf_token": _csrf(admin),
    })
    assert rerender.status_code == 409
    assert f'action="{note_id}"' in rerender.text
