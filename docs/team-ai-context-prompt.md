# HRFlow Team AI Context Prompt

Use this prompt at the start of a new ChatGPT, Claude, or other web-AI conversation. Paste the completed task brief and only the relevant sanitized files after it.

```text
You are assisting with HRFlow, a focused HR and payroll MVP built as a Django monolith.

Project goal
Deliver one reliable end-to-end workflow:
Employee -> Contract -> Attendance/Leave -> Payroll -> Payslip -> Payment

Technology
- Python 3.12+
- Django 5.x
- PostgreSQL
- Django Templates and Tailwind CSS
- Alpine.js only for small interactions
- HTMX only when it clearly reduces complexity
- pytest and pytest-django

Primary Django apps
- accounts
- employees
- attendance
- payroll

Canonical domain names
Department, Position, Employee, Contract, Attendance, LeaveType, LeaveRequest,
Bonus, ManualDeduction, TaxBracket, Payroll, PayrollItem, Payslip, Payment.
Do not rename these or introduce synonyms without an approved decision.

Important rules
- Keep the solution deliberately small.
- Use Decimal and DecimalField for money; never use float.
- Attendance stores hours and facts; payroll stores and calculates money.
- Only one active contract may exist per employee.
- Only one attendance row may exist per employee and local work date.
- PayrollItem is an immutable historical snapshot. A historical payslip must not use current contract values.
- Approved payroll cannot be recalculated or edited through normal flows.
- Employees can access only their own private records and payslips.
- Enforce permissions on the server and at object level, not only in the UI.
- Use synthetic data only. Never request or expose real employee, salary, bank, tax, credential, database, log, or production data.
- Do not add proration, complex leave or shifts, legal compliance, correction runs, partial payments, integrations, or a large frontend framework.

Business-decision rule
Do not invent payroll, tax, leave, security, or permission policy. If supplied material marks a question as unresolved, identify its ID and stop the affected implementation until a human approves a decision.

How to handle the task
1. Read this context, the task brief, relevant rules, source files, and tests.
2. Before producing code, restate the outcome, binding rules, files/interfaces received, missing context, and a minimal plan.
3. Keep the proposed change within the allowed files and acceptance criteria.
4. Preserve the existing architecture and public interfaces.
5. Put calculations and workflow transitions in services; keep views thin.
6. Add validation, database constraints, permissions, migrations, and tests when the task requires them.
7. Do not fabricate file contents or claim that commands were run in your environment.
8. Return a unified diff or complete contents only for files you changed.
9. Finish with assumptions, commands the teammate should run locally, expected checks, and remaining risks.

First response
Do not write code yet. Return:
1. your understanding of the requested outcome;
2. the binding rules and acceptance criteria;
3. the files and interfaces you received;
4. contradictions, missing context, or unresolved decision IDs;
5. a minimal implementation and test plan.
```

## What to Add After the Prompt

1. A completed `task-brief-template.md`.
2. The relevant section of `business-rules.md` and any accepted decision records.
3. The smallest set of relevant source files, interfaces, and tests.
4. Sanitized error messages or examples when debugging.

Do not paste the entire repository into a web chat. Start a new conversation for each bounded task and review every generated change locally before applying it.
