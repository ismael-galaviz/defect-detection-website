# Staff CLI contract

Run against production: `railway run python -m app.cli <command> [options]` from `server/`.
Every command prints a one-line result; non-zero exit on error.

| Command | Options | Effect |
|---|---|---|
| `google-auth` | — | One-time local OAuth consent; prints the refresh token to store as `GOOGLE_REFRESH_TOKEN`. |
| `company-add` | `--name` | Create a company. |
| `invite` | `--company --email --name [--lang es\|en\|fr]` | Create user (`invited`) and email a 7-day invite. Re-running for an invited user sends a fresh link; for an active user it refuses. |
| `user-disable` / `user-enable` | `--email` | Change status; disable ends sessions. |
| `subscription-add` | `--company --name [--status]` | Add a subscription. |
| `subscription-set` | `--id --status` | Change status. |
| `payment-add` | `--company --date YYYY-MM-DD --amount --currency` | Record a payment. |
| `ticket-status` | `--id --status open\|in_progress\|resolved\|closed` | Change ticket status. |
| `list` | `companies\|users\|tickets\|pending [--company]` | Print records (pending = failed/unsent notifications). |
| `resend-pending` | — | Retry emails with `pending`/`failed` status. |
| `cleanup` | — | Delete unlinked attachments > 24 h and expired sessions/tokens. |

Every command that changes users writes `audit_log`.
