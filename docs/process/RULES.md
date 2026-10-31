# Rules

How we work in this repo (from the agent-foundry template). Claude-specific rules: [`CLAUDE.md`](../../CLAUDE.md).

## 1. Adoption
This repo adopted the agent-foundry template retroactively (2026-10-31). The stack is recorded in
[`docs/decisions/001-stack.md`](../decisions/001-stack.md); pending work lives in GitHub issues.

## 2. Workflow
- New feature → grill-me → `/speckit-specify` → clarify → plan → tasks → implement.
- A new spec needs the owner's confirmation before implementation starts.
- Small fixes (typos, config tweaks, trivial bugs) skip the spec.
- Keep code minimal (Ponytail, `full`). Justify any new dependency or abstraction in the plan.

## 3. Branches
- `main` is permanent: no direct commits, no force-push, never deleted.
- One branch per task, named `claude/<reason>` (short kebab-case: `claude/add-login-flow`).
  Claude works on the branch the session assigns; Spec Kit only creates `specs/NNN-name/`.
- The spec directory keeps its number (`specs/NNN-name/`); the branch does not.
- Delete a branch only after `git merge-base --is-ancestor <branch> main` succeeds.

## 4. Commits
- Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`.
- One logical change per commit; the body explains why.
- Never rewrite shared history.

## 5. Pull requests
- Only when requested. Opened as draft, using the PR template.
- Reference the spec and tasks it implements.
- Merge only when CI is green and the owner approves.

## 6. Quality gates
- Tests before code for critical pure logic (constitution, Principle II at the "minimal" level, ADR 001).
- No skipped or deleted tests to get green.
- No secrets in the repo; config via environment variables.

## 7. Docs organization
- Every document lives in a subfolder of `docs/`; only the index (`docs/README.md`) sits at the top.
- Every new document gets a row in `docs/README.md`.
- Lasting decisions → `docs/decisions/NNN-title.md` (copy `000-template.md`).
- Audits → `docs/audits/YYYY-MM-DD/`; runbooks → `docs/runbooks/`.
- Temporary operational surprises → `GOTCHA.md` (with a Review-by date).
- Code, tests and skills cite docs by path: moving a doc means updating them too.

## 8. Deploy
- Vercel only: preview per PR, production on merge to `main` with the owner's approval.
