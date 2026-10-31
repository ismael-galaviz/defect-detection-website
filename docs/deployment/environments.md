# Environments

| Part | Host | Deploys from | Notes |
|---|---|---|---|
| Frontend | Vercel | `main` (production), every PR (preview) | `vercel.json` rewrites `/api/*` to the backend |
| Backend | Railway service, root directory `server` | `main` | Postgres in the same Railway project |

Vercel rewrite destinations can't read env vars, so **previews call the production backend**
until a staging environment exists. `vercel.json` holds the placeholder `RAILWAY_SERVICE_URL`
until the Railway service exists — replace it with the service's public domain.

## Railway service settings
- Root directory: `server`
- Build: Nixpacks/Railpack detects Python from `pyproject.toml` (`pip install .`)
- Pre-deploy command: `alembic upgrade head`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers`
- Healthcheck path: `/api/health`

## Environment variables (backend)

| Variable | Required | Set by | Meaning |
|---|---|---|---|
| `DATABASE_URL` | yes | Railway: reference the Postgres service's `DATABASE_URL` as-is (`postgresql://…` is accepted) | Database connection |
| `STAFF_EMAIL` | yes | owner | Inbox that receives requests; also the Gmail sender address |
| `PUBLIC_SITE_ORIGINS` | yes | owner | Comma-separated origins allowed to send POST requests; `*` wildcards allowed, e.g. `https://defect-detection.vercel.app,https://defect-detection-*-ismael-galavizs-projects.vercel.app` (previews) |
| `SITE_URL` | yes | owner | Public site URL used in links inside emails |
| `GOOGLE_FAKE` | no | dev only | `1` = log emails/events instead of calling Google |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | yes (unless fake) | owner | OAuth client (type "Desktop app") |
| `GOOGLE_REFRESH_TOKEN` | yes (unless fake) | owner, from `python -m app.cli google-auth` | Access to Gmail send + Calendar |
| `GOOGLE_CALENDAR_ID` | no | owner | Calendar to book into (default `primary`) |

Tests read `TEST_DATABASE_URL` (CI sets it; locally defaults to
`postgresql+psycopg://postgres:dev@localhost:5432/veritx_test`).

## Google OAuth setup (one time, owner)
1. In Google Cloud Console (signed in with the VeritX Gmail account): create a project, enable
   the Gmail API and Google Calendar API.
2. OAuth consent screen: External, add the scopes `gmail.send`, `calendar.events`,
   `calendar.freebusy`, and **publish it ("In production")**. In "Testing" Google expires refresh
   tokens after 7 days. An unverified app is fine for the owner's own account.
3. Create credentials → OAuth client ID → "Desktop app"; copy the ID and secret.
4. Locally: `cd server && GOOGLE_CLIENT_ID=… GOOGLE_CLIENT_SECRET=… python -m app.cli google-auth`,
   open the printed URL, approve, copy the printed refresh token into Railway.
