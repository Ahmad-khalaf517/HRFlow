# HRFlow Web-AI Context Prompt

Paste this into a new ChatGPT or Claude conversation, followed by one completed task brief and only the relevant sanitized files.

```text
You are assisting with HRFlow, a seven-calendar-day HR and payroll MVP built as a Django monolith.

Required flow:
Employee -> Contract -> Attendance/Leave -> Payroll -> Payslip -> Payment

Stack:
- Python 3.12+, Django 5.x, PostgreSQL
- Django Templates and Tailwind CSS
- Alpine.js/HTMX only for a necessary small interaction
- pytest, pytest-django, and Ruff
- apps: accounts, employees, attendance, payroll

Binding rules:
- Keep the solution deliberately small and within the supplied task brief.
- Use Decimal/DecimalField for money; never use float.
- Attendance stores facts/hours; payroll converts approved facts into money.
- Only one active contract may exist per employee.
- Only one attendance row may exist per employee and local work date.
- PayrollItem is an immutable historical snapshot.
- Approved payroll cannot be recalculated or edited normally.
- Employees may access only their own private records and payslips.
- Enforce permissions server-side and at object level.
- Use synthetic data only.
- Do not add proration, complex shifts/leave, legal compliance, correction runs, partial payments, integrations, a large frontend framework, or unrelated refactors.

Do not invent payroll, tax, leave, security, or permission policy. If the supplied business-rules decision table marks a relevant item Pending, identify its ID and stop the affected implementation.

First response—do not write code yet. Return:
1. your understanding of the outcome;
2. binding rules and acceptance criteria;
3. files/interfaces received;
4. contradictions, missing context, or pending decisions;
5. a minimal implementation and test plan.

After approval:
- change only allowed files;
- preserve canonical names and public interfaces;
- add required validation, permissions, constraints, migrations, and tests;
- keep views thin and business logic in services;
- do not fabricate files or claim to run commands;
- return a unified diff or complete changed files;
- finish with local commands to run, assumptions, and risks.
```

Use a new conversation for each bounded task. Review every generated change and command before applying it locally.
