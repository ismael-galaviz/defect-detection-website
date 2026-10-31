# 001. Stack, deploy target and test-first level

- Status: accepted
- Date: 2026-10-31

## Context

The site predates the agent-foundry workflow; this ADR records the existing stack retroactively and
the two changes made while adopting it. GitHub Pages and Vercel both deployed from `main`, but the
Pages build used a `/defect-detection/` base path while the repo is now `defect-detection-website`,
so Pages was serving broken assets. There were no tests.

## Decision

| Area | Choice |
| --- | --- |
| Project type | Marketing website + client-only simulated customer portal |
| Devices | Browser: phone, tablet, desktop (responsive) |
| Frontend | React 18 + Vite 5, plain CSS, hash routing |
| Backend / DB / Auth | None — `auth.js` simulates auth in `localStorage` (SDD §14.8) |
| Deploy | **Vercel only** (preview per PR, production on `main`). GitHub Pages dropped. |
| AI / agents | None in the site |
| Quality tools | Vitest; no linter yet |
| Test-first | **Minimal** — see below |

**Test-first: minimal.** Tests are required for pure logic where a bug is silent and costly: the ROI
calculator formulas (`CALC`) and `auth.js` (validation, verify-before-login, lockout), plus any new
pure logic. UI and copy changes are verified manually (and on the Vercel preview). Reason: the site is
mostly static content; full test-first would cost more than it catches.

## Consequences

- One deploy target; `vite.config.js` no longer needs a `VERCEL`-conditional base.
- CI (`.github/workflows/ci.yml`) runs `npm test` and `npm run build` on every PR.
- A real backend (contact form, bookings, portal) needs its own ADR before work starts.
