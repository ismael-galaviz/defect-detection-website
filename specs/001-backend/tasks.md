---
description: "Tasks for VeritX Vision backend v1"
---

# Tasks: VeritX Vision backend v1

**Input**: `specs/001-backend/` (plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md)

**Tests**: Required for backend critical logic (plan R12, ADR 001/002): auth, tenant isolation,
slots/double-booking, upload validation, no-echo visitor emails. Write them first and see them
fail. UI changes are verified manually per `quickstart.md`.

**Organization**: One phase per user story; each story ships as its own PR (plan "Delivery order").
Phases 1–2 ship inside PR 1 together with US1.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: parallelizable (different files, no dependency on an unfinished task)
- Paths: backend `server/`, frontend `src/` at repo root

---

## Phase 1: Setup

- [X] T001 Create `server/pyproject.toml` (Python 3.12; deps from plan Technical Context; dev: pytest, ruff; ruff + pytest config) and `server/app/__init__.py`
- [X] T002 [P] Create `server/.env.example` listing `DATABASE_URL`, `STAFF_EMAIL`, `PUBLIC_SITE_ORIGINS`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`, `GOOGLE_CALENDAR_ID`, `GOOGLE_FAKE`, `SITE_URL` (no values) and add `server/.venv/`, `__pycache__/` to `.gitignore`
- [X] T003 [P] Add `server` job to `.github/workflows/ci.yml`: Postgres 16 service, Python 3.12, `pip install -e 'server[dev]'`, `ruff check server`, `pytest server`
- [X] T004 [P] Add dev proxy `server.proxy: { '/api': 'http://localhost:8000' }` in `vite.config.js`
- [X] T005 [P] Create `vercel.json` with rewrite `/api/:path*` → `<RAILWAY_URL>/api/:path*` (placeholder until the owner provides the URL; leave a `shortcut:` note in the PR, not in JSON)
- [X] T006 [P] Write `docs/deployment/environments.md` (Railway service root `server`, pre-deploy `alembic upgrade head`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, every env var and who sets it, Google OAuth setup incl. "In production" consent screen) and add its row to `docs/README.md`

---

## Phase 2: Foundational (blocks all stories)

- [X] T007 Implement `server/app/config.py` (read env vars into a settings object; fail fast on missing required ones)
- [X] T008 Implement `server/app/db.py` (SQLAlchemy engine/session from `DATABASE_URL`, request-scoped session dependency)
- [X] T009 Create Alembic setup `server/alembic.ini`, `server/migrations/env.py`
- [X] T010 Write `server/tests/conftest.py`: test database (create/drop schema per session, transaction rollback per test), FastAPI `TestClient`, fake Google client fixture, fixed `Origin` header
- [X] T011 [P] Write tests for the Google client in `server/tests/test_google.py` (token refresh request shape, Gmail raw MIME base64url incl. attachments, freeBusy and events.insert payloads with conferenceData; using httpx MockTransport)
- [X] T012 Implement `server/app/google.py`: OAuth refresh, `send_email(to, subject, text, reply_to=None, attachments=())`, `busy_intervals(start, end)`, `create_event(start, end, summary, description, attendee)`; `FakeGoogle` when `GOOGLE_FAKE=1` logs instead of calling
- [X] T013 Implement `server/app/main.py`: FastAPI app under `/api`, `GET /api/health`, JSON logging (R13), Origin check for non-GET requests (403 `bad_origin`), error format from `contracts/api.md`, client-IP helper from `X-Forwarded-For`
- [X] T014 Implement `server/app/cli.py` skeleton with argparse subcommands and `google-auth` (local consent flow printing the refresh token) per `contracts/cli.md`
- [X] T015 Update `CLAUDE.md`: reference `docs/decisions/002-backend-stack.md` in Project, add commands (`server/`: `pip install -e '.[dev]'`, `uvicorn app.main:app --reload`, `pytest`, `ruff check .`) and replace the "no rewrites" trap with the `/api` rewrite rule

**Checkpoint**: `pytest server` and `GET /api/health` pass locally and in CI.

---

## Phase 3: User Story 1 — Contact requests and calculator results arrive (P1) 🎯 MVP

**Goal**: Public forms store requests and really email staff and visitor (FR-001…FR-006).
**Independent test**: quickstart.md step 1.

### Tests (write first)
- [X] T016 [P] [US1] Tests in `server/tests/test_forms.py`: valid contact → 202, row stored, staff + visitor emails sent; 422 field errors; honeypot → 202 and nothing stored/sent; 6th submission from one IP in 10 min → 429; email failure → row stored with `notification_status=failed`; calculator payload rejects non-numbers and >3 sections
- [X] T017 [P] [US1] Tests in `server/tests/test_emails.py`: every visitor template (es/en/fr) contains none of the submitted free-text values (name, company, message); staff template contains all fields

### Implementation
- [X] T018 [US1] Add `ContactRequest` model (kind, lang, email, payload jsonb, ip, notification_status) in `server/app/models.py` and migration `server/migrations/versions/0001_contact_requests.py` with index `(ip, created_at)`
- [X] T019 [P] [US1] Implement `server/app/emails.py`: templates for staff contact/calculator/booking notifications and visitor confirmation/calculator results in es/en/fr; currency formatting per lang (R10)
- [X] T020 [US1] Implement `server/app/routes/forms.py`: `POST /api/contact`, `POST /api/calculator-results` (Pydantic models per contracts/api.md, honeypot, IP rate limit from `contact_requests`, commit then send in background task updating `notification_status`)
- [X] T021 [US1] Add `list pending` and `resend-pending` commands in `server/app/cli.py`
- [X] T022 [P] [US1] Create `src/api.js`: `post(path, body)` / `get(path)` with JSON, credentials `same-origin`, throws `{status, error, fields}`; network failure → `{error: 'network'}`
- [X] T023 [US1] Wire `Contact()` message mode in `src/App.jsx` to `POST /api/contact` (controlled field values, hidden `website` input, loading state, field errors, network/429 error message per FR-031) and add copy in all three languages in `src/translations.js`
- [X] T024 [US1] Wire `handleSendResults` in `src/CalculatorPage.jsx` to `POST /api/calculator-results` with inputs, computed `CALC` results, currency and lang; errors as in T023

**Checkpoint**: Story 1 works end-to-end with `GOOGLE_FAKE=1`; on the preview with real Google (quickstart 1). → **PR 1** (`Closes #2`).

---

## Phase 4: User Story 2 — Real meeting booking (P2)

**Goal**: Picker shows only free slots; booking creates a Meet event; no double-booking (FR-007…FR-010).
**Independent test**: quickstart.md step 2.

### Tests (write first)
- [X] T025 [P] [US2] Tests in `server/tests/test_slots.py` (pure function): grid Mon–Fri 09,10,11,12,13,16,17 CDMX; excludes weekends, <24 h ahead, >60 days, busy intervals overlapping any part of the hour, already-booked slots; correct `-06:00` offsets
- [X] T026 [P] [US2] Tests in `server/tests/test_booking.py`: `GET /api/availability` range validation (422 > 62 days) and 503 when Google fails; `POST /api/bookings` → 201 + event created with visitor attendee and video_tool in description; same slot twice → second 409 `slot_unavailable`; slot not on grid → 422; event creation failure → 503 and no booking row left

### Implementation
- [X] T027 [US2] Add `Booking` model (unique `slot_start`, `calendar_event_id`, FK to contact_requests) in `server/app/models.py` and migration `server/migrations/versions/0002_bookings.py`
- [X] T028 [US2] Implement `server/app/booking.py`: `free_slots(range, busy, booked, now)` pure function per T025
- [X] T029 [US2] Implement `server/app/routes/booking.py`: `GET /api/availability`, `POST /api/bookings` (store contact_request kind `meeting`, insert booking, create event, rollback on failure, staff + visitor emails) per research R8
- [X] T030 [US2] Change `AppointmentPicker` and schedule mode of `Contact()` in `src/App.jsx`: fetch `/api/availability` for the visible month, show only returned slots, handle 409 (refresh slots + message), 503 fallback to message mode (FR-010); replace fixed `APPT_TIME_SLOTS` usage; copy in es/en/fr in `src/translations.js`

**Checkpoint**: quickstart step 2 passes → **PR 2** (`Closes #3`).

---

## Phase 5: User Story 3 — Invite-only accounts and Vision Home (P3)

**Goal**: Real invite, sign-in, reset, sessions, company data in Vision Home; simulated portal removed (FR-011…FR-024).
**Independent test**: quickstart.md step 3.

### Tests (write first)
- [X] T031 [P] [US3] Tests in `server/tests/test_security.py`: Argon2id hash/verify/rehash; token create/hash/expire/single-use; new token invalidates older ones; session expiry (7 d absolute, 24 h idle); password policy (≥12 chars, common list)
- [X] T032 [P] [US3] Tests in `server/tests/test_auth.py`: invite → accept → signed in; used/expired invite → 410; login wrong password and unknown email give identical 401; 5 failures/15 min → 429 even with right password; forgot returns 202 for unknown email; reset ends all sessions; logout invalidates cookie; disabled user's session rejected; cookie flags `HttpOnly; Secure; SameSite=Lax; Path=/api`; audit rows written for every event in FR-023
- [X] T033 [P] [US3] Tests in `server/tests/test_tenancy.py`: two companies; `GET /api/me` returns only own subscriptions/payments; no endpoint exposes another company's records
- [X] T034 [P] [US3] Tests in `server/tests/test_cli.py`: company-add, invite (new / re-invite / refuses active), user-disable ends sessions, subscription-add/set, payment-add validation

### Implementation
- [X] T035 [US3] Add models `Company`, `User`, `Token`, `Session`, `Subscription`, `Payment`, `AuditLog` in `server/app/models.py` and migration `server/migrations/versions/0003_accounts.py` (indexes per data-model.md)
- [X] T036 [US3] Implement `server/app/security.py`: hashing, token and session helpers, `current_user` dependency (validates cookie, idle/absolute expiry, updates `last_seen_at`), audit helper, login-lockout and reset-limit queries (R6)
- [X] T037 [US3] Implement `server/app/routes/auth.py`: `/api/auth/login`, `/logout`, `/invite/{token}`, `/accept-invite`, `/forgot`, `/reset`, and `GET /api/me` per contracts/api.md; invite/reset emails in user's lang in `server/app/emails.py`
- [X] T038 [US3] Add CLI commands `company-add`, `invite`, `user-disable`, `user-enable`, `subscription-add`, `subscription-set`, `payment-add`, `list companies|users`, `cleanup` (sessions/tokens) in `server/app/cli.py`
- [X] T039 [US3] Rewrite `src/auth.js` to call the API (`login`, `logout`, `getInvite`, `acceptInvite`, `requestPasswordReset`, `resetPassword`, `fetchMe`) keeping `useAuthSession()`'s shape; remove localStorage auth, `IS_DUMMY_LOGIN_ENABLED`, `DEMO_ACCOUNT`; replace `src/auth.test.js` with tests of the remaining pure helpers (e.g. `isValidEmail`) or delete if none remain
- [X] T040 [US3] Create `src/AcceptInvitePage.jsx` (`#/accept-invite?token=`: show email/company, set password, sign in) and route it in `src/App.jsx`
- [X] T041 [US3] Update `src/LoginPage.jsx` (email only, "accounts are by invitation" note, error codes) and `src/ForgotPasswordPage.jsx` (request + reset via API)
- [X] T042 [US3] Update `src/VisionHomePage.jsx` to load `GET /api/me` (loading, empty and error states; 401 → redirect to login)
- [X] T043 [US3] Delete `src/RegisterPage.jsx`, `src/RecoverUsernamePage.jsx`, `src/VerifyEmailPage.jsx`, their routes and links in `src/App.jsx`, and their copy in `src/translations.js` (all three languages); add new copy in es/en/fr

**Checkpoint**: quickstart step 3 passes → **PR 3** (`Closes #8` partially: accounts; ticket part in PR 4).

---

## Phase 6: User Story 4 — Support tickets with attachments (P4)

**Goal**: Signed-in users create tickets with ≤3 small files; staff notified; status visible (FR-025…FR-029).
**Independent test**: quickstart.md step 4. **Depends on US3.**

### Tests (write first)
- [ ] T044 [P] [US4] Tests in `server/tests/test_uploads.py`: magic-byte detection for PNG/JPEG/PDF; renamed `.exe` → 415; 2 MB + 1 byte → 413; filename sanitized
- [ ] T045 [P] [US4] Tests in `server/tests/test_tickets.py`: create ticket with 0–3 own unlinked attachments → 201 + staff email with files and user reply-to; 4 ids, foreign or already-linked id → 422; other company's ticket/attachment → 404; `ticket-status` CLI changes status shown in `/api/me`

### Implementation
- [ ] T046 [US4] Add `Ticket` and `Attachment` models in `server/app/models.py` and migration `server/migrations/versions/0004_tickets.py`
- [ ] T047 [US4] Implement `server/app/uploads.py` (size limit, magic-byte sniffing, filename sanitizing)
- [ ] T048 [US4] Implement `server/app/routes/tickets.py`: `POST /api/attachments`, `GET /api/attachments/{id}`, `POST /api/tickets` (staff email with attachments via `google.send_email`), and add tickets to `GET /api/me`
- [ ] T049 [US4] Add CLI `ticket-status`, `list tickets`, and unlinked-attachment cleanup to `cleanup` in `server/app/cli.py`
- [ ] T050 [US4] Update `SupportTicketForm` in `src/VisionHomePage.jsx`: file input (accept png/jpeg/pdf, max 3, client-side size check), upload each file then create ticket, per-file errors; ticket list with status and download links; copy in es/en/fr in `src/translations.js`

**Checkpoint**: quickstart step 4 passes → **PR 4** (`Closes #8`, `Closes #10`).

---

## Phase 7: Polish & cross-cutting (in the PR where each becomes true)

- [ ] T051 [P] Update `docs/architecture/SDD.md` §2 (stack), §4 (routes), §11 (closed gaps), §14 (portal is real; replace §14.8 table)
- [X] T052 [P] Add `GOTCHA.md` entries: Google OAuth "Testing" status expires refresh tokens after 7 days; Vercel previews call the production API
- [X] T053 [P] Add `CLAUDE.md` trap: emails to visitor-supplied addresses never echo free text (R10)
- [ ] T054 Run `quickstart.md` end-to-end on the Vercel preview and record results in each PR's test plan
- [ ] T055 Run `/ponytail-review` and `/security-review` on each PR diff before marking it ready

---

## Dependencies & execution order

- Phase 1 → Phase 2 → US1 (PR 1).
- US2 and US3 depend only on Phase 2; they can proceed in either order after PR 1.
- US4 depends on US3 (accounts, sessions).
- Within a story: tests → models/migration → logic → routes → CLI → frontend.

## Parallel opportunities

- Setup: T002–T006 together.
- Phase 2: T011 alongside T007–T009.
- US1: T016, T017, T019, T022 together.
- US2: T025, T026 together; T028 while T027 migration is reviewed.
- US3: T031–T034 together; frontend T040–T042 in parallel once T039 exists.
- US4: T044, T045 together.

## Implementation strategy

1. **MVP = Phases 1–3 (US1)**: real leads arrive. Ship PR 1, verify on preview, owner merges.
2. Add US2 (PR 2) → booking.
3. Add US3 (PR 3) → accounts; simulated portal removed in the same PR so nothing fake remains.
4. Add US4 (PR 4) → tickets.
Each PR: tasks checked off in this file in the same commit (CLAUDE.md workflow step 4).
