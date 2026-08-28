# HR & Payroll Management System Documentation

Documentation and AI-assisted delivery pack for the one-week Django MVP.

Start with [`AI_CONTEXT.md`](AI_CONTEXT.md). It defines the project invariants, document authority, safe change process, and required references.

## Files

1. `docs/project-plan.md` — scope, architecture, timeline, team plan
2. `docs/erd.md` — relational data model and Mermaid ERD
3. `docs/modules.md` — Django modules and responsibilities
4. `docs/jira-plan.md` — Jira epics, stories, dependencies, daily milestones
5. `docs/user-flows.md` — role-based and end-to-end user flows
6. `docs/business-rules.md` — canonical confirmed, proposed, and pending business rules
7. `docs/security-and-data-policy.md` — application security and safe AI-data policy
8. `docs/testing-strategy.md` — calculation, constraint, permission, and workflow testing
9. `docs/ai-agent-guide.md` — web and repository AI workflow
10. `docs/task-brief-template.md` — reusable bounded-task specification
11. `docs/open-questions.md` — decisions that must not be guessed
12. `docs/decisions/` — accepted architecture and business decision records
13. `docs/tools-and-libraries.md` — recommended free/open-source stack
14. `CLAUDE.md` and `AGENTS.md` — tool-specific entry points to `AI_CONTEXT.md`

## Important

This remains an MVP specification. Before calculation work begins, answer the blocking items in `docs/open-questions.md`, record accepted decisions, and update the related Jira acceptance criteria and tests.

Never use real employee, salary, bank, tax, payment, credential, or production data in consumer web AI tools. See `docs/security-and-data-policy.md`.
