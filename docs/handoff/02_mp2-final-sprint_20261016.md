# Handoff 02: MP2 final sprint (Fri Oct 16, 2026)

Written 04:15 ET. Hard stop: **grace deadline 2:40 pm ET today** (tag `mp2-final`
pushed + Stage 2 email sent). Aim to tag by 2:00 pm.

## State at handoff

- T01–T04 done. T04 (`4ee81e1`) is committed but **not pushed**; #5 closes on push.
- `uv run pytest -q`: 47 passed. Checker: 16/22.
- No graded feedback report from round one, so the rubric is the only guide.
- MP2plus is deferred to after `mp2-final` (due Tue Oct 20).

## Order: one fresh session per ticket

Each session: `echo <id> > .claude/state/phase`, `/clear`, `/implement #N`,
`/code-review`, post the findings and how each was resolved as a comment on
the issue, then commit `T0N: ... Closes #N`. Keep sessions short.

| # | Session | Issue | Notes |
|---|---|---|---|
| 1 | Duplicate slug | #9 | Catch `sqlite3.IntegrityError` in create/update for Notes and Pages; re-render the form with an error. One test per type. |
| 2 | T07 public site & publish | #8 | Unblocks the live URL. Also resolve the two T04 deferrals in tech-spec §9: `app/publish.py` needs the shared `markdown` filter (use `app/templating.py`), and the published-content queries move out of `main.py`. Then enable GitHub Pages and put the real URL in the README. |
| 3 | T06 user management | #7 | Needed for the `users` screenshots. Deactivated users must be refused at login. |
| 4 | T05 admin console UX | #6 | Needed for the `dashboard` screenshots. **Also fix the root-absolute links** in `templates/admin/notes_list.html` and `templates/admin/pages_list.html` (checker FAIL: `href="/admin/..."`, `action="/admin/..."`); these lists are what T05 rebuilds anyway. |

## Checker failures and who owns them

| Check | Owner |
|---|---|
| no root-absolute paths in HTML | T05 session |
| 12 screenshots | after T05: `docs/screenshots/{login,dashboard,content-list,editor,users,editor-denied}-{1280,390}.png` |
| README run-locally section | any session after T07; must work on a clean clone |
| AI Use Statement rewritten | **Ingkar writes it**: 2 real prompts quoted, 1 real model failure, models + skills, Backends table |
| report named correctly | **Ingkar writes it**: `docs/iphs400_mp2-web-cms_report_ingkar-shokan_20261016.md`, 1–2 pages, the four questions |
| tag `mp2-final` | last step |

Also required but not checked: `notes/client-brief.md` (Ingkar writes).

## Do not commit

- Transcripts **03–07** (`docs/transcripts/*_your-name_*`). Those sessions were
  career/portfolio work, not the CMS, and contain personal contact details and
  job applications. The repo is public. Only sessions 01 and 02 belong here.
- This sprint's planning session also covered portfolio work; trim it to the
  CMS part before saving it as a transcript.
- `cms.db`, `.env` (already ignored; the checker confirms).

## Final steps (by 2:00 pm)

1. `uv run pytest -q` and `uv run python scripts/check_submission.py --stage 2`, both green.
2. Check the live Pages URL loads over HTTPS with no broken links, and at 390 px.
3. `git push`, then `git tag mp2-final && git push origin mp2-final`.
4. Email Prof. Chun, subject `IPHS400 MP2 Stage 2 - Ingkar Shokan`: repo URL,
   Pages URL, tag name, report attached.
