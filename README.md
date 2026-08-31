# HRFlow

HRFlow is a focused HR and payroll Django MVP with a **seven-calendar-day delivery constraint**.

The required demonstration flow is:

```text
Employee -> Contract -> Attendance/Leave -> Payroll -> Payslip -> Payment
```

## Start Here

| Document | Purpose |
|---|---|
| `docs/delivery-plan.md` | Seven-day scope, work packages, sequence, cut line, and definition of done |
| `docs/business-rules.md` | Canonical calculations, permissions, workflow rules, and pending decisions |
| `docs/erd.md` | Minimum entities, relationships, and database constraints |
| `database/neon_schema.sql` | Executable PostgreSQL schema for the HRFlow domain tables on Neon |
| `docs/security-and-data-policy.md` | Application security and safe use of consumer web AI |
| `AI_CONTEXT.md` | Short repository context and non-negotiable rules for coding agents |
| `docs/team-ai-context-prompt.md` | Standalone prompt for teammates using web ChatGPT or Claude |
| `docs/task-brief-template.md` | Bounded task specification for one implementation change |

`AGENTS.md` and `CLAUDE.md` are intentionally tiny adapters that direct compatible coding agents to `AI_CONTEXT.md`.

## Locked Technology

- Python 3.12+ and Django 5.x
- PostgreSQL
- Django Templates and Tailwind CSS
- Alpine.js only for small interactions
- HTMX only when a specific interaction clearly benefits
- Ruff

Do not add a large frontend framework. Use Django Admin for low-value support-data management when a custom screen is not required for the demo.

## Team AI Workflow

For each task:

1. Complete `docs/task-brief-template.md`.
2. Give the AI `AI_CONTEXT.md`, the task brief, and only the relevant sanitized files.
3. Ask the AI to restate constraints and identify missing decisions before producing code.
4. Review the full diff and manually exercise the affected workflow.
5. Use a separate review pass before merge.

Never send real employee, salary, bank, tax, payment, credential, log, database, or production data to consumer web AI tools.

## Neon Schema Setup

`database/neon_schema.sql` uses Django's built-in `auth_user` table instead of creating a competing authentication system.

1. Point Django at the Neon database and run the built-in Django migrations so `public.auth_user` exists.
2. Execute `database/neon_schema.sql` in the Neon SQL Editor or through `psql`.
3. When domain models are added to Django, make their table/column definitions match this script and review the initial migrations before using `migrate --fake-initial`.

Do not run this DB-first script and normal initial domain migrations independently against the same database; they would both try to create the same tables.

## Immediate Decision Gate

The decision table at the top of `docs/business-rules.md` must be resolved before payroll calculation work begins. Until then, AI assistants and developers must not invent currency, rate, overtime, or leave-calendar policy.
