# HR & Payroll Management System — Project Plan

## 1. Project Summary

**Project:** HR & Payroll Management System  
**Framework:** Django  
**Team Size:** 3 developers  
**Deadline:** 7 days
**Frontend:** Django Templates + Tailwind CSS  
**Database:** PostgreSQL

The system manages core HR records and automates payroll using employee contracts, attendance, leave, overtime, bonuses, deductions, and taxes.

The project is intentionally scoped as a focused MVP. Recruitment, performance management, advanced reporting, biometric integration, bank APIs, and full country-specific payroll compliance are out of scope for the first version.

## 2. Primary Goal

Deliver one complete end-to-end workflow:

1. Create an employee.
2. Assign department, position, and contract.
3. Record attendance.
4. Submit and approve leave.
5. Derive overtime and attendance-based deductions.
6. Add bonuses and manual deductions.
7. Generate monthly payroll.
8. Review and approve payroll.
9. Generate a payslip.
10. Record payment.

## 3. Scope

### Must Have

- Authentication
- Roles and permissions
- Departments
- Positions
- Employees
- Contracts
- Attendance
- Leave requests
- Attendance-derived overtime
- Attendance-derived absence/unpaid-leave deductions
- Bonuses
- Manual deductions
- Tax configuration
- Payroll processing
- Payroll items
- Payslips
- Payments
- Basic dashboard

### Should Have

- Employee self-service pages
- Payroll summary reports
- Attendance summary
- CSV export
- Audit fields such as created_by and timestamps

### Out of Scope for MVP

- Recruitment pipeline
- Applicant tracking
- Performance reviews
- Biometric device integration
- Bank API integration
- Email/SMS notifications
- Multi-company tenancy
- Multi-country payroll compliance
- Advanced accounting integration
- AI recommendations

## 4. Key Business Rules

This section is a planning summary. `business-rules.md` is authoritative and identifies which rules are confirmed versus awaiting an owner decision. Do not implement a pending formula from examples in this plan.

### Attendance

Attendance stores factual work data:

- check-in
- check-out
- worked hours
- overtime hours
- attendance status

Attendance does not calculate salary amounts.

### Overtime

Overtime hours are derived from attendance.

Example:

```text
Expected daily hours = 8
Worked hours = 10
Overtime hours = 2
```

Payroll converts overtime hours into money.

### Deductions

Two categories exist:

1. Attendance-derived deductions
   - absence
   - unpaid leave
   - optionally lateness

2. Manual/financial deductions
   - loan repayment
   - insurance
   - salary advance
   - disciplinary deduction
   - other

### Payroll Formula

```text
Gross Salary =
Basic Salary
+ Allowances
+ Overtime Pay
+ Bonuses

Total Deductions =
Attendance Deductions
+ Manual Deductions
+ Tax

Net Salary = Gross Salary - Total Deductions
```

The remaining currency, rate, overtime, and weekday-counting decisions are Q-002 through Q-004 in `open-questions.md`. Proration and complex calendar rules are out of scope.

### Payroll Status

```text
Draft -> Calculated -> Reviewed -> Approved -> Paid
```

Approved or paid payroll should not be recalculated without an explicit administrative action.

### Payroll History

PayrollItem stores a salary snapshot for each employee and payroll period. Historical payslips must never be dynamically recalculated from the employee's current salary.

The snapshot must also retain enough policy/version information to reproduce the result, including currency, effective contract inputs, calculation version, and applicable tax details.

## 5. Django App Structure

To reduce overhead during the one-week deadline, use four main apps:

```text
project/
├── config/
├── accounts/
├── employees/
├── attendance/
├── payroll/
├── templates/
├── static/
└── manage.py
```

### accounts

- authentication
- roles
- permissions

### employees

- departments
- positions
- employees
- contracts

### attendance

- attendance records
- leave types
- leave requests
- attendance calculations

### payroll

- bonuses
- manual deductions
- taxes
- payroll runs
- payroll items
- payslips
- payments

## 6. Team Ownership

### Developer 1 — Employee Domain

- project setup support
- authentication support
- departments
- positions
- employees
- contracts

### Developer 2 — Attendance Domain

- attendance
- worked hours
- overtime hours
- leave types
- leave requests
- leave approval
- absence/unpaid leave facts

### Developer 3 — Payroll Domain

- bonuses
- deductions
- tax rules
- payroll engine
- payroll items
- payslips
- payments

### Shared Responsibilities

- dashboard
- UI consistency
- integration
- testing
- documentation
- seed/demo data

## 7. Anti-Blocking Strategy

### Shared models must be agreed early

Freeze naming and main fields for:

- Employee
- Contract
- Attendance
- LeaveRequest
- Payroll
- PayrollItem

### Payroll should use services/interfaces

Examples:

```python
get_employee_overtime_hours(employee, start_date, end_date)
get_unpaid_leave_days(employee, start_date, end_date)
get_absence_days(employee, start_date, end_date)
```

This allows payroll development against mock values before attendance is complete.

### Integrate daily

Do not wait until Day 7 to combine branches.

Recommended Git branches:

```text
main
develop
feature/employees
feature/attendance
feature/payroll
```

## 8. Seven-Day Delivery Plan

| Day | Main Work |
|---|---|
| 1 | Finalize docs, ERD, project setup, PostgreSQL, Tailwind, auth foundation |
| 2 | Employees, departments, positions, attendance skeleton, payroll models |
| 3 | Contracts, attendance completion, bonuses/deductions |
| 4 | Leave flow, overtime calculations, payroll calculation service with test data |
| 5 | Connect employee/contract/attendance/leave data into payroll |
| 6 | Full payroll run, review/approval, printable payslip, payment, integration testing |
| 7 | Basic dashboard, seed data, QA, bug fixes, documentation, final demo rehearsal |

## 9. Definition of Done

A task is done only when:

- code is implemented
- validation exists
- permissions are checked
- migrations are committed
- UI is usable
- tests or manual acceptance checks pass
- code is merged through review
- no known blocking bug remains
- no unresolved decision was silently converted into implementation behavior
- no secrets or real employee/payroll data appear in code, fixtures, logs, screenshots, or AI prompts

## 10. Demo Scenario

Use one coherent demo instead of random CRUD screens.

Example:

```text
Employee: Ahmad Khalaf
Basic Salary: $1,500
Overtime: 5 hours
Bonus: $200
Unpaid Leave: 1 day
Manual Deduction: $50
Tax: $100
```

Demo flow:

```text
Employee
-> Contract
-> Attendance
-> Leave
-> Payroll Calculation
-> Payroll Approval
-> Payslip
-> Payment
```
