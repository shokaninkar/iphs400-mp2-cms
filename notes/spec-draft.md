## Problem Statement

inkadmissions (Ingkar's admissions-consulting business) currently runs as a static,
hand-edited 3-page site. Publishing anything new — a Note (an admissions-tips post), or an
edit to a Page — means editing HTML by hand and committing. There's no way for a second
person (Aigerim, a part-time content assistant) to draft content without either learning
git or getting direct file access, and no safe way to let her contribute without also
giving her the ability to change the Story/Guide/Work With Me pages or publish unreviewed
material under the inkadmissions name.

## Solution

A local admin console (FastAPI + Jinja + SQLite) where:
- Ingkar (admin) logs in and can manage Pages, Notes, and users.
- Aigerim (editor) logs in and can draft and edit her own Notes, but cannot touch Pages,
  cannot publish, and cannot manage users.
- `cms publish` renders all published content to static HTML in `site/`, deployed to
  GitHub Pages — the admin console itself never goes on the public internet (ADR-001).

This runs in parallel to the existing `inkadmissions-site` repo for MP2; it does not
replace it.

## User Stories

1. As admin, I want to log in with a hashed password, so that my account can't be
   compromised by reading the database.
2. As admin or editor, I want to log out, so that a shared/borrowed machine doesn't stay
   signed in.
3. As anyone submitting a login form, I want a wrong password rejected with a clear
   message, so that I know to retry rather than assume the system is broken.
4. As an anonymous visitor, I want to be redirected to login when I hit an admin route, so
   that the admin console isn't browsable without credentials.
5. As editor, I want to be blocked (403) from every Pages route and every publish action,
   so that the permission boundary is enforced, not just hidden in the UI.
6. As admin, I want to create, edit, and delete a Page (Story/Guide/Work With Me), with
   title, slug, Markdown body, status, and timestamps, so that I can update core site copy
   without touching HTML.
7. As admin, I want a published Page to appear in the public site's navigation, so that
   visitors can reach it.
8. As editor, I want to create a new Note (title, slug, Markdown body) and save it as a
   draft, so that I can write without risking it going live by accident.
9. As editor, I want to edit my own draft Notes, so that I can revise before it's reviewed.
10. As admin, I want to review a draft Note and publish it, so that only reviewed material
    reaches the public site under the inkadmissions name.
11. As admin, I want to unpublish or delete any Note or Page, so that I can correct mistakes
    or retire stale content.
12. As admin or editor, I want the dashboard to show counts of Pages/Notes by status, so
    that I can see what needs review at a glance.
13. As admin or editor, I want the content list filterable by status (draft/published) and
    type (Page/Note), so that I can find something quickly as the content grows.
14. As admin or editor, I want a Markdown preview in the editor, so that I can see
    formatting before saving.
15. As admin, I want to create a new user (with a role), change an existing user's role, and
    deactivate a user, so that I can manage who has access without editing the database
    directly.
16. As a deactivated user, I want my login attempt refused, so that removing access is
    actually effective.
17. As a visitor to the public site, I want to see only published Pages and Notes, so that
    drafts never leak.
18. As a visitor, I want any Markdown-authored content sanitized (no `<script>`, no
    `onerror=` handlers), so that a compromised or careless editor account can't be used for
    XSS against site visitors.
19. As Ingkar running `cms publish`, I want the exported `site/` to use only relative paths,
    so that it works correctly when served from a GitHub Pages project subfolder.
20. As anyone submitting any admin form, I want the POST rejected without a valid CSRF
    token, so that a malicious third-party site can't submit changes on my behalf.

## Implementation Decisions

- **Stack** (fixed by `pyproject.toml`, ADR-002): FastAPI + Jinja2 + raw `sqlite3` (no ORM)
  + `itsdangerous` signed session cookies + `argon2-cffi` password hashing +
  `markdown-it-py` + `nh3` sanitization + `ghp-import` for deploy.
- **Roles**: exactly two, `admin` and `editor`, stored on the `users` table. Permission
  checks are a FastAPI dependency (`require_role("admin")` / `require_role("admin",
  "editor")`), not template-level hiding — hiding a button is not access control.
- **Content model**: one `content` table for both Pages and Notes, distinguished by a
  `type` column (`page` | `note`), each with `title`, `slug`, `body_md`, `status`
  (`draft`|`published`), `author_id`, `created_at`, `updated_at`. Pages additionally carry a
  `nav_order` for public navigation; Notes do not appear in nav, only in their own list.
- **Seams for testing**: prefer one seam per capability — a route module
  (`app/routes/auth.py`, `app/routes/pages.py`, `app/routes/notes.py`,
  `app/routes/users.py`) tested through FastAPI's `TestClient`/`httpx`, hitting real routes
  against a temp SQLite DB rather than mocking the DB layer. This matches `tests/conftest.py`
  patterns already in the skeleton.
- **Sessions**: signed cookie via `itsdangerous`, carrying user id + role; no server-side
  session store needed for this scale.
- **CSRF**: a per-session token embedded as a hidden field in every state-changing form,
  checked in the dependency layer before the route body runs.
- **Publish**: `cms publish` (already stubbed in `app/publish.py`) queries only
  `status='published'` rows, renders Pages into nav-linked HTML and Notes into a `/notes/`
  listing + individual pages, using `nh3`-sanitized, `markdown-it-py`-rendered HTML, with
  every internal link relative to `site/`.

## Testing Decisions

- Test through the route layer (`TestClient`), not by calling internal functions directly —
  this is what the rubric's D3 (access-control tests) and E2 (tests trace to acceptance
  criteria) actually check.
- Every capability needs at least: a happy-path test, an access-control test (wrong role /
  anonymous), and — where relevant — a persistence test (data survives a fresh DB
  connection, standing in for "survives a server restart" per C3/C4).
- Follow `tests/conftest.py`'s existing `client_as("editor")` helper pattern for
  role-scoped test clients.
- XSS test (D4): save a Note/Page body containing `<script>` and an `onerror=` attribute;
  assert neither appears unescaped in the admin preview or the published export.

## Out of Scope

- Bilingual (EN/RU) content — English only for MVP (Q3 in the grill transcript).
- Migrating or cutting over the live `inkadmissions-site` repo — this CMS is a parallel,
  separate deployment (Q4).
- The Telegram-bot CTA / lead-magnet delivery — not ready on the live site either; not part
  of this CMS's scope.
- Categories/tags on Notes, comments, media uploads, scheduled publishing, search, revision
  history — all rubric stretch goals, not MVP.
- Rate-limiting or a hardened production deploy of the admin console (ADR-001: it never
  goes on the public internet for this project).

## Further Notes

Client and role decisions came from `/grill-with-docs` session 01
(`docs/transcripts/iphs400_mp2-cms_chat-session_01_ingkar-shokan_20260929.md`). Notably,
"Posts" was deliberately resolved as "Notes" (admissions tips/blog), overriding the
recommended default of client-results spotlights — client-results content stays on the
static Work With Me page instead.
