# HRFlow — Seven-Day Delivery Plan

## 1. Outcome and Constraint

Deliver one reliable demonstration flow in seven calendar days:

```text
Employee -> Contract -> Attendance/Leave -> Payroll -> Payslip -> Payment
```

This is a synthetic-data MVP, not a production payroll or legal-compliance system. Day 7 is reserved for manual review, fixes, and rehearsal; no new mandatory feature starts on Day 7.

## 2. Required Scope

- Django authentication and four roles: Admin, HR Manager, Payroll Officer, and Employee.
- Employee, department, position, and contract data. Department and position management may use Django Admin.
- One active contract per employee.
- Attendance facts, worked hours, overtime hours, and a simple monthly summary service.
- Simple leave request and HR approval/rejection; only approved unpaid leave affects payroll.
- Bonus and manual deduction inputs. Low-volume management may use Django Admin.
- One seeded/configured demonstrative tax rule; a custom tax-management UI is not required.
- Monthly payroll calculation using `Decimal`.
- Immutable `PayrollItem` snapshots and explicit payroll statuses.
- Printable HTML payslip with employee access limited to their own payslip.
- One full completed payment per payroll item.
- Synthetic seed data and one end-to-end demonstration scenario.

## 3. Cut Line

The following are optional and must not delay the required flow:

- PDF payslip generation;
- dashboard charts or advanced totals;
- CSV export and reports;
- custom CRUD screens for support data already manageable in Django Admin;
- HTMX or Alpine enhancements that are not necessary for the workflow;
- advanced employee self-service pages;
- notifications, integrations, legal compliance, proration, correction runs, and partial payments.

If required work is unstable after Day 5, cut all optional work.

## 4. Architecture

Use one Django monolith with four primary apps:

```text
accounts -> employees -> attendance -> payroll
```

- `accounts`: authentication, roles, permissions.
- `employees`: departments, positions, employees, contracts.
- `attendance`: attendance, leave, and monthly fact services.
- `payroll`: adjustments, tax input, payroll, snapshots, payslips, payments.

Payroll consumes attendance through public service functions. Views stay thin; calculations and status transitions live in services. Do not add another primary app without approval.

## 5. Work Packages

| ID | Reviewable outcome | Depends on |
|---|---|---|
| HRF-01 | Project setup, PostgreSQL, authentication, roles, base layout | Approved decisions |
| HRF-02 | Employee and contract workflow with uniqueness/active-contract constraints | HRF-01 |
| HRF-03 | Attendance capture and worked/overtime-hour calculations | HRF-02 |
| HRF-04 | Leave request, approval, overlap validation, and unpaid-leave facts | HRF-02 |
| HRF-05 | Bonus, manual deduction, and demonstrative tax inputs | HRF-02 |
| HRF-06 | Payroll calculation service with one exact Decimal example and expected result | HRF-03, HRF-04, HRF-05 |
| HRF-07 | Payroll runs, PayrollItem snapshots, and guarded status transitions | HRF-06 |
| HRF-08 | Printable payslip and own-record authorization | HRF-07 |
| HRF-09 | Full payment recording and Paid transition | HRF-07 |
| HRF-10 | Synthetic seed data, manual integration review, UI consistency, and demo | HRF-08, HRF-09 |

## 6. Seven-Day Sequence

| Day | Required outcome |
|---|---|
| 1 | Approve the four pending defaults; freeze ERD and interfaces; set up Django, PostgreSQL, authentication, roles, base UI, and initial synthetic fixtures |
| 2 | Complete employees and contracts, including constraints, permissions, migrations, and manual workflow review |
| 3 | Complete attendance and simplified leave facts/services and review their workflows manually |
| 4 | Complete payroll inputs and the calculation service against one exact synthetic scenario |
| 5 | Complete payroll runs, immutable item snapshots, statuses, and real module integration |
| 6 | Complete payslip access, full payment, end-to-end workflow review, and required UI polish |
| 7 | Run the complete manual scenario; fix defects; review permissions and data safety; rehearse the demo |

## 7. Ownership and Integration

Assign one accountable owner to each domain: employee, attendance, and payroll. Ownership does not prevent collaboration. Shared responsibilities are authentication, UI consistency, integration, manual review, seed data, documentation, and demo readiness.

Freeze shared model names and public service signatures before dependent work. Merge small reviewed changes continuously; do not wait for the final days to integrate.

## 8. Definition of Done

A work package is done only when:

- its acceptance criteria pass;
- validation, server-side permissions, and database constraints are present;
- migrations are included when required;
- the affected workflow has been manually exercised and its observed result recorded;
- the diff contains no unrelated changes, secrets, or real HR/payroll data;
- another person has reviewed the change.

## 9. Demo Scenario

Use one coherent synthetic employee and payroll month. Record exact expected values for salary, overtime, bonus, unpaid leave, manual deduction, tax, gross, total deductions, and net salary. The final demonstration follows the required flow from employee creation through completed payment.
