#!/usr/bin/env python3
"""Create demo data so a grader (and you) can use the CMS immediately.

    cp .env.example .env              # once; app/settings.py reads it
    uv run python scripts/seed_demo.py
    uv run cms publish                # site/ now has the published content

Creates the admin (Ingkar) and the editor (Aigerim) from CONTEXT.md, the three
Pages, and three Notes: two published, one editor draft that must never reach
site/. Content is inkadmissions' own copy, condensed from the live
inkadmissions-site (grill session 01: "real facts and voice, not Lorem Ipsum").

Idempotent: re-running skips anything that already exists (UNIQUE(type, slug)).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import settings  # noqa: E402  (loads .env)
from app.db import get_connection, init_db, seed_user  # noqa: E402

ADMIN_EMAIL = "admin@example.test"
EDITOR_EMAIL = "editor@example.test"

PAGES = [
    ("story", "My Story", 1, """\
I'm Ingkar Shokan, from Almaty, Kazakhstan. I got full financial aid at a US
college as an international student, and this is what that process actually
looked like.

International students aren't eligible for US federal aid, so any "full aid" has
to come from the colleges themselves.

- **Knox College** offered me a Presidential Scholarship worth $43,000 a year for
  four years.
- **Kenyon College** admitted me with full financial aid. Kenyon meets full
  demonstrated need for every student it admits, international or not.

I chose Kenyon: it covered my full need, and its science and statistics programs
fit what I wanted to study.

Full aid for international students is real and more available than most people
assume. Almost nobody explains, step by step, how to find and win it. That's why
I started inkadmissions.
"""),
    ("guide", "The Guide", 2, """\
"Full aid" is a bigger category than the handful of famous need-blind schools
everyone applies to.

## 1. Know the three categories of aid

- **Need-blind:** admission without considering ability to pay. A short, very
  selective list.
- **Need-aware, full need met:** ability to pay may count in admissions, but
  admitted students get their full demonstrated need covered. Kenyon is one.
- **Merit scholarships:** awarded for achievement, independent of need. Knox's
  Presidential Scholarship is one.

## 2. Build your list across all three

Applying only to the famous need-blind schools is the most common mistake.

## 3. Track two sets of deadlines

Financial aid deadlines are often separate from admissions deadlines.

Aid policies change every year. Always confirm a school's current policy with its
financial aid office.
"""),
    ("work-with-me", "Work With Me", 3, """\
I work directly with students from Central Asia to build a school list,
strengthen applications, and navigate financial aid as an international
applicant.

## Client results

- Bryn Mawr College: full-ride offer
- Georgetown University in Qatar: full-ride offer
- USC: acceptance

## What I help with

- A balanced school list across need-blind, need-aware and merit categories
- Essays and applications that stand out for aid, not just admission
- International financial aid forms and deadlines
- Interview preparation

Contact details are coming soon.
"""),
]

# (slug, title, author, status, body)
NOTES = [
    ("need-blind-vs-need-aware", "Need-blind vs. need-aware: what's the actual difference",
     ADMIN_EMAIL, "published", """\
**Need-blind** schools decide admission without looking at whether you can pay.
For international students that list is very short and very selective.

**Need-aware** schools may consider ability to pay. Some of them still meet full
demonstrated need for every student they admit. Kenyon is one.

The second list is much longer and much less competitive, and most students never
hear about it.
"""),
    ("net-price-calculator-first", "Run the net price calculator before you apply",
     ADMIN_EMAIL, "published", """\
Not using a school's net price calculator is one of the most common mistakes I
see.

Run it for every school on your list *before* you apply, so you know which ones
are realistic on cost, not just on admission.
"""),
    ("aid-deadlines-are-separate", "Aid deadlines are not admissions deadlines",
     EDITOR_EMAIL, "draft", """\
Draft for Ingkar's review: financial aid forms often have their own deadlines,
separate from the application deadline. Track both for every school.
"""),
]


def main() -> int:
    admin_pw = settings.env("CMS_ADMIN_PASSWORD")
    editor_pw = settings.env("CMS_EDITOR_PASSWORD")
    if not admin_pw or not editor_pw:
        print("Set CMS_ADMIN_PASSWORD and CMS_EDITOR_PASSWORD in .env "
              "(cp .env.example .env).")
        return 1

    init_db()
    conn = get_connection()
    try:
        seed_user(conn, ADMIN_EMAIL, admin_pw, "admin")
        seed_user(conn, EDITOR_EMAIL, editor_pw, "editor")
        ids = {r["email"]: r["id"] for r in conn.execute("SELECT id, email FROM users")}

        for slug, title, order, body in PAGES:
            conn.execute(
                "INSERT OR IGNORE INTO content (type, title, slug, body_md, status, "
                "author_id, nav_order) VALUES ('page', ?, ?, ?, 'published', ?, ?)",
                (title, slug, body, ids[ADMIN_EMAIL], order),
            )
        for slug, title, author, status, body in NOTES:
            conn.execute(
                "INSERT OR IGNORE INTO content (type, title, slug, body_md, status, "
                "author_id) VALUES ('note', ?, ?, ?, ?, ?)",
                (title, slug, body, status, ids[author]),
            )
        conn.commit()
        counts = conn.execute(
            "SELECT type, status, COUNT(*) AS n FROM content GROUP BY type, status"
        ).fetchall()
    finally:
        conn.close()

    print(f"Seeded {settings.DATABASE_PATH}")
    print(f"  admin:  {ADMIN_EMAIL}   editor: {EDITOR_EMAIL}  (passwords from .env)")
    for row in counts:
        print(f"  {row['type']:5} {row['status']:9} {row['n']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
