# HR & Payroll Management System — AI Agent Development Guide

## 1. Purpose

This file defines how AI coding assistants should work on the project.

The goal is to increase implementation speed without allowing AI-generated code to create architectural inconsistency.

## 2. Project Context

- Django monolith
- PostgreSQL
- Django Templates
- Tailwind CSS
- optional Alpine.js
- optional HTMX
- 3 developers
- 8-day deadline
- payroll-focused MVP

## 3. Core Architecture

Django apps:

```text
accounts
employees
attendance
payroll
```

Do not create additional Django apps unless explicitly requested.

## 4. Coding Principles

AI agents must:

- inspect existing code before proposing changes
- preserve existing architecture
- make minimal changes
- avoid unrelated refactors
- avoid circular imports
- prefer Django built-ins
- reuse shared templates/components
- add validation where business rules require it
- use services for payroll calculations
- keep financial calculations deterministic
- use `Decimal`, never Python float, for money
- use timezone-aware timestamps
- create migrations for model changes
- update tests when behavior changes

## 5. Financial Rules

Use `DecimalField` for monetary values.

Example:

```python
models.DecimalField(max_digits=12, decimal_places=2)
```

Do not use:

```python
models.FloatField()
```

for salary, bonus, deduction, tax, or net pay.

## 6. Attendance vs Payroll Responsibility

Attendance owns:

- check-in
- check-out
- worked hours
- overtime hours
- status

Payroll owns:

- overtime monetary value
- absence monetary deduction
- unpaid leave monetary deduction
- tax
- net salary

Do not duplicate monetary payroll calculations inside attendance models.

## 7. Payroll Service Pattern

Business logic should not live entirely in Django views.

Recommended:

```text
payroll/services/payroll_service.py
payroll/services/tax_service.py
payroll/services/payslip_service.py
```

Views should orchestrate requests and responses.

Services should perform calculations.

## 8. Historical Payroll Rule

When payroll is generated, save snapshot values to `PayrollItem`.

Never generate historical payslips from the employee's current salary.

## 9. Permissions

Always check role/permission requirements before implementing views.

Prefer:

- Django Groups
- Django Permissions
- `LoginRequiredMixin`
- `PermissionRequiredMixin`
- decorators where appropriate

Do not invent a complex custom authorization framework.

## 10. UI Rules

Use Tailwind CSS.

UI should be:

- professional
- clean
- dense enough for HR/admin use
- accessible
- responsive
- consistent across screens

Prefer reusable partials/components.

Recommended visual structure:

```text
sidebar
navbar
page title + actions
summary cards
filters/search
content table/form
```

Avoid decorative gradients, excessive animations, glassmorphism, and consumer-app styling.

This is an internal business application.

## 11. AI Prompting Method

Give the AI one bounded task at a time.

Good prompt:

```text
Inspect the existing employees app.
Implement Contract CRUD.

Requirements:
- contract belongs to Employee
- only one active contract per employee
- use DecimalField for basic_salary
- use Django class-based views
- use existing Tailwind form/table components
- add validation and tests
- do not change unrelated files

Before coding, list the files you need to modify and any assumptions.
```

Bad prompt:

```text
Build the HR payroll system.
```

## 12. AI Review Checklist

Before accepting AI code, verify:

- does it match the current models?
- did it rename shared fields?
- did it introduce unnecessary dependencies?
- are monetary values Decimal?
- are permissions enforced?
- are migrations safe?
- did it add duplicate business logic?
- can another module consume the result?
- are imports one-directional?
- does it preserve historical payroll data?

## 13. Git Rules for AI-Assisted Work

AI should not silently make broad changes across the repository.

Preferred workflow:

```text
small task
-> inspect diff
-> run tests
-> manual test
-> commit
-> PR/review
```

Do not commit large AI-generated changes without review.

## 14. Testing Priority

Highest priority tests:

1. one active contract rule
2. one attendance record per employee/date
3. overtime calculation
4. unpaid leave calculation
5. payroll calculation
6. payroll snapshot persistence
7. payroll approval lock
8. employee payslip access control

## 15. AI Debugging Rule

When fixing a bug, the agent should:

1. identify the root cause
2. explain the minimal fix
3. modify only related files
4. run relevant tests
5. avoid unrelated refactoring

## 16. Shared Terminology

Use these names consistently:

```text
Employee
Department
Position
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

Do not introduce alternate names such as `SalaryRun`, `PayRecord`, or `Worker` unless the team explicitly changes the architecture.
