# Gotchas

Temporary, operational surprises: things that cost time to diagnose, are not obvious from the code,
and will stop being true. Permanent code traps belong in `CLAUDE.md` → *Traps worth knowing*.

**Keep it alive.** When something new is worth a note, add it here in the format below. When an
entry's *Remove when* holds, delete it. A `SessionStart` hook (`.claude/hooks/gotcha-check.mjs`)
warns at the start of every Claude Code session about entries missing a field or past their
*Review by* date — then either resolve and delete the entry, or renew the date with a reason.

Format (every field required, dates as `YYYY-MM-DD`):

```md
## Short title
- Added: 2026-01-01
- Review by: 2026-02-01
- Remove when: the condition that makes this note obsolete

What happens, how to recognize it, what to do meanwhile.
```
