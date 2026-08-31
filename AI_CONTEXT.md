# HRFlow AI Context

Read this file before changing the repository. HRFlow is a seven-calendar-day Django HR/payroll MVP that uses synthetic data only.

## Required outcome

```text
Employee -> Contract -> Attendance/Leave -> Payroll -> Payslip -> Payment
```

When instructions conflict, use this priority:

1. the current human-approved task brief;
2. this file;
3. confirmed rules in `docs/business-rules.md`;
4. existing code, public interfaces, and database constraints;
5. other documentation.

Report conflicts instead of resolving them silently.

## Locked architecture

- Python 3.12+, Django 5.x, and PostgreSQL hosted by Supabase.
- Supabase is the database host only; authentication uses Django `User`, `Group`, password hashing, and database sessions.
- Django Templates and Tailwind CSS 4; Alpine.js or HTMX only for a specific small interaction.
- Ruff and pytest/pytest-django.
- Primary apps: `accounts`, `employees`, `attendance`, `payroll`.
- Dependency direction: `accounts -> employees -> attendance -> payroll`.
- Django migrations are the only executable schema source of truth.

Do not add another primary app, a large frontend framework, a second authentication system, or a parallel SQL schema without approval. Payroll consumes attendance only through public service functions.

## Current baseline

The repository currently contains authentication, the dashboard shell, all initial domain models/migrations, Django Admin registrations, the shared design system, and foundational tests. Custom employee, attendance, leave, payroll, payslip, payment, service, and object-permission workflows are not complete.

The current migrated domain models are:

- `employees`: `Department`, `Position`, `Employee`, `Contract`;
- `attendance`: `Attendance`, `LeaveType`, `LeaveRequest`;
- `payroll`: `Bonus`, `ManualDeduction`, `TaxBracket`, `Payroll`, `PayrollItem`, `Payslip`, `Payment`.

`Payslip` currently stores optional generated-file metadata, while payroll values must come from the saved `PayrollItem` snapshot.

## Non-negotiable target rules

- Use `Decimal`/`DecimalField` for money; never use `float`.
- Attendance stores facts and hours, never money.
- At most one active contract may exist per employee.
- At most one attendance row may exist per employee and local work date.
- `PayrollItem` is intended to be an immutable historical snapshot.
- Approved payroll cannot be recalculated or edited normally.
- Employees may access only their own private records and payslips.
- Enforce permissions server-side and at object level.
- Status transitions use services and record actor/time.
- Model changes require migrations and appropriate database constraints.
- Use synthetic data only.
- Do not add proration, complex shifts/leave, legal compliance, correction runs, partial payments, integrations, or separation-of-duties workflows.

The decision table in `docs/business-rules.md` is authoritative. Do not implement a pending currency, rate, overtime, or leave-calendar policy. Q-002 through Q-004 currently block payroll calculation work.

## Known implementation gaps

The current migrations do not yet enforce every target rule. In particular:

- leave-request overlap prevention is not implemented;
- `Payment.payroll_item` permits multiple rows even though the target MVP rule is one full payment;
- `PayrollItem` lacks currency/calculation-version fields and database immutability enforcement;
- several nonnegative and period-consistency checks are missing;
- the four role groups are seeded, but their permissions and object-level enforcement are not assigned;
- `Payroll.currency_code` defaults to `USD` while Q-002 remains pending.

Treat `docs/erd.md` as the exact current-schema reference and `docs/business-rules.md` as the target behavior. Do not silently claim a gap is implemented; address it only inside an approved task.

## Change workflow

Before editing:

- read the task brief, relevant rules, `docs/erd.md`, and the affected implementation;
- restate the bounded outcome, allowed files, acceptance criteria, and blockers;
- stop if a pending decision materially affects the task.

While editing:

- keep the diff small and preserve names/public interfaces;
- keep views thin and put calculations/transitions in services;
- include server-side permissions, validation, tests, constraints, and migrations when required;
- keep `docs/design-system.md`, Tailwind source, and generated CSS synchronized.

Before completion:

- inspect the full diff;
- run proportionate checks and manually exercise the affected workflow;
- verify no secrets or real HR/payroll data are present;
- report exact results, assumptions, migrations, gaps, and remaining risks.

Never claim to have performed an action that was not performed.

## Required references

- Setup and current status: `README.md`
- Canonical target rules and decisions: `docs/business-rules.md`
- Exact current migration schema and gaps: `docs/erd.md`
- UI system: `docs/design-system.md`
- Scope and sequence: `docs/delivery-plan.md`
- Security and AI data handling: `docs/security-and-data-policy.md`
- Per-task scope: `docs/task-brief-template.md`
- Shareable onboarding prompt: `docs/team-ai-context-prompt.md`
