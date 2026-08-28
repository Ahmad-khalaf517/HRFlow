# CLAUDE.md — HR & Payroll Management System

## Project

You are assisting with an 8-day Django MVP for an HR & Payroll Management System.

Primary objective: deliver a reliable end-to-end payroll workflow, not a large feature set.

## Stack

- Python 3.12+
- Django 5.x
- PostgreSQL
- Django Templates
- Tailwind CSS
- Alpine.js when lightweight client-side interaction is needed
- HTMX only when it clearly simplifies partial page interactions
- pytest + pytest-django

## Django Apps

Use only these primary apps unless explicitly instructed otherwise:

```text
accounts
employees
attendance
payroll
```

## Core Models

Use these canonical names:

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

Do not rename shared models or important fields without explicit approval.

## Architecture Rules

1. Inspect existing code before editing.
2. Prefer minimal diffs.
3. Do not refactor unrelated code.
4. Avoid circular imports.
5. Keep payroll calculations in services.
6. Use Django forms/model validation for business validation.
7. Use Django Groups/Permissions for roles.
8. Use `Decimal` for all money calculations.
9. Preserve payroll snapshots.
10. Approved payroll is immutable through normal flows.

## Attendance Responsibility

Attendance represents work facts:

```text
check-in
check-out
worked hours
overtime hours
status
```

Attendance does not own overtime money or salary deductions.

## Payroll Responsibility

Payroll translates HR/attendance facts into money.

Inputs:

```text
active contract
basic salary
allowances
overtime hours
absence days
unpaid leave days
bonuses
manual deductions
tax
```

Outputs:

```text
gross salary
total deductions
net salary
```

## Payroll Formula

```text
Gross = Basic + Allowances + Overtime Amount + Bonuses

Total Deductions =
Absence Deduction
+ Unpaid Leave Deduction
+ Manual Deductions
+ Tax

Net = Gross - Total Deductions
```

## Payroll Snapshot Rule

`PayrollItem` stores the values used for the payroll period.

Never make old payslips depend on current Employee or Contract salary values.

## UI Direction

This is an internal HR/admin application.

Use Tailwind to create:

- left sidebar
- top header
- compact page title/action area
- statistic cards
- professional data tables
- filters/search
- clear forms
- status badges
- confirmation modals
- responsive layouts

Avoid:

- excessive gradients
- glassmorphism
- oversized cards
- unnecessary animation
- playful consumer-app design

## Reusable Template Components

Prefer reusable partials for:

```text
button
badge
form-field
alert
modal
table
pagination
empty-state
stat-card
```

Do not duplicate large Tailwind class strings across every page if a reusable pattern already exists.

## Suggested Project Layout

```text
config/
accounts/
employees/
attendance/
payroll/
templates/
    base.html
    components/
    accounts/
    employees/
    attendance/
    payroll/
static/
```

## Service Interfaces

Payroll should preferably consume attendance through service functions such as:

```python
get_employee_overtime_hours(employee, start_date, end_date)
get_absence_days(employee, start_date, end_date)
get_unpaid_leave_days(employee, start_date, end_date)
```

Do not tightly couple payroll to low-level attendance implementation when a service interface is sufficient.

## Testing

Prioritize tests for:

- one active contract per employee
- attendance uniqueness per day
- overtime calculation
- leave approval
- unpaid leave calculations
- payroll calculation
- payroll snapshot values
- approval lock
- access control to payslips

## When Implementing a Task

Before changing code:

1. inspect relevant models/views/templates/tests
2. identify dependencies
3. state a short implementation plan
4. modify only necessary files
5. run targeted tests
6. report what changed and any remaining risk

## When Generating UI from a Screenshot or Description

- preserve existing layout system
- reuse existing components
- match spacing, hierarchy, sizing, borders, and typography carefully
- use Lucide icons or Heroicons
- do not add arbitrary new design systems
- ensure forms/tables remain functional

## Deadline Rule

Prefer a complete, testable MVP over optional features.

If a requested feature threatens the core payroll flow, flag it and propose the smallest implementation that satisfies the requirement.
