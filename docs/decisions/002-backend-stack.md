# 002. Backend stack

- Status: proposed
- Date: 2026-10-31

## Context

Spec `specs/001-backend` needs real email, booking, accounts and tickets. ADR 001 fixed Railway as
the backend host and left runtime, database and repo location open. The owner settled them in a
grill-me interview. VeritX has no domain and uses a personal Gmail account.

## Decision

| Area | Choice |
|---|---|
| Runtime | Python 3.12 + FastAPI (Uvicorn) |
| Location | `server/` in this repo; Railway service root `server` |
| Database | Railway Postgres 16; SQLAlchemy 2 + psycopg 3; Alembic migrations |
| Browser access | Vercel rewrite `/api/*` → Railway (same origin, first-party cookies) |
| Auth | Invite-only; email + password; Argon2id; server-side sessions in Postgres |
| Email + calendar | Owner's personal Google account via one OAuth refresh token (Gmail send, Calendar) over HTTPS (httpx) |
| Files | Attachments ≤2 MB in Postgres |
| Admin | Python CLI (`python -m app.cli`), run with `railway run` |
| Tests | pytest + Postgres in CI; extends ADR 001 "minimal" to backend auth, tenant isolation, booking and uploads |

Details and alternatives: `specs/001-backend/research.md`.

## Consequences

- Two toolchains (Node + Python) and two CI jobs.
- Vercel previews call the production API until a staging environment exists.
- The Gmail account limits sending to ~500/day and its OAuth consent screen must stay "In
  production"; a domain + email service is the upgrade path.
- IP-based rate limits are best-effort (spoofable `X-Forwarded-For` if Railway is called directly);
  per-account limits are authoritative.
