# Compaction log

Note on how grill/spec/tickets/T01-T03 were actually
done: this work ran from a Claude Code session rooted at the home directory
(`~`, a separate tracked repo — `telegram-bot`), not at this repo's root, so the
`.claude/hooks/` Stop/PreCompact hooks configured here (`ctx_guard.py`,
`ctx_compact_log.py`) never fired for real — they only fire when
`CLAUDE_PROJECT_DIR` (or the hook event's `cwd`) is this repo. This ledger and
this log are therefore genuinely empty, not filled with fabricated numbers.

**For Stage 2 credit on B6/B7 (session hygiene, token budget), future
`/implement` sessions for T04 onward should be run from a Claude Code session
whose actual project root is this repo** (`cd ~/code/iphs400-mp2-cms && claude`),
so the context-meter and usage-ledger hooks record real data.

One auto compaction so far: session `4d4e6cad` (sprint planning, T07, T10;
transcript 03) ran long. The hook appends rows to the end of this file, so the
table stays last.

| UTC time | Session | Trigger | Focus note |
|---|---|---|---|
| 2026-10-16 09:54 | 4d4e6cad | auto | (none) |
| 2026-10-16 22:12 | 4d4e6cad | auto | (none) |
