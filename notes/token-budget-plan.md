# Token budget plan

One `/implement` session per ticket, per `CLAUDE.md`. Plan made before the first
`/implement` commit (T01); actuals get filled in from `notes/usage-ledger.csv` for the
Stage 2 report.

| Ticket | Planned sessions | Notes |
|---|---|---|
| T01 — Auth | 1 | Foundational; smallest scope (login/logout/hash/CSRF) |
| T02 — Roles & access control | 1 | Thin layer on T01; mostly a FastAPI dependency + tests |
| T03 — Notes vertical slice | 1–2 | First content type + schema; likely the largest of the three MVP tickets |
| T04 — Pages vertical slice | 1 | Reuses T03's schema/patterns |
| T05 — Admin console UX | 1 | Dashboard + filters + preview, no new schema |
| T06 — User management | 1 | Reuses T01/T02's auth patterns |
| T07 — Public site & publish | 1–2 | Templating + relative-path correctness needs care |

**Total planned:** 8 sessions across 7 tickets. Grill (`docs/transcripts/..._01_...`), spec,
and ticket-breakdown sessions are tracked separately in the ledger under phases `grill`,
`spec`, `tickets`.

Actual vs. plan gets filled in for the Stage 2 report once `notes/usage-ledger.csv` has
enough sessions logged.
