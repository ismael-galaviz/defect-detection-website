# HTTP API contract (v1)

Base path `/api`, same origin as the site (Vercel rewrite). JSON unless noted. The API is used
only by this site, so it is unversioned; breaking changes ship with the matching frontend change
in the same PR.

**Errors**: `{"error": "<code>", "fields": {"<field>": "<code>"}}` (`fields` only on 422).
Common codes: `invalid` (422), `rate_limited` (429), `not_found` (404), `unauthenticated` (401),
`bad_origin` (403). State-changing requests without a matching `Origin` → 403.

## Public

| Method & path | Body | Success | Errors |
|---|---|---|---|
| `GET /health` | — | 200 `{"ok": true}` | — |
| `POST /contact` | `{kind: "message", name, company, email, country?, stage?, message?, lang, website}` | 202 | 422, 429 |
| `POST /calculator-results` | `{name?, email, lang, currency, inputs: {section: {field: number}}, results: {section: number, total: number}}` | 202 | 422, 429 |
| `GET /availability?from=YYYY-MM-DD&to=YYYY-MM-DD` | — | 200 `{"timezone": "America/Mexico_City", "slots": ["2026-11-03T10:00:00-06:00", …]}` | 422 (range > 62 days), 503 `calendar_unavailable` |
| `POST /bookings` | `{slot_start, name, company, email, country?, stage?, video_tool?, message?, lang, website}` | 201 `{"slot_start": …}` | 409 `slot_unavailable`, 422, 429, 503 `calendar_unavailable` |

`website` is the honeypot: non-empty → respond as success, store nothing, send nothing.
`calculator-results`: numbers only; at most 3 sections × 4 fields.

## Auth

| Method & path | Body | Success | Errors |
|---|---|---|---|
| `POST /auth/login` | `{email, password}` | 204 + `Set-Cookie: vx_session` | 401 `invalid_credentials` (unknown email, wrong password, not active), 429 `locked` `{retry_after}` |
| `POST /auth/logout` | — | 204, cookie cleared | — |
| `GET /auth/invite/{token}` | — | 200 `{email, name, company}` | 410 `link_expired` |
| `POST /auth/accept-invite` | `{token, password}` | 204 + cookie | 410 `link_expired`, 422 `password_weak` |
| `POST /auth/forgot` | `{email, lang}` | 202 always | 429 |
| `POST /auth/reset` | `{token, password}` | 204 (all sessions ended) | 410 `link_expired`, 422 `password_weak` |

## Portal (session cookie required, else 401)

| Method & path | Body | Success | Errors |
|---|---|---|---|
| `GET /me` | — | 200 `{user: {name, email, lang}, company: {name}, subscriptions: [{name, status}], payments: [{paid_on, amount, currency}], tickets: [{id, subject, priority, status, created_at, attachments: [{id, filename, size}]}]}` | — |
| `POST /attachments` | multipart, field `file` | 201 `{id, filename, size, content_type}` | 413 `too_large`, 415 `unsupported_type` |
| `GET /attachments/{id}` | — | 200 file (`Content-Disposition: attachment`) | 404 (incl. other company) |
| `POST /tickets` | `{subject, description, priority, attachment_ids: [≤3]}` | 201 `{id}` | 422 (incl. foreign/used attachment id) |
