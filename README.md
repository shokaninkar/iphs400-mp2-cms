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

I used Claude Code to help build this CMS. The saved usage ledger labels the provider as **Anthropic** and the model as **Opus 5.5**. Claude wrote implementation code, tests and draft documentation. I supplied the project direction and answered the client questions. I also used ChatGPT to revise the client brief, report and this statement against the saved files and my answers. This was substantial AI assistance, not just spelling correction.

The planning and review workflow included `/grill-with-docs`, `/to-spec`, `/to-tickets`, test-first work, `/code-review` and `/handoff`. I asked for `/implement`, but it was unavailable in sessions 05 and 06. Session 05 checked existing T09 work, and Claude implemented T06 directly from the ticket in session 06. The intended one-ticket-per-fresh-session process was not followed consistently.

Two prompts in the transcripts are:

> “Read docs/handoff/01_t04-pages-wrapup_20261006.md and finish T04 following CLAUDE.md.”

> `/code-review`

One choice I disagreed with was the meaning of Posts. Claude suggested client-results spotlights. I chose recurring admissions tips, called **Notes**, because I wanted the site to help people understand applications. I kept the first version English-only and required admin approval before publication. I let Claude choose the fictional editor name **Aigerim**; she is a workflow persona, not a real employee I interviewed.

The review caught a duplicate slug (Notes and Pages) that caused a 500 error and public links that broke one folder down, under `/pages/`. Claude made the code fixes. The misleading Pages permission test was fixed in T05; I should not claim I personally wrote that fix. I also noticed when my task had not started after I put instructions on the same line as `/clear`, and asked Claude what was happening.

### Backends used

| Backend | Model | Role |
|---|---|---|
| Anthropic | Claude Opus 5.5 | Claude Code planning, implementation and review; recorded in `notes/usage-ledger.csv` |

Claude Code never ran on another provider, so there are no `Backend:` commit trailers. Outside Claude Code, I used **ChatGPT** (OpenAI; model not independently verified) in the browser for WordPress Playground help and to revise the client brief, report and this statement. It was not a Claude Code backend, so it has no ledger rows.

The transcripts, `CONTEXT.md`, specification, issues and tests are the record against which these claims can be checked.
