# IPHS 400 MP2 — T09 duplicate slug, session 04

**Student:** Ingkar Shokan
**Date:** 2026-10-16
**Session id:** `7ff170a2` (matches `notes/usage-ledger.csv`)
**Ticket:** T09 (#9). Fresh session (`/clear`) from the sprint handoff.

_Converted from the Claude Code session log. Tool calls are shown as one-line summaries; tool output, subagent transcripts and system/hook context are omitted._

**Ingkar:**

`/clear` echo T09 > .claude/state/phase
Read docs/handoff/02_mp2-final-sprint_20261016.md, then /implement #9

**Ingkar:**

- notes/client-brief.md
- the AI Use Statement in the README
- the report, docs/iphs400_mp2-web-cms_report_ingkar-shokan_20261016.md

**Claude:**

> 🔧 **Bash** — Read handoff, phase file, ticket #9

**Claude:**

> 🔧 **Bash** — Read implement skill, glossary, and route files

**Claude:**

> 🔧 **Bash** — Read form templates and tests

**Claude:**

> 🔧 **Bash** — Read notes test helpers and rest of pages tests

**Claude:**

Writing the failing tests first (one per content type, each covering create and edit).

**Claude:**

> 🔧 **Bash** — Add duplicate-slug tests and run them (expect red)

**Claude:**

> 🔧 **Bash** — Confirm failure reason is the IntegrityError

**Claude:**

Red for the right reason. Now the fix: catch the error, roll back, and re-render the form with the submitted values.

**Claude:**

> 🔧 **Bash** — Let form templates show an error and resubmitted values

**Claude:**

Now the routes.

**Claude:**

> 🔧 **Bash** — Catch IntegrityError in Note/Page create and update; run tests

**Claude:**

49 passed. Checking for a configured typechecker/linter, then running `/code-review` as the workflow requires.

**Claude:**

> 🔧 **Bash** — Check for lint/typecheck config and run ruff

**Claude:**

> 🔧 **Skill** — code-review

**Claude:**

> 🔧 **Bash** — Find standards docs and confirm diff is non-empty

**Claude:**

`docs/agents/issue-tracker.md` is missing (the skill suggests `/setup-matt-pocock-skills`), but I already have issue #9 from `gh`, so I'll go ahead with it. Starting both review axes in parallel.

**Claude:**

> 🔧 **Agent** — Standards review for T09

**Claude:**

> 🔧 **Agent** — Spec review for T09

**Claude:**

I've fixed T09 (#9) but not committed it yet: the code review is still running. Duplicate slugs no longer cause a 500 for Notes or Pages, on both create and edit.

- **Routes** (`app/routes/notes.py`, `app/routes/pages.py`): the create and update routes now catch the duplicate-slug database error and roll back. They then show the form again with status 409, a message ("Another Note/Page already uses that slug. Choose a different one.") and the user's entered values. On edit, the form still posts to that same item.
- **Templates** (`templates/admin/note_form.html`, `templates/admin/page_form.html`): they show the error and refill the fields from what was submitted.
- **Tests:** one per content type, each covering create and edit, and checking that nothing in the database changed. Both failed with the original 500 error before the fix. The full suite now passes (49 tests).

There was no typecheck or lint run: the project has neither configured, and `ruff` isn't installed. I also kept the existing `/admin/...` links in the form templates, since the T05 session is assigned those.

The review's Standards and Spec checks are running in parallel. When they finish I'll fix anything they find, post the findings and how each was resolved as a comment on #9, and commit as `T09: ... Closes #9`. The skill wanted a setup file (`docs/agents/issue-tracker.md`) that doesn't exist, so I used issue #9 from `gh` instead. You can add the file later with `/setup-matt-pocock-skills`.

Your message ended with three files: `notes/client-brief.md`, the AI Use Statement in the README, and the report. The handoff says you're writing those yourself, so I'm leaving all three alone in this session. Tell me if you meant something else.

**Claude:**

> 🔧 **Bash** — Read tech-spec known-issues section

**Claude:**

The Standards review is back. I'm waiting for the Spec review before making any changes, so I can apply all fixes together.

**Claude:**

Both reviews are in. I'll make these fixes: narrow the catch so only the slug constraint counts (both reviewers flagged it), update the stale line in tech-spec, rename `v`, and add CSRF assertions to the tests. First I'm checking the schema and whether there's already a test that re-saves an unchanged slug.

**Claude:**

> 🔧 **Bash** — Inspect schema, existing edit test, and Python sqlite features

**Claude:**

Existing tests already re-save a Note and a Page with their own slug and expect a 303, so that gap is covered. Applying the fixes:

**Claude:**

> 🔧 **Bash** — Narrow catch, rename template var, add CSRF asserts, update tech-spec; run suite

**Claude:**

> 🔧 **Bash** — Check backend URL and pending changes

**Claude:**

> 🔧 **Bash** — Post code-review findings and resolutions on issue #9

**Claude:**

> 🔧 **Bash** — Commit T09 changes

**Claude:**

T09 is committed as `7b1fbd3` but not pushed. When you push, #9 closes, and so does #5 (T04 is still unpushed too). The full suite passes (49 tests).

**The fix:** if a Note or Page is created or edited with a slug that already exists, the form comes back with status 409. It shows an error and keeps what you typed, and nothing in the database changes. Any other database constraint error still fails loudly instead of being shown as "slug already used". There's one test per content type, each covering both create and edit.

**Code review:** the findings and how each was handled are posted on #9 ([comment](https://github.com/shokaninkar/iphs400-mp2-cms/issues/9#issuecomment-6211164190)).
- **Fixed:**
  - The error check was too broad; it now matches only the duplicate-slug case.
  - The known-issue line in `docs/tech-spec.md` was out of date and is updated.
  - A template variable named `v` is renamed to `values`.
  - The tests now also check that the CSRF token is still in the re-shown form.
- **Kept:** the 409 status, which the ticket didn't specify but is the standard code for a conflict like this.
- **Deferred:** small duplicated code between the Notes and Pages routes and tests. It copies a pattern that was already there, and cleaning it up is beyond this ticket on deadline day.

The commit message has `Closes #9` just above the required `Co-Authored-By` line, not as the very last line as `CLAUDE.md` asks. GitHub still closes the issue this way.

I didn't commit `notes/usage-ledger.csv`, the handoff file, or any transcripts. The ledger and handoff were already changed or untracked when this session started.

Next in the handoff is T07 (#8). To push now:
```
git push
```
