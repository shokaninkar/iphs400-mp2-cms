# Tech Spec — inkadmissions CMS

**Status:** T01–T07, #9, T10 (#10, admin styling and a friendly 403 page) and T11 (#11, admin nav, logout button, success messages) implemented. Tagged `mp2-final`.
**Source of truth for requirements:** [spec issue #1](https://github.com/shokaninkar/iphs400-mp2-cms/issues/1). This document is the engineering-facing companion — architecture and data model detail the spec issue deliberately leaves out.

## 1. Overview

A local-only admin console (FastAPI + Jinja2 + SQLite) for **inkadmissions**, Ingkar's real admissions-consulting business. Ingkar (admin) manages the site's static Pages and reviews content; Aigerim, a part-time content assistant (editor), drafts periodic advice posts ("Notes"). Published content is rendered to static HTML (`cms publish`) and deployed to GitHub Pages — the admin console itself never runs on the public internet (ADR-001).

Client context, vocabulary, and the decisions behind this design live in [`CONTEXT.md`](../CONTEXT.md) and the [grill transcript](transcripts/iphs400_mp2-cms_chat-session_01_ingkar-shokan_20260929.md).

## 2. Goals / Non-goals

**In scope (MVP, per the 7 required capabilities):**
- Login/logout with hashed passwords (T01)
- Two roles, admin and editor, enforced at the route level (T02)
- Notes: editor-authored drafts, admin-reviewed publish (T03)
- Pages: admin-only, appear in public nav (T04)
- Admin console UX: dashboard, filterable list, Markdown preview (T05)
- User management: admin creates users, changes roles, deactivates users (T06)
- Public site + `cms publish`: only published content, relative paths (T07)

**Explicitly out of scope** (see `CONTEXT.md` → Resolved):
- Bilingual (EN/RU) content — English only
- Migrating or replacing the live `inkadmissions-site` static repo
- Telegram-bot CTA / lead-magnet delivery
- Categories/tags, comments, media uploads, scheduled publishing, search, revision history (rubric stretch goals, not MVP)

## 3. Architecture

```
┌─────────────────────────── your laptop (private) ───────────────────────────┐
│  FastAPI app (app/main.py)                                                  │
│    ├─ app/routes/auth.py    — /login, /logout                               │
│    ├─ app/routes/notes.py   — /admin/notes/*                                │
│    ├─ app/routes/pages.py   — /admin/pages/*        (T04)                   │
│    ├─ app/routes/users.py   — /admin/users/*        (T06)                   │
│    └─ app/deps.py           — get_db, get_session, require_role, verify_csrf│
│                                     │                                        │
│                                     ▼                                        │
│                            SQLite (cms.db, gitignored)                      │
│                            users, content                                   │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                    │ cms publish (T07)
                                    ▼
                          site/ (static HTML, relative paths)
                                    │ cms deploy (ghp-import)
                                    ▼
                          gh-pages branch → GitHub Pages
```

No ORM (ADR-002): raw `sqlite3`, `conn.row_factory = sqlite3.Row`. One shared `Jinja2Templates` instance in `app/templating.py` (T04), with the `markdown` filter registered once; every route module imports it.

## 4. Data model

```sql
users (
    id, email UNIQUE, password_hash,           -- argon2 (D1)
    role CHECK IN ('admin','editor'),
    is_active DEFAULT 1,
    created_at
)

content (
    id, type CHECK IN ('page','note'), title, slug,
    body_md, status CHECK IN ('draft','published') DEFAULT 'draft',
    author_id REFERENCES users(id), nav_order,   -- nav_order: pages only (T04)
    created_at, updated_at,
    UNIQUE(type, slug)
)
```

One table for both Pages and Notes, discriminated by `type`. Pages additionally use `nav_order` for public navigation (T04); Notes ignore it.

## 5. Roles & permissions matrix

| Action | Admin | Editor |
|---|---|---|
| Log in / out | ✅ | ✅ |
| View own Notes | ✅ | ✅ |
| View all Notes | ✅ | ❌ (403) |
| Create/edit own Note (draft) | ✅ | ✅ |
| Edit another user's Note | ✅ | ❌ (403) |
| Publish/unpublish/delete a Note | ✅ | ❌ (403) |
| Create/edit/publish/delete a Page | ✅ | ❌ (403) |
| Create users, change role, deactivate | ✅ | ❌ (403) |
| Change own role or deactivate self | ❌ (400, prevents admin lockout) | ❌ (403) |
| Anonymous → any `/admin/*` route | redirected to `/login` | redirected to `/login` |

Enforced by `app/deps.py::require_role(*roles)`, applied per-route, not hidden in templates — two distinct failure modes: **no session → 303 to `/login`**, **wrong role → 403**.

## 6. Routes (current + planned)

| Method | Path | Role | Ticket | Status |
|---|---|---|---|---|
| GET/POST | `/login` | anonymous | T01 | ✅ |
| POST | `/logout` (CSRF token required since T11) | any | T01, T11 | ✅ |
| GET | `/admin` | admin, editor | T02 | ✅ |
| GET | `/admin/notes` | admin, editor | T03 | ✅ |
| GET | `/admin/notes/new` | admin, editor | T03 | ✅ |
| POST | `/admin/notes` | admin, editor | T03 | ✅ |
| GET | `/admin/notes/{id}/edit` | owner or admin | T03 | ✅ |
| POST | `/admin/notes/{id}` | owner or admin | T03 | ✅ |
| POST | `/admin/notes/{id}/publish` | admin | T03 | ✅ |
| POST | `/admin/notes/{id}/unpublish` | admin | T03 | ✅ |
| POST | `/admin/notes/{id}/delete` | admin | T03 | ✅ |
| GET/POST | `/admin/pages*` | admin | T04 | ✅ |
| GET | `/pages/{slug}.html` (published only, else 404) | anonymous | T04 | ✅ |
| GET | `/notes/index.html`, `/notes/{slug}.html` (live preview of the export) | anonymous | T07 | ✅ |
| GET | `/admin` (dashboard counts), `/admin/content?type=&status=` (filterable list) | admin, editor | T05 | ✅ |
| POST | `/admin/preview` (live Markdown preview, sanitized) | admin, editor | T05 | ✅ |
| — | any 403 renders `admin/forbidden.html` with a link back to the dashboard | — | T10 | ✅ |
| GET/POST | `/admin/users*` | admin | T06 | ✅ |
| — | `cms publish` CLI → `site/` (index, `pages/`, `notes/`, style.css) | — | T07 | ✅ |

## 7. Security

- **D1 Password hashing:** argon2 (`app/security.py`), never logged or stored plain.
- **D2 CSRF:** every state-changing form beyond `/login` requires a token minted at login and carried in the signed session cookie (`app/deps.py::verify_csrf`). `/login` is the one documented exception — no prior session exists for a forged request to ride on, and `tests/conftest.py`'s `client_as` fixture (used by every role test) depends on token-free login.
- **D3 Access control:** `require_role` dependency, tested per route (T02–T06 tests); a wrong role gets 403, anonymous gets 303 to `/login`.
- **D4 Sanitized Markdown:** `nh3.clean()` default allowlist strips `<script>` and `on*` attributes before any Note/Page body reaches a template (`app/markdown.py`). Verified directly against the library before writing app code.
- **D5 No secrets committed:** `cms.db` and `.env` gitignored; verified via `check_submission.py`'s history grep.

## 8. Testing strategy

Route-level tests via `fastapi.testclient.TestClient`, not internal-function mocking — matches what the rubric's D3/E2 actually check. Every capability gets: a happy path, an access-control case (wrong role / anonymous), and a persistence case (fresh DB connection stands in for a server restart). Current: 108/108 passing (`tests/test_t00.py`, `test_auth.py`, `test_roles.py`, `test_notes.py`, `test_pages.py`, `test_dashboard.py`, `test_users.py`, `test_publish.py`, `test_admin_ui.py`, `test_admin_nav.py`, `test_ctx_guard.py`, `test_usage_report.py`).

## 9. Open questions / risks

- ~~Per-module `Jinja2Templates` instances~~ — resolved in T04 (`app/templating.py`); the last separate `Environment`, in `app/publish.py`, was removed in T07, so the export uses the same sanitizing `markdown` filter as the admin.
- ~~Published-content queries inline in `app/main.py`; no site-wide nav~~ — resolved in T07: `app/content.py` owns the published Pages/Notes queries for both `cms publish` and the live preview, and `base.html` renders nav from published Pages.
- Slugs are file names in `site/`, so T07 restricts them to `[a-z0-9]` with single hyphens (`app/content.py::SAFE_SLUG`), checked on the Note/Page forms (422) and again at export.
- ~~Duplicate slug on create/edit (Notes and Pages) raises an unhandled `sqlite3.IntegrityError` (500)~~ — resolved in T09 (#9): the form re-renders with a 409 and an error; other integrity errors still propagate.
- ~~The `Notes` list shows a fully-rendered body inline; T05's "Markdown preview" may want a distinct preview~~ — resolved in T05: the Note/Page editor has a preview pane, server-rendered first and refreshed as you type via `/admin/preview`.
- Session/usage-ledger hooks (`decide()`, `spend()`) are implemented and tested, but only fire for real when Claude Code's project root is this repo — see `docs/process/compaction-log.md` for the note on why T01–T03's sessions didn't populate real ledger data.
