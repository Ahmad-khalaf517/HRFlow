# HRFlow AI Context

Read this file before changing the repository. HRFlow is a seven-calendar-day Django HR/payroll MVP using synthetic data.

## Goal and Priority

The required flow is:

```text
Employee -> Contract -> Attendance/Leave -> Payroll -> Payslip -> Payment
```

When instructions conflict, follow: current human request/task brief, this file, confirmed rules in `docs/business-rules.md`, existing code/tests/interfaces, then other documentation. Report conflicts instead of resolving them silently.

## Locked Architecture

- Python 3.12+, Django 5.x, PostgreSQL.
- Django Templates and Tailwind CSS.
- Alpine.js or HTMX only for a specific small interaction.
- pytest, pytest-django, and Ruff.
- Primary apps: `accounts`, `employees`, `attendance`, `payroll`.
- Dependency direction: `accounts -> employees -> attendance -> payroll`.

Do not add another primary app or a large frontend framework without approval. Payroll consumes attendance through public service functions.

## Canonical Domain Names

`Department`, `Position`, `Employee`, `Contract`, `Attendance`, `LeaveType`, `LeaveRequest`, `Bonus`, `ManualDeduction`, `TaxBracket`, `Payroll`, `PayrollItem`, `Payslip`, `Payment`.

`Payslip` is the rendered business concept; a separate database model is not required for the MVP.

## Non-Negotiable Rules

- Use `Decimal`/`DecimalField` for money; never use float.
- Attendance stores facts and hours, not money.
- One active contract may exist per employee.
- One attendance row may exist per employee and local work date.
- `PayrollItem` is an immutable historical snapshot.
- Approved payroll cannot be recalculated or edited normally.
- Employees may access only their own private records and payslips.
- Enforce permissions server-side and at object level.
- Status transitions use services and record the actor/time.
- Model changes require migrations and constraint tests.
- Use synthetic data only.
- Do not add proration, complex shifts/leave, legal compliance, correction runs, partial payments, integrations, or separation-of-duties workflows.

The decision table in `docs/business-rules.md` is authoritative. Do not implement a pending currency, rate, overtime, or leave-calendar policy.

## Change Workflow

Before editing, read the task brief, relevant rules, implementation, and tests. Restate the bounded outcome, allowed files, acceptance criteria, and blockers.

While editing, keep the diff small, preserve names/interfaces, keep views thin, put calculations/transitions in services, and avoid unrelated refactors.

Before completion, run targeted tests, inspect the full diff, check for sensitive data, and report exact results, assumptions, migrations, manual checks, and remaining risks. Never claim to have run a command that was not run.

## Required References

- Seven-day scope and sequence: `docs/delivery-plan.md`
- Canonical rules and decisions: `docs/business-rules.md`
- Minimum data design: `docs/erd.md`
- Executable PostgreSQL schema: `database/neon_schema.sql`
- Verification: `docs/testing-strategy.md`
- Security and AI data handling: `docs/security-and-data-policy.md`
- Per-task scope: `docs/task-brief-template.md`
