# CONTEXT.md glossary

Client: **inkadmissions** — Ingkar Shokan's real admissions-consulting business (existing
static site at `~/inkadmissions-site`). This CMS runs in parallel to that site for MP2; it
does not replace it. Settled in `/grill-with-docs` session 01 (`docs/transcripts/iphs400_mp2-cms_chat-session_01_ingkar-shokan_20260929.md`).

**inkadmissions**:
The front-facing brand for the client's admissions-consulting business. Every page and post
presents itself as inkadmissions.
_Avoid_: "the business", "the service", "Ink's Diary" (a related but distinct brand).

**Ink's Diary**:
inkadmissions' existing English-learning / study-abroad Telegram audience (20,000+
followers). Referenced as social proof on the site; not the brand the CMS's content
represents itself as.

**Full aid** (scope term):
Any outcome that leaves an international student with the full cost of a US college
covered — need-aware full-need-met aid or a merit scholarship. Broader than "full ride."

**Need-blind**:
Admissions decisions made without considering ability to pay (a short, highly selective
list of schools).

**Need-aware**:
Admissions decisions that may consider ability to pay, but the school still meets full
demonstrated need for students it admits (e.g. Kenyon, the site's worked example).

**Page** (CMS content type):
One of the three static, admin-only pages — Story, Guide, Work With Me — that appear in
public navigation. Editors cannot create, edit, or publish Pages.

**The Guide** (a Page):
The evergreen, process-focused walkthrough for finding full-aid schools. Distinct from
Notes (below), which are periodic rather than evergreen.

**Post / Notes** (CMS content type):
inkadmissions' name for its "Posts" content type: periodic, dated admissions-tips/blog
entries, e.g. "Need-blind vs. need-aware: what's the actual difference." Editors may create
and edit Notes in **draft** status; only admin can publish one.
_Avoid_: "blog post", "article" — the client's own site calls this section "Notes".

**Editorial review** (CMS workflow):
The draft → published handoff: an editor's Note stays in draft until admin (Ingkar)
approves and publishes it. This is the concrete permission boundary between the two roles.

**Admin** (CMS role):
Ingkar Shokan. Full access: Pages, Notes (draft and publish), and user management.

**Editor** (CMS role):
Aigerim, a part-time assistant based in Almaty who helps draft Notes from Ingkar's voice
memos/outlines. Scoped to creating/editing her own Notes in draft status only — cannot
touch Pages, cannot publish, cannot manage users.

**Lead magnet**:
The free checklist offered on The Guide page, delivered via the Ink's Diary Telegram bot
link (not a gated email form). Out of scope for the CMS MVP — the bot link isn't ready yet
on the live site either.

**Client results**:
Verified outcomes from students inkadmissions has directly advised (Bryn Mawr, USC,
Georgetown). Used as proof on Work With Me; a source of genuine seed content for demo
Notes, not a CMS content type of its own (see Q2 in the grill transcript — this was
considered and rejected as the meaning of "Posts").

## Resolved (this project)

- Bilingual (EN/RU) is explicitly **out of scope** for the CMS MVP — English content only.
  The live `inkadmissions-site` repo remains the bilingual source of truth.
- The CMS does not replace or deploy over the live site; it publishes to its own
  `gh-pages` on this repo.
- "Posts" = Notes (admissions tips/blog), not client-results spotlights — a deliberate
  override of the recommended default in the grill session.

## Open facts (not yet resolved — do not invent)

- Whether Notes ever get categories/tags (stretch goal only, not MVP).
- Whether the CMS's demo Notes get migrated back into the live site once written.
