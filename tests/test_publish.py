"""T07: `cms publish` renders site/ from published content only (#8).

Each test seeds its own DB under tmp_path and renders into tmp_path/site, so
nothing here touches the developer's cms.db or site/.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.db import get_connection, init_db, seed_user
from app.publish import render_site


def _db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test.db"
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        seed_user(conn, "admin@example.test", "pw", "admin")
    finally:
        conn.close()
    return db_path


def _add(db_path: Path, type_: str, slug: str, status: str,
         body: str = "Body.", title: str | None = None, nav_order: int | None = None):
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO content (type, title, slug, body_md, status, author_id, nav_order) "
            "VALUES (?, ?, ?, ?, ?, 1, ?)",
            (type_, title or slug.title(), slug, body, status, nav_order),
        )
        conn.commit()
    finally:
        conn.close()


def _all_html(site: Path) -> dict[str, str]:
    return {str(p.relative_to(site)): p.read_text() for p in site.rglob("*.html")}


def test_publish_writes_only_published_pages_and_notes(tmp_path):
    db = _db(tmp_path)
    _add(db, "page", "guide", "published", nav_order=1)
    _add(db, "page", "secret-page", "draft")
    _add(db, "note", "need-blind", "published")
    _add(db, "note", "draft-note", "draft", body="UNPUBLISHED-DRAFT-TEXT")

    site = render_site(tmp_path / "site", db_path=db)

    assert (site / "pages" / "guide.html").exists()
    assert (site / "notes" / "need-blind.html").exists()
    assert not (site / "pages" / "secret-page.html").exists()
    assert not (site / "notes" / "draft-note.html").exists()
    assert not any("UNPUBLISHED-DRAFT-TEXT" in html for html in _all_html(site).values())


def test_publish_regenerates_site_and_removes_unpublished_files(tmp_path):
    db = _db(tmp_path)
    _add(db, "note", "old", "published")
    site = render_site(tmp_path / "site", db_path=db)
    assert (site / "notes" / "old.html").exists()

    conn = get_connection(db)
    try:
        conn.execute("UPDATE content SET status='draft' WHERE slug='old'")
        conn.commit()
    finally:
        conn.close()
    render_site(tmp_path / "site", db_path=db)
    assert not (site / "notes" / "old.html").exists()


def test_exported_html_uses_only_relative_paths(tmp_path):
    db = _db(tmp_path)
    _add(db, "page", "story", "published", nav_order=1)
    _add(db, "note", "need-aware", "published")

    pages = _all_html(render_site(tmp_path / "site", db_path=db))

    assert set(pages) == {"index.html", "notes/index.html", "pages/story.html",
                          "notes/need-aware.html"}
    for name, html in pages.items():
        assert not re.search(r'(href|src|action)="/', html), name


def test_public_nav_is_built_from_published_pages_in_nav_order(tmp_path):
    db = _db(tmp_path)
    _add(db, "page", "work-with-me", "published", title="Work With Me", nav_order=3)
    _add(db, "page", "story", "published", title="Story", nav_order=1)
    _add(db, "page", "hidden", "draft", title="Hidden Draft", nav_order=2)

    site = render_site(tmp_path / "site", db_path=db)

    for name, prefix in [("index.html", ""), ("notes/index.html", "../"),
                         ("pages/story.html", "../")]:
        html = (site / name).read_text()
        nav = re.search(r"<nav[^>]*>(.*?)</nav>", html, re.S).group(1)
        assert f'href="{prefix}pages/story.html"' in nav, name
        assert f'href="{prefix}pages/work-with-me.html"' in nav, name
        assert nav.index("Story") < nav.index("Work With Me"), name
        assert "Hidden Draft" not in nav, name


def test_nav_links_resolve_to_files_that_exist(tmp_path):
    db = _db(tmp_path)
    _add(db, "page", "guide", "published", nav_order=1)
    _add(db, "note", "a-note", "published")
    site = render_site(tmp_path / "site", db_path=db)

    for name, html in _all_html(site).items():
        page_dir = (site / name).parent
        for href in re.findall(r'(?:href|src)="([^"#:]+)"', html):
            assert (page_dir / href).resolve().exists(), f"{name} -> {href}"


def test_notes_appear_in_a_public_listing_and_as_individual_pages(tmp_path):
    db = _db(tmp_path)
    _add(db, "note", "need-blind", "published", title="Need-blind vs need-aware",
         body="The **actual** difference.")
    _add(db, "note", "full-aid", "published", title="What full aid means")

    site = render_site(tmp_path / "site", db_path=db)

    listing = (site / "notes" / "index.html").read_text()
    assert 'href="need-blind.html"' in listing and "Need-blind vs need-aware" in listing
    assert 'href="full-aid.html"' in listing
    note = (site / "notes" / "need-blind.html").read_text()
    assert "<strong>actual</strong>" in note


@pytest.mark.parametrize("type_,path", [("note", "notes/x.html"), ("page", "pages/x.html")])
def test_script_and_onerror_do_not_survive_export(tmp_path, type_, path):
    db = _db(tmp_path)
    _add(db, type_, "x", "published", nav_order=1,
         body='Hi <script>alert(1)</script> <img src="x.png" onerror="alert(2)">')

    html = (render_site(tmp_path / "site", db_path=db) / path).read_text()

    assert "<script>alert(1)" not in html
    assert "onerror" not in html


def test_publish_refuses_a_slug_that_would_escape_site(tmp_path):
    db = _db(tmp_path)
    _add(db, "note", "../../evil", "published")

    with pytest.raises(ValueError, match="slug"):
        render_site(tmp_path / "site", db_path=db)
    assert not (tmp_path / "evil.html").exists()
