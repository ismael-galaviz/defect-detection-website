# Stack decision

Questionnaire to run at the start of every project (already answered for this repo: see *Stack chosen*).
Claude asks **one question at a time** (grill-me style), presents the options **neutrally**
(no recommendation unless the owner asks), and records the outcome as a single ADR:
`docs/decisions/001-stack.md`.

Options are examples, not a closed list: "Other" is always valid.

## Questions

| # | Area | Question | Options (examples) |
| --- | --- | --- | --- |
| 1 | Project type | What are we building? | Web app, API only, agent/AI app, CLI, mobile app, library |
| 2 | Where it's used | On which devices/environments will it run or be used? | Phone, tablet, computer, browser, headless/server, embedded, several |
| 3 | Frontend | Which framework, if any? | Next.js, React + Vite, SvelteKit, Astro, native/mobile toolkit, none |
| 4 | Backend | Which runtime/framework, if any? | Framework API routes, Node (Fastify/Express), Python (FastAPI), .NET, Go, none |
| 5 | Database | Which store, if any? | Postgres, SQLite, MongoDB, key-value, none |
| 6 | Auth | How do users sign in? | Auth provider, custom, none |
| 7 | Deploy | Where does it run? | Vercel, Railway, container host, self-hosted, store distribution |
| 8 | AI / agents | Does it call LLMs? | Claude API / Agent SDK, other provider, none |
| 9 | Quality tools | Test, lint and format tools? | Derived from the stack; confirm with the owner |
| 10 | Test-first | Is test-first required? | Required (default), minimal (critical paths only), none (throwaway prototype) |

Question 2 can change the rest (for example, "phone" may rule out a headless-only design,
"headless" removes the frontend). Re-check earlier answers when it does.

## Procedure
1. Ask the questions in order; skip those a previous answer made irrelevant.
2. For each answer, state the trade-off in one line (cost, complexity, lock-in).
3. For question 10, record the level and the reason in the ADR; if not "required", say what replaces tests (manual checks, smoke test).
4. Apply the Ponytail ladder to the final set: is each piece needed, and is there a simpler one?
5. Write `docs/decisions/001-stack.md` from `docs/decisions/000-template.md`.
6. Fill the table below and the *Commands* section of `CLAUDE.md`.
7. Add the stack's CI jobs to `.github/workflows/ci.yml`.
8. Specialize `.specify/memory/constitution.md` for the chosen stack.

## Stack chosen

| Area | Choice |
| --- | --- |
| Project type | Marketing website + client-only simulated portal |
| Devices / environments | Browser (phone, tablet, desktop) |
| Frontend | React 18 + Vite 5 |
| Backend | None |
| Database | None |
| Auth | None (simulated in `localStorage`) |
| Deploy | Vercel |
| AI / agents | None |
| Quality tools | Vitest |
| Test-first | minimal |

ADR: [`docs/decisions/001-stack.md`](../decisions/001-stack.md)
