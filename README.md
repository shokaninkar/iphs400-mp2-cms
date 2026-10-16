# inkadmissions CMS — IPHS 400 Mini-Project #2

A small web CMS for **inkadmissions**, my admissions-consulting business for students
from Central Asia applying to US colleges for full financial aid. A local admin console
(FastAPI + Jinja2 + SQLite) is where content gets written and reviewed; `cms publish`
exports only the published content as static HTML, which GitHub Pages serves. The admin
console never runs on the public internet ([ADR-001](docs/adr/ADR-001-local-admin-static-public.md)).

**Live URL:** https://shokaninkar.github.io/iphs400-mp2-cms/

Built from Prof. Jon Chun's starter template,
[jon-chun/iphs400-mp2-cms-starter](https://github.com/jon-chun/iphs400-mp2-cms-starter)
(T00 skeleton, hooks, checker, exercise scaffolding).

## Run locally

Needs Python 3.12+ and [uv](https://docs.astral.sh/uv/). From a clean clone:

```bash
uv sync --extra dev
cp .env.example .env                 # then change the two demo passwords if you like
uv run python scripts/seed_demo.py   # demo users, 3 Pages, 3 Notes (one draft)
uv run cms serve                     # admin console at http://localhost:8000/admin
uv run pytest -q                     # test suite
```

Log in at http://localhost:8000/login with:

| Role | Email | Password |
|---|---|---|
| Admin (Ingkar) | `admin@example.test` | `CMS_ADMIN_PASSWORD` from `.env` |
| Editor (Aigerim) | `editor@example.test` | `CMS_EDITOR_PASSWORD` from `.env` |

The editor can draft and edit her own Notes only. Pages, publishing and user management
are admin-only, and the server returns 403 if an editor tries them directly.

## Publish

```bash
uv run cms publish     # writes site/ from published Pages and Notes only
uv run cms deploy      # pushes site/ to the gh-pages branch
```

`site/` is generated and gitignored. Every link in it is relative, so it works under the
`/iphs400-mp2-cms/` project path. Preview it with `python3 -m http.server -d site 8001`.

## Content model

Vocabulary is defined in [CONTEXT.md](CONTEXT.md).

- **Pages**: My Story, The Guide, Work With Me. Admin-only; published Pages make up the
  public navigation.
- **Notes**: inkadmissions' name for posts (dated admissions tips). Editors draft them;
  only the admin publishes.

## Where things are

```text
app/            FastAPI app: routes/, publish.py (the export), content.py (published-content queries)
templates/      admin/ and public/ Jinja templates
tests/          pytest suite, one file per ticket
scripts/        seed_demo.py, check_submission.py, usage_report.py
docs/           tech-spec, ADRs, handoffs, transcripts, screenshots, report
notes/          field notes, client brief, token budget plan, usage ledger
```

Spec: issue #1. Tickets: issues #2–#9, each closed by a `TNN: ... Closes #N` commit after
its `/code-review` findings were posted on the issue.

## Generative AI Use Statement

*(Required. Replace this section: name the models and skills you used, quote two
prompts you really sent, describe one real model failure, and include a
"Backends used" table if you ever switched providers.)*

<!--
Facts you can use (from the repo; write the statement yourself):
- Model: Claude Opus 5.5 in Claude Code; every ledger row is provider "anthropic" (notes/usage-ledger.csv).
- Skills used: /grill-with-docs, /to-spec, /to-tickets, /implement, /tdd, /code-review, /handoff.
- Your grill override: "Posts" = Notes (admissions tips), not client-results spotlights (session 01, Q2).
- Real failures caught by review: T04 public page links broke under /pages/ (S1, #5);
  duplicate slug gave a 500 (#9); T07 review found one bad slug would stop the whole publish (#8, S2);
  the T00 publish tests silently read the real cms.db, so they would have crashed on a clean clone (T07).
- The seed copy had two sentences stronger than the live site ("Every US college...",
  "many of them...") that had to be toned down to match the source.
-->
