# Quickstart & validation: backend v1

## Prerequisites
- Python 3.12, Node 22, a Postgres 16 (Docker: `docker run -e POSTGRES_PASSWORD=dev -p 5432:5432 postgres:16`).
- For real Google calls: the OAuth client and refresh token (research R7). Without them set
  `GOOGLE_FAKE=1` to log emails/events instead of sending.

## Run locally
```bash
cd server && python -m venv .venv && . .venv/bin/activate && pip install -e '.[dev]'
cp .env.example .env              # DATABASE_URL, GOOGLE_*, STAFF_EMAIL, PUBLIC_SITE_ORIGINS
alembic upgrade head
uvicorn app.main:app --reload     # :8000
# other terminal, repo root
npm run dev                       # Vite proxies /api → :8000
```

## Automated checks
```bash
cd server && ruff check . && pytest      # backend
npm test && npm run build                # frontend
```

## Manual validation (one per story, on a Vercel preview with GOOGLE_FAKE unset)
1. **Story 1**: send the contact form → staff inbox gets all fields; visitor gets a confirmation
   with no echoed text. Send calculator results → visitor gets the numbers. Fill the honeypot via
   devtools → success shown, nothing stored.
2. **Story 2**: block a slot in the Google Calendar → it disappears from the picker. Book a free
   slot → event with Meet link + invite. Book the same slot from a second browser → "no longer
   available".
3. **Story 3**: `cli company-add`, `cli invite`, `cli subscription-add`, `cli payment-add` → accept
   the invite, see Vision Home data. Wrong password ×5 → locked. Reset password → old session in
   another browser is signed out. `cli user-disable` → signed out.
4. **Story 4**: open a ticket with a PNG → staff email has it; a renamed `.exe` and a 3 MB file are
   rejected. `cli ticket-status` → status visible in Vision Home. A user of another company gets
   404 on the attachment URL.
