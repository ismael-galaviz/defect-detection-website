---
name: grill-me
description: Clarify and challenge software requirements before writing or modifying code. Use when a task is ambiguous, underspecified, architectural, or likely to require significant implementation. Do not write production code until critical requirements, constraints, edge cases, and acceptance criteria are understood.
---

# Grill Me

## Purpose

Before implementing a software task, interrogate the requirements until there is enough information to implement the solution without making important undocumented assumptions.

The goal is not to ask every possible question.

The goal is to identify questions whose answers could materially change:

- architecture
- API design
- database schema
- business logic
- security
- UX
- infrastructure
- dependencies
- implementation strategy
- acceptance criteria

---

# Core Rule

Do NOT start coding immediately when this skill is active.

First:

1. Understand the requested outcome.
2. Inspect the existing project when relevant.
3. Identify ambiguity and hidden assumptions.
4. Ask targeted questions.
5. Resolve the important decisions.
6. Produce a concise implementation specification.
7. Get confirmation when the decisions materially affect the implementation.
8. Only then implement.

Do not ask questions whose answers can be determined safely by inspecting the repository.

---

# Step 1 — Understand the request

Extract:

- Objective
- User/persona
- Expected behavior
- Scope
- Constraints
- Existing components involved
- Expected output

Rewrite the request internally as:

> "The system must..."

If this statement cannot be written clearly, ask for clarification.

---

# Step 2 — Inspect before asking

Before asking questions, inspect the repository when access is available.

Look for:

- architecture
- existing patterns
- relevant files
- APIs
- database models
- authentication
- configuration
- tests
- CI/CD
- documentation
- similar existing functionality

Prefer repository evidence over asking the user.

Example:

Bad question:

> "Do you use PostgreSQL?"

If the repository clearly contains PostgreSQL configuration, do not ask.

Instead:

> "The project currently uses PostgreSQL. Should this feature use the existing database?"

---

# Step 3 — Grill the requirements

Ask questions in priority order.

## A. Business behavior

Determine:

- What should happen?
- What should NOT happen?
- Who can perform the action?
- What are the important business rules?
- What happens in exceptional cases?

## B. Scope

Determine:

- What is explicitly included?
- What is explicitly excluded?
- Is this an MVP or production-ready implementation?
- Should existing behavior change?

## C. Data

Determine:

- What entities are involved?
- What fields are required?
- What relationships exist?
- What validation is required?
- What happens to existing data?
- Are migrations required?

## D. API / interfaces

Determine:

- Inputs
- Outputs
- HTTP methods
- Status codes
- Error format
- Authentication
- Authorization
- Backward compatibility

## E. UX

For UI-related tasks determine:

- User flow
- Empty states
- Loading states
- Error states
- Validation
- Responsive behavior
- Accessibility
- Existing design system

## F. Security

Consider:

- Authentication
- Authorization
- Input validation
- Sensitive data
- Secrets
- Injection
- Rate limiting
- Audit requirements

Do not introduce unnecessary security complexity, but explicitly identify meaningful risks.

## G. Performance / scale

Ask only when relevant:

- Expected traffic
- Data volume
- Latency requirements
- Concurrent users
- Background processing
- Caching requirements

## H. Operations

Determine when relevant:

- Logging
- Metrics
- Monitoring
- Deployment
- Rollback
- Configuration
- Feature flags

---

# Step 4 — Challenge assumptions

For every important assumption, determine whether it is:

1. Explicitly stated
2. Evident from the repository
3. A reasonable convention
4. Unknown and potentially important

Only category 4 should normally become a question.

Use questions such as:

> "I see X in the existing implementation. Should the new feature follow the same pattern?"

or:

> "There are two reasonable behaviors here. Which should we use?"

Avoid vague questions such as:

> "Any preferences?"

---

# Step 5 — Ask questions efficiently

Do not overwhelm the user with 20 questions.

Ask the smallest set of questions that resolves the highest-risk ambiguity.

Prefer grouped questions:

### Behavior

1. Should deleting an asset be permanent or soft-delete?
2. Should users be able to restore deleted assets?

### Permissions

3. Should all authenticated users be able to delete assets, or only administrators?

If one answer determines several other decisions, ask that question first.

---

# Step 6 — Detect contradictions

If requirements conflict, explicitly identify the conflict.

Example:

> You said the asset must be unique by serial number, but you also want historical records to retain the old serial number after reassignment. These requirements conflict unless uniqueness is scoped to active assets.

Then ask for the intended behavior.

Never silently choose a business rule.

---

# Step 7 — Produce the specification

Once the important questions are resolved, produce:

## Implementation Specification

### Objective

...

### Scope

Included:
- ...

Excluded:
- ...

### Behavior

...

### Data model

...

### API / interfaces

...

### UI

...

### Security

...

### Edge cases

...

### Acceptance criteria

- [ ] ...
- [ ] ...
- [ ] ...

### Technical approach

...

### Files/components expected to change

...

### Open decisions

None.

---

# Step 8 — Confirmation threshold

Ask for confirmation before coding when the unresolved decision could materially change the implementation.

Examples:

- database schema changes
- public API changes
- authentication/authorization
- destructive operations
- architectural changes
- external integrations
- significant UX behavior

For low-risk tasks, proceed once requirements are sufficiently clear.

Do not ask for confirmation merely to be bureaucratic.

---

# Step 9 — Implementation

After requirements are sufficiently clear:

1. Implement the smallest coherent solution.
2. Follow existing project conventions.
3. Avoid unrelated refactoring.
4. Add or update tests.
5. Run relevant validation.
6. Report what changed.
7. Report any assumptions that remained.

---

# Question Quality Rules

Every question should satisfy:

- It has a meaningful impact on implementation.
- The answer cannot reliably be inferred.
- It is understandable without technical context when possible.
- It has a clear set of possible answers.

Prefer:

> "Should deleting an asset remove it permanently, or should it remain recoverable?"

Avoid:

> "What deletion strategy do you prefer?"

---

# Anti-patterns

Do NOT:

- ask questions that repository inspection can answer
- ask questions merely to appear thorough
- block simple tasks unnecessarily
- redesign unrelated parts of the application
- invent business requirements
- silently choose between conflicting business rules
- start implementing while critical requirements remain unresolved
- generate speculative architecture before understanding the problem

---

# Output Style

Be concise.

Use tables when comparing decisions.

For unresolved decisions use:

| Decision | Option A | Option B | Impact |
|---|---|---|---|

For questions, number them.

After the requirements are resolved, clearly state:

> Requirements clarified. Ready to implement.

Then proceed with implementation when appropriate.
