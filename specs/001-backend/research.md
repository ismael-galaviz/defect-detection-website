# Research: VeritX Vision backend v1

Decisions behind `plan.md`. Owner decisions from the grill-me interview are marked **(owner)**.

## R1. Runtime and framework
- **Decision**: Python 3.12 + FastAPI, served by Uvicorn, in `/server` of this repo **(owner)**.
- **Rationale**: Typed request validation (Pydantic) and generated OpenAPI docs; same language as
  likely future ML/defect-detection code.
- **Alternatives**: Node + Fastify/Express (one language), Vercel functions (rejected: owner chose
  Railway; uploads and long calls are awkward there).

## R2. Database access and migrations
- **Decision**: Railway Postgres **(owner)**; SQLAlchemy 2.0 (sync, ORM-light) with psycopg 3;
  Alembic migrations run on deploy (`alembic upgrade head` as Railway pre-deploy command).
- **Rationale**: Sync code is simpler; FastAPI runs sync endpoints in a thread pool, ample for
  tens of requests/day. Alembic is the standard for SQLAlchemy schema history.
- **Alternatives**: raw SQL (no migration story), async SQLAlchemy (more complexity, no need).

## R3. Same-origin API via Vercel rewrite
- **Decision**: `vercel.json` rewrites `/api/:path*` to the Railway service URL **(owner)**. In
  development, Vite's `server.proxy` forwards `/api` to `http://localhost:8000`.
- **Rationale**: Browser sees one origin, so the session cookie is first-party (works in Safari)
  and no CORS is needed. Keeps working when a domain is added later.
- **Consequence**: `CLAUDE.md`'s trap "Vercel has no rewrites" must be updated. Vercel rewrite
  destinations cannot read env vars, so **preview deployments also use the production API** in
  v1 (accepted; a staging Railway environment is a later improvement).
- **Body size**: to stay well under proxy request-size limits, attachments are uploaded one file
  per request (≤2 MB) — see R9.

## R4. Password hashing
- **Decision**: Argon2id via `argon2-cffi` with its default (RFC 9106 low-memory) parameters;
  rehash on login when parameters change.
- **Alternatives**: bcrypt (72-byte limit, older), scrypt.

## R5. Sessions and CSRF
- **Decision**: Random 32-byte token in cookie `vx_session` (`HttpOnly; Secure; SameSite=Lax;
  Path=/api`); only its SHA-256 is stored in `sessions`. Expiry: 7 days absolute, 24 h idle
  (FR-017). State-changing requests must carry an `Origin` header matching `PUBLIC_SITE_ORIGINS`.
- **Rationale**: Server-side sessions are revocable (reset, disable — FR-020, scenario 3.9).
  SameSite=Lax + Origin check covers CSRF without tokens in forms.
- **Alternatives**: JWT (not revocable without a denylist), CSRF tokens (more frontend work).

## R6. Rate limiting without extra infrastructure
- **Decision**: Count rows already being written, in Postgres:
  - login lockout: failed-login rows in `audit_log` for the email in the last 15 min (FR-019);
  - reset requests: reset-requested rows per email/IP in `audit_log`;
  - public forms: `contact_requests` rows per IP in the last 10 min (FR-005).
- **Rationale**: Single instance, low volume — no Redis or limiter library needed (Ponytail).
- **Caveat**: Client IP comes from `X-Forwarded-For` added by Vercel/Railway. A caller hitting the
  Railway URL directly can spoof it, so **IP limits are best-effort; per-account limits are the
  authoritative control**. Documented, accepted for v1.

## R7. Google: one OAuth credential for Gmail and Calendar
- **Decision**: A Google Cloud OAuth client ("Desktop app") owned by the VeritX Gmail account,
  scopes `gmail.send` and `calendar.events` + `calendar.freebusy`. A one-time CLI command runs the
  consent flow locally and prints a refresh token, stored as `GOOGLE_REFRESH_TOKEN` in Railway.
  Calls use plain HTTPS (httpx) to four endpoints: token refresh, `gmail.users.messages.send`,
  `freeBusy.query`, `events.insert`.
- **Rationale**: Personal Gmail accounts cannot use service accounts with delegation. Four REST
  calls do not justify the large `google-api-python-client`.
- **Trap**: The OAuth consent screen must be set to **"In production"** (unverified is fine for
  the owner's own account). In "Testing" status Google expires refresh tokens after 7 days. To be
  recorded in `GOTCHA.md` when implemented.
- **Alternatives**: Gmail SMTP with an app password (needs 2FA, separate credential from Calendar).

## R8. Booking and double-booking prevention
- **Decision**: Availability = slot grid (FR-007) minus Google free/busy minus existing
  `bookings`. Booking: re-check free/busy, `INSERT` into `bookings` (unique on `slot_start`), then
  create the event with `conferenceData` (Meet link), `attendees=[visitor]`, `sendUpdates=all`. If
  the insert violates uniqueness → 409 `slot_unavailable`; if event creation fails → delete the
  row, 503 `calendar_unavailable`.
- **Visitor's preferred tool**: the form already asks for a preferred tool (Zoom, Teams, …). The
  event always gets a Meet link; the preference is written into the event description and the
  staff email so staff can send another link. (Resolves a conflict between the spec and the
  existing form; no UI change.)

## R9. Attachments
- **Decision**: Stored in Postgres (`bytea`) **(owner)**. Two-step upload: `POST /api/attachments`
  (one file, ≤2 MB, owned by the user, not yet linked) → ticket creation references up to 3
  attachment ids. Type is judged by magic bytes (PNG `89 50 4E 47 0D 0A 1A 0A`, JPEG `FF D8 FF`,
  PDF `%PDF-`) — stdlib only. Unlinked uploads older than 24 h are deleted by a CLI command.
  Downloads are served with `Content-Disposition: attachment` and the sniffed type.

## R10. Email content and abuse
- **Decision**: Emails are rendered from fixed templates per language (es/en/fr) in
  `server/app/emails.py`. **Messages sent to visitor-supplied addresses never echo free text**
  (no name, message or company) — only fixed copy and, for calculator results, numbers. Free text
  goes only to the staff inbox.
- **Rationale**: Otherwise the public forms become a spam relay through the VeritX Gmail account.
- **Sending**: after the DB commit, via FastAPI background tasks; each request row has
  `notification_status` (`pending`/`sent`/`failed`); `vx resend-pending` retries (FR-006).

## R11. Staff CLI
- **Decision**: `python -m app.cli <command>` using stdlib `argparse`, run with `railway run` (or
  `railway ssh`) so it uses production env vars. Commands in `contracts/cli.md`.
- **Alternatives**: Typer/Click (extra dependency for ~12 commands).

## R12. Testing and CI
- **Decision**: pytest against a real Postgres (CI service container `postgres:16`; locally Docker
  or a local Postgres). Google calls go through one small client module that tests replace with a
  fake. Required tests (ADR 001 "minimal", extended): auth (hashing, sessions, lockout, tokens,
  tenant isolation), slot computation and double-booking, upload validation, email templates don't
  echo free text to visitors.
- **CI**: new `server` job in `.github/workflows/ci.yml` (ruff lint + pytest).

## R13. Logging
- **Decision**: stdlib `logging` with a JSON formatter to stdout (Railway collects it); one line
  per request (method, path, status, duration) and per external call failure. No secrets, tokens
  or passwords in logs.
