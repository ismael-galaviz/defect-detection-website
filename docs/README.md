# Docs

Where each document lives and what it is for. `CLAUDE.md` (repo guide), `GOTCHA.md` (dated
operational surprises) and `README.md` stay at the root; feature specs live in `specs/`; pending work
lives in GitHub issues.

| Path | What it is |
| --- | --- |
| [`process/RULES.md`](process/RULES.md) | How we work: workflow, branches, commits, PRs, docs organization |
| [`process/STACK-DECISION.md`](process/STACK-DECISION.md) | Stack questionnaire and the stack chosen |
| [`decisions/`](decisions/000-template.md) | Architecture decision records (`NNN-title.md`) |
| [`decisions/001-stack.md`](decisions/001-stack.md) | Stack, deploy target and test-first level |
| [`architecture/SDD.md`](architecture/SDD.md) | Full technical/design record of the site and portal |
| [`architecture/*.drawio`](architecture/) | Architecture/container diagrams (draw.io) |
| `deployment/` | Environments and every environment variable (none today) |
| `runbooks/` | Operational procedures |
| `audits/` | Audit reports, one folder per `YYYY-MM-DD` |

Every document lives in a subfolder; only this index sits at the top of `docs/`. Code, tests,
skills and specs cite docs by path, so a move updates them too. Add a row here for any new document.
