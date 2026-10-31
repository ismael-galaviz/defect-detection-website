# CLAUDE.md

Rules for Claude in this repo. Keep this file short; details live in `docs/process/RULES.md`.
`.specify/memory/constitution.md` governs and supersedes this file where they conflict.
Adopted from the agent-foundry template.

**Read `GOTCHA.md` at the start of a task.** It holds temporary, dated operational surprises. When
you hit something new that cost time to diagnose and isn't obvious from the code, add an entry in
its format; delete entries whose *Remove when* holds. A `SessionStart` hook flags entries past their
*Review by* date — relay that to the owner.

## Project
- VeritX Vision marketing site + client-only simulated customer portal. Stack: React 18 + Vite 5,
  plain CSS, Vitest, Vercel (`docs/decisions/001-stack.md`). No backend.
- Read `docs/architecture/SDD.md` before changing content or behavior — §10 holds established
  decisions, §11 known gaps, §14 the portal.
- Commands: install `npm install` · dev `npm run dev` · test `npm test` · build `npm run build` ·
  lint: none.
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
- Every route is a `#/...` hash fragment; don't add path-based routes (Vercel has no rewrites).
- Anything "sent" (contact form, appointments, calculator results, portal emails) is simulated
  client-side. Never describe it as real.
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
- Vercel only: preview per PR, production on merge to `main` (owner approves the merge).
