# VeritX Vision — Website

Trilingual (Spanish/English/French) marketing website for VeritX Vision, an AI-powered fabric defect
detection system for textile manufacturers, with an invite-only customer portal (Vision Home) — see
`docs/architecture/SDD.md` §14.

- Technical/design record: [`docs/architecture/SDD.md`](docs/architecture/SDD.md)
- Docs index: [`docs/README.md`](docs/README.md) · Claude rules: [`CLAUDE.md`](CLAUDE.md)
- Pending work: [GitHub issues](https://github.com/ismael-galaviz/defect-detection-website/issues)

## Stack

React 18 + Vite 5, plain CSS, Vitest. Backend: FastAPI + Postgres in `server/`, on Railway
([`docs/decisions/002-backend-stack.md`](docs/decisions/002-backend-stack.md)) — contact form,
calculator results, meeting booking and portal accounts. Rationale: [`docs/decisions/001-stack.md`](docs/decisions/001-stack.md).

## Commands

```bash
npm install
npm run dev       # dev server
npm test          # Vitest
npm run build     # production build to dist/
```

## Workflow

Spec-driven with agent-foundry conventions (see `CLAUDE.md` and `docs/process/RULES.md`): work on a
`claude/<reason>` branch, open a draft PR, CI must be green. No direct commits to `main`.

## Deploy

Frontend on Vercel, via Vercel's git integration: every PR gets a preview, merging to `main` deploys
production. No `vercel.json` needed — Vite is auto-detected and routes are `#/...` hash fragments.

## Notes

Marketing content (specs, comparisons, hero copy) is placeholder pending real product photography,
demo footage and validated specs — see `docs/architecture/SDD.md` §11.
