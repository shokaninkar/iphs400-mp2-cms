# IPHS 400 MP2 — /grill-with-docs session 01

**Student:** Ingkar Shokan
**Date:** 2026-09-29
**Client:** inkadmissions (Ingkar's real admissions-consulting business, existing site at `~/inkadmissions-site`)

## Round 1

❓ **Q1 — Is the editor role a real person?**
The CMS needs two roles (admin, editor) with genuinely different permissions the grader will test. Is there an actual second person who'll use inkadmissions, or should we invent a plausible one for the project?

➡️ Recommended: invent a plausible one — a part-time assistant who drafts content but can't publish/manage users.

**Ingkar:** Confirmed — a part-time assistant who drafts content but can't publish/manage users.

❓ **Q2 — What do "Posts" actually mean for inkadmissions?**
(a) Client results spotlights (b) Admissions tips/blog — periodic advice posts (c) Testimonials

➡️ Recommended: (a) client results spotlights.

**Ingkar:** Overrode the recommendation — chose (b), admissions tips/blog, periodic advice posts.

❓ **Q3 — Is bilingual (EN/RU) in scope for the CMS MVP?**

➡️ Recommended: out of scope for MVP, English only, noted explicitly in the spec's out-of-scope list.

**Ingkar:** Confirmed — English only, not bilingual, for MVP.

❓ **Q4 — Does this CMS replace the live inkadmissions site, or run in parallel?**

➡️ Recommended: run in parallel, seeded with real inkadmissions facts, no cutover of the live site.

**Ingkar:** Confirmed — run in parallel.

## Round 2

❓ **Q5 — Can the editor touch the three static Pages (Story/Guide/Work With Me)?**

➡️ Recommended: Pages are admin-only; editor is scoped entirely to Posts.

**Ingkar:** Confirmed.

❓ **Q6 — Can the editor publish their own posts, or does publishing require admin approval?**

➡️ Recommended: editor can create/edit posts as drafts only; only admin can flip a post to published.

**Ingkar:** Confirmed.

## Round 3

❓ **Q7 — What do you call the blog/advice section in nav and copy?**
Options: "Notes," "Advice," "The Notes," or the student's own.

➡️ Recommended: "Notes" — short, on-brand, distinct from "The Guide" (evergreen how-to) since Notes are periodic/dated.

**Ingkar:** Confirmed — "Notes."

❓ **Q8 — Who is the editor persona, concretely?**
A plausible name/detail beats a generic "Editor User" for seed data and the glossary.

➡️ Recommended: give them a first name and a one-line role.

**Ingkar:** Delegated the specific name/detail back to Claude ("your call").
**Resolved (Claude, on delegation):** Aigerim — a part-time assistant based in Almaty who helps draft Notes from Ingkar's voice memos/outlines.

## Settled design

- **Roles:** admin (Ingkar) — full access. editor (Aigerim) — Notes only, draft status only, no Pages, no publish, no user management.
- **Content model:** Pages = Story, Guide, Work With Me (admin-only, in public nav). Posts = "Notes," periodic admissions-tips/blog entries (editor drafts, admin publishes).
- **Scope:** English only for MVP (bilingual EN/RU explicitly out of scope). Runs in parallel to the live `inkadmissions-site` repo — no cutover.
- **Seed content:** real inkadmissions facts and voice (from the live site's `CONTEXT.md`), not placeholder Lorem Ipsum.
