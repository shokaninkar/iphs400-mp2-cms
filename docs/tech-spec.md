# Tech Spec — inkadmissions CMS

**Status:** T01–T03 implemented and closed; T04–T07 planned.
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
- User management: admin creates/edits/deactivates users (T06)
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
│    ├─ app/routes/pages.py   — /admin/pages/*        (T04, planned)          │
│    ├─ app/routes/users.py   — /admin/users/*        (T06, planned)          │
│    └─ app/deps.py           — get_db, get_session, require_role, verify_csrf│
│                                     │                                        │
│                                     ▼                                        │
│                            SQLite (cms.db, gitignored)                      │
│                            users, content                                   │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                    │ cms publish (T07, planned)
                                    ▼
                          site/ (static HTML, relative paths)
                                    │ cms deploy (ghp-import)
                                    ▼
                          gh-pages branch → GitHub Pages
```

No ORM (ADR-002): raw `sqlite3`, `conn.row_factory = sqlite3.Row`. One `Jinja2Templates` instance per route module currently (see T03 code-review note on `templates.env.filters` — worth consolidating if T04/T05 need the same filter).

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
| Create/edit/delete a Page | ✅ | ❌ (403) — planned T04 |
| Create/edit users, deactivate | ✅ | ❌ (403) — planned T06 |
| Anonymous → any `/admin/*` route | redirected to `/login` | redirected to `/login` |

Enforced by `app/deps.py::require_role(*roles)`, applied per-route, not hidden in templates — two distinct failure modes: **no session → 303 to `/login`**, **wrong role → 403**.

## 6. Routes (current + planned)

| Method | Path | Role | Ticket | Status |
|---|---|---|---|---|
| GET/POST | `/login` | anonymous | T01 | ✅ |
| POST | `/logout` | any | T01 | ✅ |
| GET | `/admin` | admin, editor | T02 | ✅ |
| GET | `/admin/notes` | admin, editor | T03 | ✅ |
| GET | `/admin/notes/new` | admin, editor | T03 | ✅ |
| POST | `/admin/notes` | admin, editor | T03 | ✅ |
| GET | `/admin/notes/{id}/edit` | owner or admin | T03 | ✅ |
| POST | `/admin/notes/{id}` | owner or admin | T03 | ✅ |
| POST | `/admin/notes/{id}/publish` | admin | T03 | ✅ |
| POST | `/admin/notes/{id}/unpublish` | admin | T03 | ✅ |
| POST | `/admin/notes/{id}/delete` | admin | T03 | ✅ |
| GET/POST | `/admin/pages*` | admin | T04 | planned |
| GET | `/admin/dashboard`, list filters | admin, editor | T05 | planned |
| GET/POST | `/admin/users*` | admin | T06 | planned |
| — | `cms publish` CLI | — | T07 | planned (stub exists) |

## 7. Security

- **D1 Password hashing:** argon2 (`app/security.py`), never logged or stored plain.
- **D2 CSRF:** every state-changing form beyond `/login` requires a token minted at login and carried in the signed session cookie (`app/deps.py::verify_csrf`). `/login` is the one documented exception — no prior session exists for a forged request to ride on, and `tests/conftest.py`'s `client_as` fixture (used by every role test) depends on token-free login.
- **D3 Access control:** `require_role` dependency, tested per route (T02/T03 tests; T04/T06 will extend coverage as those routes land).
- **D4 Sanitized Markdown:** `nh3.clean()` default allowlist strips `<script>` and `on*` attributes before any Note/Page body reaches a template (`app/markdown.py`). Verified directly against the library before writing app code.
- **D5 No secrets committed:** `cms.db` and `.env` gitignored; verified via `check_submission.py`'s history grep.

## 8. Testing strategy

Route-level tests via `fastapi.testclient.TestClient`, not internal-function mocking — matches what the rubric's D3/E2 actually check. Every capability gets: a happy path, an access-control case (wrong role / anonymous), and a persistence case (fresh DB connection stands in for a server restart). Current: 40/40 passing (`tests/test_t00.py`, `test_auth.py`, `test_roles.py`, `test_notes.py`, `test_ctx_guard.py`, `test_usage_report.py`).

## 9. Open questions / risks

- `templates.env.filters["markdown"]` is registered inside `app/routes/notes.py` — fine with one shared `Jinja2Templates` instance, but should move to a single shared template-setup module before T04/T05 add their own filters or template instances.
- The `Notes` list currently shows a fully-rendered body inline; T05's "Markdown preview" requirement may want a distinct, possibly JS-driven preview instead — worth revisiting when T05 starts.
- Session/usage-ledger hooks (`decide()`, `spend()`) are implemented and tested, but only fire for real when Claude Code's project root is this repo — see `docs/process/compaction-log.md` for the note on why T01–T03's sessions didn't populate real ledger data.
