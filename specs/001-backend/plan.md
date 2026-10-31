# Implementation Plan: VeritX Vision backend v1

**Branch**: `claude/backend-spec` | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-backend/spec.md`

## Summary

Add a backend so the site's simulated features become real: public forms that email
(Story 1), booking against the owner's Google Calendar (Story 2), invite-only multi-user customer
accounts with Vision Home (Story 3), and support tickets with small attachments (Story 4).
A FastAPI service in `/server`, deployed on Railway with Railway Postgres, reached by the browser
through a Vercel rewrite of `/api/*` so cookies stay first-party. Gmail and Calendar are used
through one OAuth credential of the owner's personal Google account. Staff administer everything
through a command-line tool. Each story ships as its own PR. Details: [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12 (backend); JavaScript/React 18 + Vite 5 (existing frontend)

**Primary Dependencies**: FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2, psycopg 3, Alembic,
argon2-cffi, httpx, python-multipart. Dev: pytest, ruff. Frontend: no new dependencies.

**Storage**: Railway Postgres 16 (attachments as `bytea`)

**Testing**: pytest against real Postgres (CI service container); Vitest for frontend logic

**Target Platform**: Linux container on Railway (backend); Vercel static hosting (frontend)

**Project Type**: Web application (existing static frontend + new API service)

**Performance Goals**: Low volume (tens of requests/day, <100 portal users); pages and API
responses feel instant (<1 s); email reaches staff within 2 min (SC-001)

**Constraints**: No own domain; personal Gmail ~500 emails/day; same-origin via Vercel rewrite;
attachments ≤2 MB uploaded one per request; marketing site must keep working if the API is down

**Scale/Scope**: 4 user stories, ~11 tables, ~15 endpoints, ~12 CLI commands, 6 frontend pages touched

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Simplicity First | ✅ with justification | Second language and a server are owner decisions (grill-me); complexity kept down: no Redis (limits from existing rows, R6), no Google SDK (4 REST calls, R7), stdlib CLI (R11). See Complexity Tracking. |
| II. Test-First (minimal, ADR 001) | ✅ | Extended to backend critical logic: auth, tenant isolation, slots/double-booking, upload validation, no-echo emails (R12). Written before the code they cover. |
| III. Modular & testable | ✅ | Modules per concern (auth, booking, tickets, forms, google client, emails); Google client swappable with a fake. |
| IV. Observability | ✅ | JSON logs per request and per external failure; notification status stored per record; audit log (R13). |
| V. Versioning | ✅ with note | API is private to this site and deployed with it; unversioned `/api`, documented in contracts/api.md. Schema changes via Alembic migrations. |
| VI. Spec before code | ✅ | spec.md confirmed by owner; implementation waits for confirmation of this plan. |
| Quality & Security | ⚠ flag for security review | Touches auth and personal data → every PR flagged. OWASP: parameterized queries (ORM), Argon2id, server sessions, Origin check, generic errors, rate limits, magic-byte uploads, no free-text echo to visitors. |
| New dependencies need an ADR | ✅ | ADR `docs/decisions/002-backend-stack.md` (written with this plan). |

Post-design re-check: no new violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-backend/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md
├── contracts/api.md · contracts/cli.md
├── checklists/requirements.md
└── tasks.md             # next step (/speckit-tasks)
```

### Source Code (repository root)

```text
server/                      # NEW — Railway service root
├── pyproject.toml           # deps, ruff, pytest config
├── .env.example             # names of every env var (no values)
├── alembic.ini · migrations/
├── app/
│   ├── main.py              # FastAPI app, routers, origin check, JSON logging
│   ├── config.py            # env vars
│   ├── db.py · models.py    # engine/session, tables (data-model.md)
│   ├── security.py          # hashing, tokens, sessions, rate-limit queries
│   ├── google.py            # OAuth refresh, Gmail send, freeBusy, events.insert (+ fake)
│   ├── emails.py            # es/en/fr templates (R10)
│   ├── routes/forms.py      # /contact, /calculator-results            (Story 1)
│   ├── routes/booking.py    # /availability, /bookings                 (Story 2)
│   ├── routes/auth.py       # /auth/*, /me                             (Story 3)
│   ├── routes/tickets.py    # /attachments, /tickets                   (Story 4)
│   └── cli.py               # staff commands (contracts/cli.md)
└── tests/                   # pytest, per module

src/                         # EXISTING frontend
├── api.js                   # NEW — fetch wrapper for /api, error codes → i18n keys
├── auth.js                  # REWRITTEN — calls /api/auth, keeps useAuthSession()
├── App.jsx                  # Contact + AppointmentPicker use the API
├── CalculatorPage.jsx       # send-results uses the API
├── LoginPage.jsx · ForgotPasswordPage.jsx · VisionHomePage.jsx   # use the API
├── AcceptInvitePage.jsx     # NEW (#/accept-invite?token=) replaces VerifyEmailPage
├── RegisterPage.jsx · RecoverUsernamePage.jsx · VerifyEmailPage.jsx   # DELETED
└── translations.js          # new/removed copy in es/en/fr

vercel.json                  # NEW — rewrite /api/:path* → Railway URL
vite.config.js               # dev proxy /api → localhost:8000
.github/workflows/ci.yml     # NEW job: server (Postgres service, ruff, pytest)
docs/decisions/002-backend-stack.md · docs/deployment/environments.md   # NEW
```

**Structure Decision**: Web application in one repo: existing frontend stays at the root (no
move, to keep Vercel config untouched); backend in `server/` with its own Python tooling, deployed
by Railway with root directory `server`.

## Delivery order (one PR per story)

| PR | Story | Contains | Depends on |
|---|---|---|---|
| 1 | Foundation + P1 | server skeleton, DB + migrations, Google client, emails, CI job, vercel.json, ADR 002, deployment doc, forms endpoints + frontend wiring | — |
| 2 | P2 | availability + bookings, picker wiring | PR 1 |
| 3 | P3 | auth, sessions, CLI admin, Vision Home data, page removals | PR 1 |
| 4 | P4 | attachments, tickets, Vision Home tickets | PR 3 |

Owner actions before PR 1 can be verified live: create the Railway project + Postgres, create the
Google OAuth client (consent screen "In production"), run `cli google-auth`, set env vars
(`docs/deployment/environments.md`), and give the Railway URL for `vercel.json`.

## Docs to update during implementation
- `CLAUDE.md`: commands for `server/`, replace the "no rewrites" trap, add "emails to visitors never echo free text".
- `docs/architecture/SDD.md`: §2 (stack), §11 (gaps closed), §14 (portal now real).
- `GOTCHA.md`: Google OAuth "Testing" status expires refresh tokens in 7 days; preview deployments hit the production API.
- `docs/README.md`: rows for ADR 002 and the deployment doc.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Second language/toolchain (Python) in the repo | Owner chose FastAPI (grill-me) | Node backend: owner preference for Python and future ML code |
| A server + database at all | Real email, booking, accounts cannot be done client-side | Third-party form/booking services: don't cover accounts; owner wants one system |
| Two-step attachment upload | Keeps each request ≤2 MB through the proxy | Single multipart request of up to 6 MB risks proxy body limits |
