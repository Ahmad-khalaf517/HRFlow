# HRFlow AI Context

Use this file as the first context supplied to any AI assistant working on this repository. It is intentionally short. Detailed rules live in the linked documents and in the current task brief.

## Instruction Priority

When instructions conflict, use this order:

1. The current human request and approved task brief.
2. This file.
3. Approved decisions in `docs/decisions/` and confirmed rules in `docs/business-rules.md`.
4. Existing code, tests, and public service interfaces.
5. Other project documentation.

Do not resolve a conflict silently. Report it before changing code.

## Product and Scope

HRFlow is a focused HR and payroll Django MVP. The primary goal is one reliable flow:

```text
Employee -> Contract -> Attendance/Leave -> Payroll -> Payslip -> Payment
```

Recruitment, performance management, biometric integration, bank APIs, multi-company tenancy, multi-country compliance, and advanced accounting are outside the MVP.

This repository is currently a design specification. Keep the implementation deliberately small. The four unresolved items in `docs/open-questions.md` must not be invented during implementation.

## Technology and Architecture

- Python 3.12+
- Django 5.x
- PostgreSQL
- Django Templates and Tailwind CSS
- Alpine.js only for small interactions
- HTMX only where it clearly reduces complexity
- pytest and pytest-django

Primary Django apps:

```text
accounts
employees
attendance
payroll
```

Do not add another primary app without explicit approval.

## Canonical Domain Names

```text
Department
Position
Employee
Contract
Attendance
LeaveType
LeaveRequest
Bonus
ManualDeduction
TaxBracket
Payroll
PayrollItem
Payslip
Payment
```

Do not rename these or introduce synonyms for them without an approved decision.

## Non-Negotiable Invariants

- Use `Decimal` and `DecimalField` for money; never use binary floating point.
- Attendance stores work facts and hours, not monetary amounts.
- Payroll services translate approved HR facts into money.
- A `PayrollItem` is a historical snapshot. Old payslips never use current contract values.
- Approved payroll cannot be recalculated or edited through normal flows.
- One employee may have contract history, but only one contract may be active.
- One attendance record exists per employee and local work date.
- Employees may access only their own private HR and payslip data.
- Every privileged workflow must enforce authorization on the server, not only in navigation or templates.
- Model changes require migrations and constraint tests.
- Payroll status changes use explicit service operations and record the responsible user/timestamp.
- Do not expand the MVP with proration, legal compliance, complex shifts/leave, correction runs, partial payments, or separation-of-duties workflows.

## Dependency Direction

```text
accounts -> employees -> attendance -> payroll
```

Payroll should consume attendance through public service functions. Avoid circular imports and duplicated business logic.

## Change Rules

Before editing:

1. Read this file, the task brief, relevant approved decisions, existing implementation, and related tests.
2. Restate the goal, constraints, files in scope, and unresolved questions.
3. Stop if an unresolved business decision would materially affect the result.

While editing:

- Keep the diff bounded to the task.
- Preserve existing architecture and terminology.
- Do not refactor unrelated code.
- Add database constraints where they protect an invariant.
- Keep views thin and calculations in services.
- Never expose secrets, credentials, or real employee/payroll data.

Before completion:

- Run targeted tests and report the exact commands and results.
- Inspect the diff for unrelated changes and sensitive data.
- Report assumptions, risks, migrations, and manual checks.
- Never claim a test or command was run when it was not.

## Definition of Done

A change is done only when:

- acceptance criteria pass;
- validation and permissions are enforced;
- migrations are included when needed;
- relevant automated tests pass;
- the affected workflow is manually reviewable;
- documentation is updated when behavior or an interface changed;
- the diff has been human-reviewed before merge.

## Data Safety

Follow `docs/security-and-data-policy.md`. Consumer web AI tools may receive only approved, sanitized context. Never upload real employee records, salaries, bank information, leave reasons, credentials, production logs, database dumps, or private keys.

## Required References

- Business rules: `docs/business-rules.md`
- Unresolved decisions: `docs/open-questions.md`
- Security and AI data policy: `docs/security-and-data-policy.md`
- Testing strategy: `docs/testing-strategy.md`
- AI-assisted workflow: `docs/ai-agent-guide.md`
- Task template: `docs/task-brief-template.md`
