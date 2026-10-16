"""T03: Notes vertical slice — create, draft, publish, sanitize."""
from __future__ import annotations

import re

from app.db import get_connection


def _csrf(client) -> str:
    """Pull the csrf token out of a page that renders a form."""
    html = client.get("/admin/notes/new").text
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, "no csrf token found on the new-Note form"
    return match.group(1)


def test_editor_can_create_a_note_as_a_draft(client_as, tmp_path):
    editor = client_as("editor")
    token = _csrf(editor)
    response = editor.post(
        "/admin/notes",
        data={"title": "Need-blind vs need-aware", "slug": "need-blind-vs-aware",
              "body_md": "The short version.", "csrf_token": token},
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection(tmp_path / "test.db")
    try:
        row = conn.execute(
            "SELECT * FROM content WHERE type='note' AND slug='need-blind-vs-aware'"
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row["status"] == "draft"


def test_editor_can_edit_her_own_draft(client_as, tmp_path):
    editor = client_as("editor")
    editor.post("/admin/notes", data={
        "title": "Draft one", "slug": "draft-one", "body_md": "v1",
        "csrf_token": _csrf(editor),
    })
    conn = get_connection(tmp_path / "test.db")
    try:
        note_id = conn.execute(
            "SELECT id FROM content WHERE slug='draft-one'"
        ).fetchone()["id"]
    finally:
        conn.close()

    edit_html = editor.get(f"/admin/notes/{note_id}/edit").text
    token = re.search(r'name="csrf_token" value="([^"]+)"', edit_html).group(1)
    response = editor.post(f"/admin/notes/{note_id}", data={
        "title": "Draft one, revised", "slug": "draft-one", "body_md": "v2",
        "csrf_token": token,
    }, follow_redirects=False)
    assert response.status_code == 303

    conn = get_connection(tmp_path / "test.db")
    try:
        row = conn.execute("SELECT * FROM content WHERE id=?", (note_id,)).fetchone()
    finally:
        conn.close()
    assert row["title"] == "Draft one, revised"
    assert row["body_md"] == "v2"


def test_editor_gets_403_publishing_a_note(client_as, tmp_path):
    editor = client_as("editor")
    editor.post("/admin/notes", data={
        "title": "Try to publish me", "slug": "try-publish", "body_md": "x",
        "csrf_token": _csrf(editor),
    })
    conn = get_connection(tmp_path / "test.db")
    try:
        note_id = conn.execute(
            "SELECT id FROM content WHERE slug='try-publish'"
        ).fetchone()["id"]
    finally:
        conn.close()

    response = editor.post(f"/admin/notes/{note_id}/publish",
                            data={"csrf_token": _csrf(editor)})
    assert response.status_code == 403


def test_admin_can_publish_unpublish_and_delete_any_note(client_as, tmp_path):
    editor = client_as("editor")
    editor.post("/admin/notes", data={
        "title": "Admin will manage me", "slug": "admin-managed", "body_md": "x",
        "csrf_token": _csrf(editor),
    })
    conn = get_connection(tmp_path / "test.db")
    try:
        note_id = conn.execute(
            "SELECT id FROM content WHERE slug='admin-managed'"
        ).fetchone()["id"]
    finally:
        conn.close()

    admin = client_as("admin")
    admin_token = _csrf(admin)

    assert admin.post(f"/admin/notes/{note_id}/publish", data={"csrf_token": admin_token},
                       follow_redirects=False).status_code == 303
    conn = get_connection(tmp_path / "test.db")
    try:
        assert conn.execute(
            "SELECT status FROM content WHERE id=?", (note_id,)
        ).fetchone()["status"] == "published"
    finally:
        conn.close()

    assert admin.post(f"/admin/notes/{note_id}/unpublish", data={"csrf_token": admin_token},
                       follow_redirects=False).status_code == 303
    assert admin.post(f"/admin/notes/{note_id}/delete", data={"csrf_token": admin_token},
                       follow_redirects=False).status_code == 303

    conn = get_connection(tmp_path / "test.db")
    try:
        assert conn.execute(
            "SELECT * FROM content WHERE id=?", (note_id,)
        ).fetchone() is None
    finally:
        conn.close()


def test_note_body_is_sanitized_in_the_admin_preview(client_as):
    editor = client_as("editor")
    editor.post("/admin/notes", data={
        "title": "Malicious", "slug": "malicious",
        "body_md": '<script>window.__xss=1</script><img src=x onerror="window.__xss=2">',
        "csrf_token": _csrf(editor),
    })
    html = editor.get("/admin/notes").text
    assert "<script>" not in html
    assert "onerror=" not in html


def test_create_note_without_csrf_token_is_rejected(client_as):
    editor = client_as("editor")
    response = editor.post("/admin/notes", data={
        "title": "No token", "slug": "no-token", "body_md": "x",
    })
    assert response.status_code == 403


def test_editor_cannot_edit_another_users_note(client_as, tmp_path):
    admin = client_as("admin")
    admin_token = _csrf(admin)
    admin.post("/admin/notes", data={
        "title": "Admin's own note", "slug": "admins-note", "body_md": "x",
        "csrf_token": admin_token,
    })
    conn = get_connection(tmp_path / "test.db")
    try:
        note_id = conn.execute(
            "SELECT id FROM content WHERE slug='admins-note'"
        ).fetchone()["id"]
    finally:
        conn.close()

    editor = client_as("editor")
    response = editor.get(f"/admin/notes/{note_id}/edit")
    assert response.status_code == 403


def test_notes_persist_across_a_fresh_db_connection(client_as, tmp_path):
    editor = client_as("editor")
    editor.post("/admin/notes", data={
        "title": "Survives restart", "slug": "survives-restart", "body_md": "x",
        "csrf_token": _csrf(editor),
    })
    # A fresh connection stands in for a server restart (T01/T02's pattern).
    conn = get_connection(tmp_path / "test.db")
    try:
        row = conn.execute(
            "SELECT * FROM content WHERE slug='survives-restart'"
        ).fetchone()
    finally:
        conn.close()
    assert row is not None


def test_duplicate_note_slug_rerenders_the_form_with_an_error(client_as, tmp_path):
    editor = client_as("editor")
    token = _csrf(editor)
    for slug in ("first", "second"):
        editor.post("/admin/notes", data={
            "title": slug, "slug": slug, "body_md": "x", "csrf_token": token,
        })

    created = editor.post("/admin/notes", data={
        "title": "Copy", "slug": "first", "body_md": "kept", "csrf_token": token,
    }, follow_redirects=False)
    assert created.status_code == 409
    assert "already uses that slug" in created.text
    assert f'name="csrf_token" value="{token}"' in created.text
    assert 'value="Copy"' in created.text

    conn = get_connection(tmp_path / "test.db")
    try:
        second_id = conn.execute(
            "SELECT id FROM content WHERE type='note' AND slug='second'"
        ).fetchone()["id"]
    finally:
        conn.close()
    edited = editor.post(f"/admin/notes/{second_id}", data={
        "title": "Renamed", "slug": "first", "body_md": "x", "csrf_token": token,
    }, follow_redirects=False)
    assert edited.status_code == 409
    assert "already uses that slug" in edited.text
    assert f'action="{second_id}"' in edited.text

    conn = get_connection(tmp_path / "test.db")
    try:
        rows = conn.execute(
            "SELECT title, slug FROM content WHERE type='note' ORDER BY id"
        ).fetchall()
    finally:
        conn.close()
    assert [(r["title"], r["slug"]) for r in rows] == [
        ("first", "first"), ("second", "second"),
    ]


def test_unsafe_note_slug_is_rejected_on_the_form(client_as, tmp_path):
    """T07 review: a slug becomes a file name in site/, so the form rejects one
    that would break (or escape) the export instead of failing `cms publish`."""
    editor = client_as("editor")
    token = _csrf(editor)
    for bad in ("My Note", "../evil", "UPPER"):
        response = editor.post("/admin/notes", data={
            "title": "Bad", "slug": bad, "body_md": "x", "csrf_token": token,
        }, follow_redirects=False)
        assert response.status_code == 422, bad
        assert "Slug must be lowercase" in response.text
    conn = get_connection(tmp_path / "test.db")
    try:
        assert conn.execute("SELECT COUNT(*) FROM content").fetchone()[0] == 0
    finally:
        conn.close()
