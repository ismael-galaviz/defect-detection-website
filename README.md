# VeritX Vision — Website

Trilingual (Spanish/English/French) marketing website for VeritX Vision, an AI-powered fabric defect
detection system for textile manufacturers. Includes a client-only simulated customer portal (login,
registration, recovery, account dashboard) — see `docs/architecture/SDD.md` §14 for what's real versus
simulated.

- Technical/design record: [`docs/architecture/SDD.md`](docs/architecture/SDD.md)
- Docs index: [`docs/README.md`](docs/README.md) · Claude rules: [`CLAUDE.md`](CLAUDE.md)
- Pending work: [GitHub issues](https://github.com/ismael-galaviz/defect-detection-website/issues)

## Stack

React 18 + Vite 5, plain CSS, Vitest. No backend yet — the contact form, appointment booking and
customer portal are client-only prototypes. The future backend will be hosted on Railway (issue #8). Rationale: [`docs/decisions/001-stack.md`](docs/decisions/001-stack.md).

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
demo footage and validated specs — see `docs/architecture/SDD.md` §11. Treat the customer portal as a
UI/UX demo, not a real auth system.
