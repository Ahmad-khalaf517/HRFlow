# HRFlow — Seven-Day Delivery Roadmap

## 1. Outcome and constraint

Deliver one reliable synthetic-data demonstration flow in seven calendar days:

```text
Employee -> Contract -> Attendance/Leave -> Payroll -> Payslip -> Payment
```

This is an MVP, not a production payroll or legal-compliance system. Day 7 is reserved for integration review, fixes, and rehearsal; no new mandatory feature starts on Day 7.

Pending decisions Q-002 through Q-004 in `business-rules.md` block payroll calculation work. Q-001 also awaits formal owner confirmation. Do not interpret schema defaults as decision approval.

## 2. Current repository baseline

| Area | Present now | Still required |
|---|---|---|
| Foundation | Django project, Supabase database configuration, migrations, Tailwind build, base templates | Deployment hardening is outside this MVP task |
| Accounts | Login/logout, Django sessions, four group names, auth tests | Permission assignment and object-level enforcement |
| Employees | Models, migrations, Admin, active-contract uniqueness test | Custom workflows, forms, views, services, permissions |
| Attendance | Models, migrations, Admin, employee/date uniqueness test | Worked/overtime calculation service and custom screens |
| Leave | Models, migrations, Admin | Derived days, overlap prevention, approval transitions, permissions |
| Payroll inputs | Bonus, deduction, tax models and Admin | Input validation/workflow decisions and tests |
| Payroll processing | Payroll/PayrollItem models and core uniqueness tests | Calculation service, complete snapshot, immutability, guarded transitions |
| Payslip/payment | Models and Admin | Printable own-record view, one-full-payment rule, transition service, tests |
| Demo | Dashboard shell | Coherent synthetic fixtures and end-to-end scenario |

The exact migrated schema and current gaps are recorded in `erd.md`.

## 3. Required scope

- Django authentication and four roles: Admin, HR Manager, Payroll Officer, Employee.
- Employee, department, position, and contract data.
- One active contract per employee.
- Attendance facts, worked hours, overtime hours, and a simple monthly summary service.
- Simple leave request and HR approval/rejection; only approved unpaid leave affects payroll.
- Bonus and manual deduction inputs.
- One configured demonstrative tax rule.
- Monthly payroll calculation using `Decimal` after required decisions are confirmed.
- Complete, immutable `PayrollItem` snapshots and explicit payroll statuses.
- Printable HTML payslip with employee access limited to their own record.
- One full completed payment per payroll item.
- Synthetic seed data and one end-to-end demonstration scenario.

Use Django Admin for low-volume support data when a custom screen does not materially improve the demonstration.

## 4. Cut line

These items are optional and must not delay the required flow:

- PDF payslip generation;
- dashboard charts or advanced totals;
- CSV export and reports;
- custom CRUD for support data already manageable in Django Admin;
- nonessential HTMX or Alpine enhancements;
- advanced employee self-service;
- notifications, integrations, compliance, proration, corrections, and partial payments.

If the required workflow is unstable after Day 5, cut every optional item.

## 5. Architecture and ownership

Use one Django monolith:

```text
accounts -> employees -> attendance -> payroll
```

- `accounts`: authentication, role setup, and permission helpers.
- `employees`: departments, positions, employees, contracts.
- `attendance`: attendance, leave, and public monthly fact services.
- `payroll`: adjustments, tax input, payroll, snapshots, payslips, payments.

Assign one accountable owner to each feature stream:

1. employee/contract;
2. attendance/leave;
3. payroll/payslip/payment;
4. shared integration, UI, and review.

Owners may work in parallel only after shared models and service contracts are agreed. Payroll must not import attendance internals or calculate attendance facts itself.

## 6. Work packages

| ID | Reviewable outcome | Depends on | Baseline state |
|---|---|---|---|
| HRF-001 | Project, PostgreSQL, authentication, roles, base layout | Owner decisions | Foundation present; permissions incomplete |
| HRF-002 | Employee/contract workflow, validation, permissions | HRF-001 | Models/Admin present |
| HRF-003 | Attendance capture and hour-calculation services | HRF-002 | Models/Admin present |
| HRF-004 | Leave submit/approve/reject, overlap prevention, unpaid facts | HRF-002 | Models/Admin present |
| HRF-005 | Bonus, deduction, and demonstrative tax inputs | HRF-002 | Models/Admin present |
| HRF-006 | Decimal payroll calculation with exact expected example | HRF-003/004/005 and Q-002–Q-004 | Blocked |
| HRF-007 | Complete immutable snapshots and guarded payroll transitions | HRF-006 | Partial models only |
| HRF-008 | Printable payslip and own-record authorization | HRF-007 | File-metadata model only |
| HRF-009 | Exact full payment and Paid transition | HRF-007 | Partial model only |
| HRF-010 | Synthetic fixtures, integration review, UI consistency, demo | HRF-008/009 | Not started |

Each work package gets its own completed `task-brief-template.md`, branch, tests, manual review notes, and focused pull request.

## 7. Seven-day sequence

| Day | Required outcome |
|---|---|
| 1 | Confirm Q-001–Q-004, review the migrated schema/gaps, freeze public service contracts and ownership |
| 2 | Complete employee/contract workflow, permissions, validation, tests, and migration changes |
| 3 | Complete attendance and leave services/workflows, including overlap and approval rules |
| 4 | Complete payroll inputs; after decisions are confirmed, implement the exact calculation service |
| 5 | Complete snapshots, immutability guards, payroll statuses, and module integration |
| 6 | Complete payslip authorization, payment workflow, synthetic fixtures, and UI consistency |
| 7 | Run the full manual scenario, permission/security review, fixes, and demo rehearsal |

If the calendar starts after some baseline work is complete, use the recovered capacity for tests, permission review, and integration—not optional scope until the end-to-end flow passes.

## 8. Definition of done

A work package is done only when:

- its exact acceptance criteria pass;
- server-side permissions and object-access cases are tested;
- model validation and database constraints exist where appropriate;
- migrations are included and `makemigrations --check --dry-run` reports no drift;
- unit/integration tests and `ruff check .` pass;
- the affected workflow is manually exercised and its observed result recorded;
- UI work follows `design-system.md` and includes rebuilt CSS;
- the diff contains no unrelated changes, secrets, or real HR/payroll data;
- another person reviews it.

## 9. Demonstration scenario

After Q-001–Q-004 are confirmed, define one coherent synthetic employee and payroll month. Record exact expected values for salary, overtime, bonus, unpaid leave, manual deduction, tax, gross, total deductions, and net salary in the task acceptance criteria.

The final demonstration must begin with employee/contract setup and end with the recorded completed payment. It must also demonstrate at least one denied object-access case for an employee user.
