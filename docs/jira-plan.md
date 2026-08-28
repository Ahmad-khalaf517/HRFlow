# HRFlow — Jira Delivery Plan

## 1. Board Workflow

Use:

```text
Backlog
-> To Do
-> In Progress
-> Code Review
-> Testing
-> Done
```

## 2. Delivery Strategy

Keep one ordered MVP backlog and move work through named milestones. Staffing and calendar commitments are managed separately from this product specification.

Recommended release:

```text
HRFlow MVP
```

## 3. Epics

### EPIC-01 — Project Foundation

- Django setup
- PostgreSQL
- Tailwind
- shared templates
- authentication
- roles
- seed data

### EPIC-02 — Employee Management

- departments
- positions
- employees
- contracts

### EPIC-03 — Attendance & Leave

- attendance
- work hours
- overtime hours
- leave types
- leave requests
- approvals
- absence/unpaid leave calculations

### EPIC-04 — Payroll Inputs

- bonuses
- manual deductions
- taxes

### EPIC-05 — Payroll Processing

- payroll runs
- payroll calculation service
- payroll items
- review and approval

### EPIC-06 — Payslips & Payments

- payslip screen
- PDF generation
- payments

### EPIC-07 — Dashboard & Final QA

- dashboard
- integration
- tests
- UI consistency
- demo data

---

# 4. Jira Stories

## Foundation

### HRF-001 Setup Django Project

**As a developer, I want the Django project configured so the team can develop on a shared foundation.**

Acceptance Criteria:

- Django project starts locally
- environment variables are supported
- PostgreSQL connection configured
- apps created
- base settings committed
- `.env`, credentials, database dumps, uploaded payslips, and local sensitive files excluded from Git

### HRF-002 Configure Tailwind

Acceptance Criteria:

- Tailwind builds locally
- base template loads compiled CSS
- production/dev commands documented

### HRF-003 Authentication

Acceptance Criteria:

- login works
- logout works
- unauthenticated users are redirected
- role/group foundation exists

---

## Employees

### HRF-010 Department CRUD

Acceptance Criteria:

- list departments
- create department
- edit department
- deactivate department

### HRF-011 Position CRUD

Acceptance Criteria:

- position belongs to department
- create/edit/list works
- salary range is optional

### HRF-012 Employee CRUD

Acceptance Criteria:

- employee number unique
- employee can be assigned to department and position
- active/inactive status supported
- searchable employee list

### HRF-013 Contract Management

Acceptance Criteria:

- create contract for employee
- basic salary stored
- working hours stored
- old contracts remain available
- only one active contract per employee

---

## Attendance & Leave

### HRF-020 Attendance CRUD

Acceptance Criteria:

- one record per employee/date
- check-in/check-out supported
- worked hours calculated

### HRF-021 Calculate Overtime Hours

Acceptance Criteria:

- overtime is derived from worked hours vs expected hours
- overtime stores hours only
- negative overtime is not allowed

### HRF-022 Leave Type Management

Acceptance Criteria:

- create/edit leave type
- paid/unpaid flag supported
- annual allowance supported

### HRF-023 Employee Leave Request

Acceptance Criteria:

- employee selects leave type
- start/end dates required
- requested days calculated
- initial status is pending
- overlapping pending/approved requests rejected
- working-day behavior follows an accepted decision

### HRF-024 Leave Approval

Acceptance Criteria:

- HR can approve/reject
- approver and date stored
- employee cannot approve own request

### HRF-025 Attendance Summary Services

Acceptance Criteria:

Expose services for:

- overtime hours
- absence days
- unpaid leave days

---

## Payroll Inputs

### HRF-030 Bonus Management

Acceptance Criteria:

- employee bonus can be created
- amount and effective date required
- payroll can retrieve bonuses for a period

### HRF-031 Manual Deduction Management

Acceptance Criteria:

- deduction type and amount stored
- effective date stored
- payroll can retrieve deductions for period

### HRF-032 Tax Configuration

Acceptance Criteria:

- configurable percentage brackets supported
- tax service returns monetary tax value
- uses the simple non-progressive demonstrative rule in `business-rules.md`
- UI does not claim legal tax compliance

---

## Payroll

### HRF-040 Create Payroll Run

Acceptance Criteria:

- month/year selectable
- duplicate month/year prevented
- initial status = draft

### HRF-041 Payroll Calculation Service

Acceptance Criteria:

Calculation includes:

```text
basic salary
allowances
overtime
bonus
absence deduction
unpaid leave deduction
manual deductions
tax
```

Returns:

```text
gross salary
total deductions
net salary
```

Additional Acceptance Criteria:

- calculation follows accepted decisions Q-002 through Q-004
- uses `Decimal` throughout
- fails safely when an active contract is missing
- table-driven boundary tests document exact expected values

### HRF-042 Generate Payroll Items

Acceptance Criteria:

- one payroll item per active employee
- snapshot values saved
- duplicate employee item prevented

### HRF-043 Payroll Review

Acceptance Criteria:

- calculated payroll can be reviewed
- payroll totals displayed
- individual employee breakdown visible

### HRF-044 Payroll Approval

Acceptance Criteria:

- authorized user only
- approver/date stored
- approved payroll cannot be recalculated normally
- Payroll Officer or Admin may approve for this MVP

---

## Payslips & Payments

### HRF-050 Payslip View

Acceptance Criteria:

Shows:

- employee information
- payroll period
- earnings
- deductions
- net salary

### HRF-051 Generate Payslip PDF

**Optional — only after the complete HTML payslip/payment flow works.**

Acceptance Criteria:

- PDF generated from payroll snapshot
- employee can download own payslip

### HRF-052 Record Employee Payment

Acceptance Criteria:

- payment amount
- payment date
- method
- optional reference number
- payment linked to payroll item
- only approved payroll items can be paid
- payment amount must equal the payroll item's net salary
- partial payments, overpayments, failures, and reversals are out of scope

---

## Dashboard / QA

### HRF-060 Dashboard

Acceptance Criteria:

Display:

- active employees
- present today
- absent today
- on leave today
- pending leaves
- current payroll net total

### HRF-061 Seed Demo Data

Acceptance Criteria:

Seed includes:

- departments
- positions
- 3 employees
- contracts
- attendance
- leave
- bonuses/deductions
- one payroll period

### HRF-062 End-to-End Demo Test

Acceptance Criteria:

Scenario passes:

```text
Employee -> Contract -> Attendance -> Leave -> Payroll -> Payslip -> Payment
```

---

# 5. Dependencies

Important Jira links:

```text
HRF-013 Contract Management
blocks HRF-041 Payroll Calculation Service

HRF-021 Calculate Overtime Hours
blocks HRF-041 Payroll Calculation Service

HRF-025 Attendance Summary Services
blocks HRF-041 Payroll Calculation Service

HRF-030 Bonus Management
blocks HRF-041 Payroll Calculation Service

HRF-031 Manual Deduction Management
blocks HRF-041 Payroll Calculation Service

HRF-041 Payroll Calculation Service
blocks HRF-042 Generate Payroll Items

HRF-042 Generate Payroll Items
blocks HRF-050 Payslip View

HRF-042 Generate Payroll Items
blocks HRF-052 Record Employee Payment
```

## 6. Delivery Milestones

### Foundation

- HRF-001
- HRF-002
- HRF-003
- ERD freeze

### HR Core

- HRF-010
- HRF-011
- HRF-012
- HRF-020 start
- HRF-040 model start

### Attendance and Payroll Inputs

- HRF-013
- HRF-020
- HRF-021
- HRF-030
- HRF-031

### Leave and Calculation Services

- HRF-022
- HRF-023
- HRF-024
- HRF-025
- HRF-032
- HRF-041 with fixture/mock data

### Payroll Integration

- HRF-041 real integration
- HRF-042

### Approval, Payslips, and Payments

- HRF-043
- HRF-044
- HRF-050
- HRF-052
- integration fixes

### Quality and Demo Readiness

- HRF-060
- HRF-061
- HRF-062
- bug fixing
- UI polish
- documentation
- HRF-051 only if the full MVP is already stable

---

# 7. Definition of Ready

A Jira story can enter development when:

- acceptance criteria are clear
- required models are known
- dependencies are identified
- expected UI is understood
- no unresolved business rule blocks implementation
- related Q-001 through Q-004 decisions are answered where relevant
- AI context contains no Restricted data

# 8. Definition of Done

- acceptance criteria pass
- migrations committed
- permissions verified
- code reviewed
- merged to `develop`
- no regression in existing flow
- manual or automated tests pass
- exact verification commands and results recorded in the PR
- server-side permission and object-level access tests pass
- no secrets or real employee/payroll data are present
