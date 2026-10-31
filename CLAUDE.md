# CLAUDE.md

Rules for Claude in this repo. Keep this file short; details live in `docs/process/RULES.md`.
`.specify/memory/constitution.md` governs and supersedes this file where they conflict.
Adopted from the agent-foundry template.

**Read `GOTCHA.md` at the start of a task.** It holds temporary, dated operational surprises. When
you hit something new that cost time to diagnose and isn't obvious from the code, add an entry in
its format; delete entries whose *Remove when* holds. A `SessionStart` hook flags entries past their
*Review by* date — relay that to the owner.

## Project
- VeritX Vision marketing site + invite-only customer portal. Stack: React 18 + Vite 5,
  plain CSS, Vitest, Vercel (`docs/decisions/001-stack.md`). Backend (in progress, spec
  `specs/001-backend`): FastAPI + Postgres in `server/`, on Railway (`docs/decisions/002-backend-stack.md`,
  `docs/deployment/environments.md`).
- Read `docs/architecture/SDD.md` before changing content or behavior — §10 holds established
  decisions, §11 known gaps, §14 the portal.
- Frontend commands (repo root): install `npm install` · dev `npm run dev` · test `npm test` ·
  build `npm run build` · lint: none.
- Backend commands (`server/`): install `python -m venv .venv && . .venv/bin/activate && pip install
  -e '.[dev]'` · dev `uvicorn app.main:app --reload` (with `server/.env` from `.env.example`,
  `GOOGLE_FAKE=1`) · test `pytest` (needs Postgres, `TEST_DATABASE_URL`) · lint `ruff check .` ·
  migrations `alembic upgrade head` · staff CLI `python -m app.cli --help`.
- Pending work lives in GitHub issues. Reference them in PRs (`Closes #N`).

## Workflow (Spec-Driven)
1. New feature → create a spec in `specs/<NNN-name>/` (spec.md → plan.md → tasks.md) with the
   `speckit-*` skills. Small fixes (typos, copy tweaks, config, trivial bugs) need no spec.
2. ALWAYS before writing a new spec: GRILL ME (`grill-me` skill), one question at a time.
3. After a NEW spec/plan, STOP and wait for explicit confirmation before implementing.
4. Implement one task at a time, applying Ponytail; mark it done in tasks.md in the same commit.
5. If code makes spec/plan/tasks or the SDD stale, update them in the same PR.
6. Test-first is **minimal** (ADR 001): tests required for calculator formulas, `auth.js`, and any
   new pure logic; UI/copy changes are verified manually.

## Ponytail (minimal code, intensity `full`)
- Plugin is declared in `.claude/settings.json`. If missing: `/plugin marketplace add
  DietrichGebert/ponytail` then `/plugin install ponytail@ponytail`; run `/ponytail full`.
- Before writing code, climb the ladder: needed at all? already in the codebase? platform feature?
  Then write the minimum that works.
- Never cut validation, error handling, security, or accessibility for brevity.
- Run `/ponytail-review` on the diff before opening or updating a PR.
- Mark deliberate shortcuts with `shortcut:` comments; `/ponytail-debt` lists them.

## Repository layout

```
CLAUDE.md, README.md, GOTCHA.md   Root docs (the only docs at the root)
src/                              App code; *.test.js next to the code they test
public/                           Static assets
.specify/ .claude/ .github/       Spec Kit, Claude settings/hooks/skills, CI + templates
specs/NNN-feature-name/           Spec Kit artifacts (sequential numbering, no gaps)
docs/                             README.md (index); process/ decisions/ architecture/
                                  deployment/ runbooks/ audits/YYYY-MM-DD/
```

Every document lives in a `docs/` subfolder; every new one gets a row in `docs/README.md`.

## Traps worth knowing
- All user-facing copy lives in `src/translations.js` in **three** languages (es/en/fr). A copy
  change must update all three.
- Every page route is a `#/...` hash fragment; don't add path-based routes. The only server path is
  `/api/*`, rewritten by `vercel.json` to Railway (and proxied by Vite in dev) so the API is same-origin.
- The contact form, calculator results, meeting booking and portal accounts are real (backend
  Stories 1–3). Only the Vision Home support-ticket form is still client-only until Story 4.
- Portal accounts are invite-only (staff CLI); there is no self-registration — don't add one
  without a spec.
- Emails to visitor-supplied addresses must never echo text the visitor typed (name, company,
  message); only fixed copy and numbers. Otherwise the forms become a spam relay
  (`server/app/emails.py`, test `server/tests/test_emails.py`).
- Don't fabricate URLs (LinkedIn, Vercel, etc.); ask the owner.

## Git & PRs
- Work only on the session's `claude/<reason>` branch; never push to `main`. No force-push.
- Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`); body explains why.
- Delete a branch only after `git merge-base --is-ancestor <branch> main` succeeds.
- Open a PR only when asked. Then: draft, use `.github/pull_request_template.md`, subscribe to its
  activity, and fix CI failures and review comments until green. Never skip a test or push an
  empty commit to get green.

## Communication
- Be concise and direct. Ask clarifying questions when the request is ambiguous.
- Report outcomes faithfully: failing tests or skipped steps must be stated.

## Never
- Commit secrets, `.env` files, or credentials.
- Skip, disable, or delete tests to get green.
- Rewrite history on shared branches or force-push.
- Add dependencies or change the stack without a decision record in `docs/decisions/`.
- Take outward-facing or hard-to-reverse actions (deploys, deletes, publishing) without
  confirmation.

## Deployment
- Frontend: Vercel — preview per PR, production on merge to `main` (owner approves the merge).
- Backend (future): Railway. Production deploys only with the owner's approval.
