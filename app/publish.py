"""Render the public site into site/ as plain HTML (T07, #8).

Two rules the rubric checks:

  1. Only PUBLISHED content is written here. A draft that reaches site/ is a bug.
  2. Every href and src is RELATIVE ("style.css", "notes/x.html"), never
     root-absolute ("/style.css"), because Pages serves this from a subfolder.

Layout written:

    index.html            home: site nav + latest Notes
    pages/<slug>.html     one per published Page (also linked from the nav)
    notes/index.html      public listing of published Notes
    notes/<slug>.html     one per published Note
    style.css
"""
from __future__ import annotations

import shutil
from pathlib import Path

from app import settings
from app.content import check_slug, nav_items, published_notes, published_pages
from app.db import get_connection, init_db
from app.templating import templates

CSS = """:root { color-scheme: light dark; --accent: #2f5bd3; }
@media (prefers-color-scheme: dark) { :root { --accent: #8fb0ff; } }
* { box-sizing: border-box; }
body { font: 17px/1.6 system-ui, sans-serif; margin: 0 auto; max-width: 42rem; padding: 1rem; overflow-wrap: anywhere; }
header { display: flex; flex-wrap: wrap; align-items: baseline; gap: .5rem 1.25rem; padding-bottom: .75rem; border-bottom: 1px solid color-mix(in srgb, currentColor 20%, transparent); }
header .brand { font-weight: 700; font-size: 1.15rem; text-decoration: none; color: inherit; }
nav { display: flex; flex-wrap: wrap; gap: .25rem 1rem; }
nav a, a { color: var(--accent); }
main { margin-block: 2rem; }
img { max-width: 100%; height: auto; }
pre { overflow-x: auto; }
ul.notes { padding-left: 1.1rem; }
ul.notes small { opacity: .7; margin-left: .4rem; }
footer { opacity: .7; }
"""


def render_site(out: Path | None = None, db_path: Path | None = None) -> Path:
    out = out or settings.SITE
    init_db(db_path)  # a fresh clone has no tables yet; publish an empty site
    conn = get_connection(db_path)
    try:
        pages = published_pages(conn)
        notes = published_notes(conn)
    finally:
        conn.close()
    # Validate every slug before deleting the old site, so a bad slug leaves
    # the previous export intact instead of half-written.
    for row in [*pages, *notes]:
        check_slug(row)

    if out.exists():
        shutil.rmtree(out)
    (out / "pages").mkdir(parents=True)
    (out / "notes").mkdir()

    env = templates.env  # shared Environment: carries the sanitizing `markdown` filter
    common = {"site_title": settings.SITE_TITLE, "nav": nav_items(pages)}

    def write(rel: str, template: str, **ctx) -> None:
        root = "../" * rel.count("/")
        html = env.get_template(template).render(**common, root=root, **ctx)
        (out / rel).write_text(html, encoding="utf-8")

    (out / "style.css").write_text(CSS, encoding="utf-8")
    write("index.html", "public/home.html", title=settings.SITE_TITLE, notes=notes)
    write("notes/index.html", "public/notes_index.html", title="Notes", notes=notes)
    for page in pages:
        write(f"pages/{page['slug']}.html", "public/page.html",
              title=page["title"], page=page)
    for note in notes:
        write(f"notes/{note['slug']}.html", "public/note.html",
              title=note["title"], note=note)
    return out
