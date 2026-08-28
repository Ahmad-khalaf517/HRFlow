# HR & Payroll Management System — Modules

## 1. Module Strategy

Use four Django apps to keep the project manageable during the 8-day deadline.

```text
accounts
employees
attendance
payroll
```

Avoid over-splitting the project into many apps because it increases setup, imports, migrations, and integration overhead.

---

# 2. Accounts Module

## Responsibilities

- login
- logout
- access control
- Django groups and permissions
- user-to-employee relationship

## Roles

### Admin

Full system access.

### HR Manager

Can manage:

- departments
- positions
- employees
- contracts
- attendance
- leave approval

### Payroll Officer

Can manage:

- bonuses
- deductions
- taxes
- payroll
- payslips
- payments

### Employee

Can view:

- profile
- attendance
- leave
- payslips

Can submit:

- leave requests

## Recommended Implementation

Use Django's built-in:

- `User`
- `Group`
- `Permission`
- `LoginRequiredMixin`
- `PermissionRequiredMixin`

Do not build a custom RBAC engine for this MVP.

---

# 3. Employees Module

## Responsibilities

- departments
- positions
- employees
- contracts

## Pages

### Departments

- list
- create
- edit
- deactivate

### Positions

- list
- create
- edit
- deactivate

### Employees

- list
- create
- view
- edit
- deactivate
- search/filter

### Contracts

- employee contract history
- create contract
- update contract
- mark active/inactive

## Important Business Rules

- employee number must be unique
- only one active contract per employee
- salary is owned by Contract
- old contracts must remain available for payroll history reference

---

# 4. Attendance Module

## Responsibilities

- attendance records
- worked-hour calculation
- overtime-hour calculation
- leave types
- leave requests
- leave approval
- absence/unpaid leave facts

## Attendance Rules

Attendance stores facts, not financial values.

Example:

```text
check_in = 08:00
check_out = 18:00
worked_hours = 10
overtime_hours = 2
```

Do not store `$30 overtime pay` in attendance.

## Leave Flow

```text
Employee submits request
        ↓
Pending
        ↓
HR reviews
   ↓          ↓
Approved    Rejected
```

## Service Interface

Expose functions that payroll can consume.

Examples:

```python
get_employee_overtime_hours(employee, start_date, end_date)
get_absence_days(employee, start_date, end_date)
get_unpaid_leave_days(employee, start_date, end_date)
```

This avoids payroll depending directly on attendance implementation details.

---

# 5. Payroll Module

## Responsibilities

- bonuses
- manual deductions
- tax rules
- payroll runs
- payroll calculation
- payroll items
- payslips
- payments

## Payroll Inputs

### From Contract

- basic salary
- default allowances
- expected working hours

### From Attendance

- overtime hours
- absence days

### From Leave

- unpaid leave days

### Direct Financial Inputs

- bonus
- manual deduction
- tax

## Payroll Calculation Service

Recommended structure:

```text
payroll/
├── models.py
├── forms.py
├── views.py
├── urls.py
├── services/
│   ├── payroll_service.py
│   ├── tax_service.py
│   └── payslip_service.py
└── tests/
```

### Suggested service functions

```python
calculate_hourly_rate(contract)
calculate_overtime_amount(contract, overtime_hours)
calculate_absence_deduction(contract, absence_days)
calculate_unpaid_leave_deduction(contract, unpaid_leave_days)
calculate_tax(taxable_income)
calculate_employee_payroll(employee, payroll_period)
generate_payroll(payroll)
```

## Payroll Workflow

```text
Create Payroll Run
      ↓
Draft
      ↓
Calculate Employees
      ↓
Calculated
      ↓
Review
      ↓
Reviewed
      ↓
Approve
      ↓
Approved
      ↓
Generate Payslips / Record Payments
      ↓
Paid
```

## Locking Rule

Approved payroll must not be recalculated through the standard UI.

---

# 6. Dashboard

Dashboard is shared, not a separate Django app for MVP.

## HR Dashboard Cards

- total active employees
- present today
- absent today
- on leave today
- pending leave requests

## Payroll Dashboard Cards

- current payroll status
- current payroll total gross
- current payroll total deductions
- current payroll total net

## Optional Charts

Only if time allows:

- employees per department
- monthly payroll totals
- attendance summary

---

# 7. UI Strategy

## Stack

- Django Templates
- Tailwind CSS
- Alpine.js for lightweight interactivity
- HTMX only where it gives clear value

Do not build React/Vue for this 8-day project.

## Core Reusable UI Components

Create reusable template partials for:

```text
sidebar
navbar
page header
stat card
button
form field
badge
modal
table
empty state
pagination
alert
```

## Layout

Desktop-first admin layout:

```text
Sidebar | Header
        | Main Content
```

Employee pages may reuse the same layout with fewer navigation links.

---

# 8. Module Dependency Rules

Recommended direction:

```text
accounts
   ↓
employees
   ↓
attendance
   ↓
payroll
```

But payroll should use public service functions rather than tightly coupling itself to attendance internals.

Avoid circular imports.

### Example

Good:

```python
from attendance.services import get_employee_overtime_hours
```

Bad:

```python
# payroll imports attendance models
# attendance then imports payroll models
```

---

# 9. MVP Permission Matrix

| Action | Admin | HR | Payroll | Employee |
|---|---:|---:|---:|---:|
| Manage employees | Yes | Yes | View | Own profile |
| Manage contracts | Yes | Yes | View | View own |
| Manage attendance | Yes | Yes | View | View own |
| Submit leave | Yes | Yes | Yes | Yes |
| Approve leave | Yes | Yes | No | No |
| Manage bonuses | Yes | No | Yes | No |
| Manage deductions | Yes | No | Yes | No |
| Generate payroll | Yes | No | Yes | No |
| Approve payroll | Yes | No | Yes | No |
| View all payslips | Yes | Limited | Yes | No |
| View own payslip | Yes | Yes | Yes | Yes |
| Record payment | Yes | No | Yes | No |
