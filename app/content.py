"""Published-content queries, shared by `cms publish` and the live preview routes.

T07 owns these (tech-spec §9): the "only published Pages, by nav_order" query
used to live inline in app/main.py. Keeping it here means the exported site and
the preview can't drift apart on what counts as published.
"""
from __future__ import annotations

import re
import sqlite3

# Slugs become file names under site/, so anything outside this set (a "/",
# "..", spaces) could write outside site/ or produce a broken link.
SAFE_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def published_pages(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM content WHERE type='page' AND status='published' "
        "ORDER BY nav_order IS NULL, nav_order, title"
    ).fetchall()


def published_notes(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM content WHERE type='note' AND status='published' "
        "ORDER BY created_at DESC, id DESC"
    ).fetchall()


def published_one(conn: sqlite3.Connection, type_: str, slug: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM content WHERE type=? AND slug=? AND status='published'",
        (type_, slug),
    ).fetchone()


def nav_items(pages: list[sqlite3.Row]) -> list[dict]:
    """Site-wide nav: published Pages in nav_order. Hrefs are relative to the
    site root; templates prefix them with `root` ("" or "../")."""
    return [{"title": p["title"], "href": f"pages/{p['slug']}.html"} for p in pages]


def check_slug(row: sqlite3.Row) -> str:
    slug = row["slug"]
    if not SAFE_SLUG.fullmatch(slug):
        raise ValueError(
            f"Refusing to publish {row['type']} {row['title']!r}: slug {slug!r} must be "
            "lowercase letters, digits and single hyphens (e.g. need-blind-vs-need-aware)."
        )
    return slug
