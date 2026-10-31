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

## Google OAuth refresh token expires after 7 days in "Testing"
- Added: 2026-10-31
- Review by: 2027-01-31
- Remove when: VeritX moves email to its own domain/email service and booking no longer uses the personal Google account

If the OAuth consent screen of the VeritX Google Cloud project is left in "Testing", Google
revokes the refresh token after 7 days: emails stop (requests show `failed` in
`python -m app.cli list pending`) and booking reports the calendar as unavailable. Publish the
consent screen ("In production"), re-run `python -m app.cli google-auth`, update
`GOOGLE_REFRESH_TOKEN` in Railway, then `python -m app.cli resend-pending`.

## Vercel previews call the production backend
- Added: 2026-10-31
- Review by: 2027-01-31
- Remove when: a staging Railway environment exists and previews point to it

`vercel.json` rewrite destinations can't use env vars, so every preview deployment sends
`/api/*` to the production Railway service. Testing a form on a preview sends real emails and
stores real rows. Use local dev (`GOOGLE_FAKE=1`) for experiments.
