<!--
Sync Impact Report
==================
Version change: 1.0.0 -> 1.1.0 (adopted in defect-detection-website; specialized for its stack)

Modified principles: N/A (initial adoption)
Added sections:
  - Core Principles: I. Simplicity First (YAGNI), II. Test-First Development (NON-NEGOTIABLE unless opted out in ADR 001),
    III. Modular & Independently Testable Components, IV. Observability & Debuggability,
    V. Versioning & Breaking-Change Discipline, VI. Spec Before Code
  - Quality & Security Standards
  - Development Workflow & Review Process
  - Governance
Removed sections: none

Templates requiring updates:
  - .specify/templates/*: Constitution Check gate is generic; no edits needed.

Follow-up TODOs: none. Principle II applies at the "minimal" level per ADR 001. Principle V applies
  only to persisted formats (localStorage keys in src/auth.js) until a public API exists.
-->

# VeritX Vision Website Constitution

## Core Principles

### I. Simplicity First (YAGNI)

Every feature MUST start with the simplest design that satisfies its actual, current
requirements. New abstractions, dependencies, services, or layers of indirection MUST be
justified in writing (in the PR description or plan's Complexity Tracking table) before they
are introduced. Do not build for hypothetical future requirements.

**Rationale**: Unjustified complexity is the leading source of long-term maintenance cost and
defect surface area. Simplicity keeps the system legible to both humans and agents working on it.

### II. Test-First Development (NON-NEGOTIABLE unless opted out in ADR 001)

Unless the owner opts out in `docs/decisions/001-stack.md` (see `docs/process/STACK-DECISION.md`,
question 10), tests MUST be written before implementation for all new behavior, and MUST fail
before the corresponding code is written (Red-Green-Refactor). No change MAY be merged to the main
branch without automated tests covering the new or modified behavior.

If the owner opts out, ADR 001 MUST state the level chosen (none or minimal) and why, and this
principle applies only to that extent.

**Rationale**: Test-first development forces requirements to be explicit before code exists,
and provides a regression safety net that allows the codebase to change confidently over time.
Opting out is a conscious, recorded trade-off (for example a throwaway prototype), never a default.

### III. Modular & Independently Testable Components

Every feature MUST be organized into self-contained units (modules, libraries, services, or
functions) with a single clear purpose and a well-defined contract. Each unit MUST be testable
in isolation, without requiring the full system to be running. Purely organizational units with
no independent purpose or contract are not permitted.

**Rationale**: Independently testable components keep feedback loops short, make failures easy
to localize, and allow the system to be understood and changed one piece at a time.

### IV. Observability & Debuggability

Components MUST emit structured, inspectable logs and errors sufficient to diagnose failures
without attaching a live debugger. Prefer text-based, greppable I/O and structured logging over
opaque binary or in-memory-only state. Error messages MUST include enough context (what failed,
with what input, in what unit) to locate the cause.

**Rationale**: Systems fail in production and in CI, not just in the debugger. Observability
built in from the start is far cheaper than observability retrofitted after an incident.

### V. Versioning & Breaking-Change Discipline

All public interfaces (APIs, CLIs, schemas, data formats) MUST follow semantic versioning
(MAJOR.MINOR.PATCH). Breaking changes MUST be documented with a migration path and MUST bump the
MAJOR version. Additive, backward-compatible changes bump MINOR; fixes and clarifications bump
PATCH.

**Rationale**: Predictable versioning lets consumers of an interface (including other parts of
this project) upgrade safely and lets the team reason about compatibility without inspecting
implementation details.

### VI. Spec Before Code

Every new feature MUST start from a specification (`specs/NNN-name/`). Before a new spec is
written, requirements MUST be clarified with the owner (grill-me); after a new spec and plan,
implementation MUST NOT start until the owner confirms. Small fixes (typos, config tweaks,
trivial bugs) are exempt. Code that makes the spec, plan or tasks stale MUST update them in the
same change.

**Rationale**: Resolving ambiguity before code exists is cheaper than rewriting code built on
unstated assumptions, and keeps humans and agents aligned on what "done" means.

## Quality & Security Standards

All code MUST pass the CI checks (tests, build; lint/type-check once configured) before merge.
User-facing copy MUST exist in all three site languages (es/en/fr). Features that only simulate
backend behavior MUST say so in the UI and in `docs/architecture/SDD.md`. Secrets, credentials, and API keys MUST NOT be committed to the repository; use
environment variables or a secrets manager instead. Changes touching authentication,
authorization, or personal/sensitive data handling MUST be flagged in the PR description for
focused security review, and MUST NOT introduce common OWASP Top 10 classes of vulnerability
(e.g., injection, broken access control, insecure deserialization).

## Development Workflow & Review Process

All changes MUST go through review before merging to the main branch — self-merges of
non-trivial changes are not permitted. When the Spec Kit workflow is in use, PRs SHOULD
reference the spec and/or task(s) they implement. Automated checks (tests, lint, type-checks)
MUST pass before a change is merged. Reviewers MUST verify compliance with the Core Principles
above as part of review, not only functional correctness.

## Governance

This constitution supersedes all other development practices and guidance documents for this
project when they conflict. Amendments require: (1) a documented rationale for the change,
(2) an update to this file with a version bump following the semantic versioning rules below,
and (3) a propagation review of dependent templates (plan, spec, tasks, checklist) and any
runtime guidance docs to keep them consistent with the amended principles.

**Versioning policy**: CONSTITUTION_VERSION follows MAJOR.MINOR.PATCH:
- MAJOR: Backward-incompatible governance changes, or removal/redefinition of a principle.
- MINOR: A new principle or section is added, or existing guidance is materially expanded.
- PATCH: Clarifications, wording fixes, and other non-semantic refinements.

All PRs and reviews MUST verify compliance with this constitution. Any complexity introduced in
violation of Principle I (Simplicity First) MUST be explicitly justified in the PR description
or rejected. Use CLAUDE.md (or an equivalent agent-guidance file), when present, for day-to-day
runtime development guidance that supplements — but never overrides — this constitution.

**Version**: 1.1.0 | **Ratified**: 2026-10-08 | **Last Amended**: 2026-10-31
