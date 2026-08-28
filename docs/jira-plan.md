# HR & Payroll Management System — Jira Sprint Plan

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

## 2. Sprint Strategy

Because the deadline is 8 days, do not create several long formal sprints. Use one delivery sprint with daily milestones.

Recommended sprint:

```text
Sprint 1 — HR & Payroll MVP
Duration: 8 days
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

### HRP-001 Setup Django Project

**As a developer, I want the Django project configured so the team can develop on a shared foundation.**

Acceptance Criteria:

- Django project starts locally
- environment variables are supported
- PostgreSQL connection configured
- apps created
- base settings committed

### HRP-002 Configure Tailwind

Acceptance Criteria:

- Tailwind builds locally
- base template loads compiled CSS
- production/dev commands documented

### HRP-003 Authentication

Acceptance Criteria:

- login works
- logout works
- unauthenticated users are redirected
- role/group foundation exists

---

## Employees

### HRP-010 Department CRUD

Acceptance Criteria:

- list departments
- create department
- edit department
- deactivate department

### HRP-011 Position CRUD

Acceptance Criteria:

- position belongs to department
- create/edit/list works
- salary range is optional

### HRP-012 Employee CRUD

Acceptance Criteria:

- employee number unique
- employee can be assigned to department and position
- active/inactive status supported
- searchable employee list

### HRP-013 Contract Management

Acceptance Criteria:

- create contract for employee
- basic salary stored
- working hours stored
- old contracts remain available
- only one active contract per employee

---

## Attendance & Leave

### HRP-020 Attendance CRUD

Acceptance Criteria:

- one record per employee/date
- check-in/check-out supported
- worked hours calculated

### HRP-021 Calculate Overtime Hours

Acceptance Criteria:

- overtime is derived from worked hours vs expected hours
- overtime stores hours only
- negative overtime is not allowed

### HRP-022 Leave Type Management

Acceptance Criteria:

- create/edit leave type
- paid/unpaid flag supported
- annual allowance supported

### HRP-023 Employee Leave Request

Acceptance Criteria:

- employee selects leave type
- start/end dates required
- requested days calculated
- initial status is pending

### HRP-024 Leave Approval

Acceptance Criteria:

- HR can approve/reject
- approver and date stored
- employee cannot approve own request

### HRP-025 Attendance Summary Services

Acceptance Criteria:

Expose services for:

- overtime hours
- absence days
- unpaid leave days

---

## Payroll Inputs

### HRP-030 Bonus Management

Acceptance Criteria:

- employee bonus can be created
- amount and effective date required
- payroll can retrieve bonuses for a period

### HRP-031 Manual Deduction Management

Acceptance Criteria:

- deduction type and amount stored
- effective date stored
- payroll can retrieve deductions for period

### HRP-032 Tax Configuration

Acceptance Criteria:

- configurable percentage brackets supported
- tax service returns monetary tax value

---

## Payroll

### HRP-040 Create Payroll Run

Acceptance Criteria:

- month/year or period selectable
- duplicate payroll period prevented
- initial status = draft

### HRP-041 Payroll Calculation Service

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

### HRP-042 Generate Payroll Items

Acceptance Criteria:

- one payroll item per active employee
- snapshot values saved
- duplicate employee item prevented

### HRP-043 Payroll Review

Acceptance Criteria:

- calculated payroll can be reviewed
- payroll totals displayed
- individual employee breakdown visible

### HRP-044 Payroll Approval

Acceptance Criteria:

- authorized user only
- approver/date stored
- approved payroll cannot be recalculated normally

---

## Payslips & Payments

### HRP-050 Payslip View

Acceptance Criteria:

Shows:

- employee information
- payroll period
- earnings
- deductions
- net salary

### HRP-051 Generate Payslip PDF

Acceptance Criteria:

- PDF generated from payroll snapshot
- employee can download own payslip

### HRP-052 Record Employee Payment

Acceptance Criteria:

- payment amount
- payment date
- method
- optional reference number
- payment linked to payroll item

---

## Dashboard / QA

### HRP-060 Dashboard

Acceptance Criteria:

Display:

- active employees
- present today
- absent today
- on leave today
- pending leaves
- current payroll net total

### HRP-061 Seed Demo Data

Acceptance Criteria:

Seed includes:

- departments
- positions
- 5+ employees
- contracts
- attendance
- leave
- bonuses/deductions
- one payroll period

### HRP-062 End-to-End Demo Test

Acceptance Criteria:

Scenario passes:

```text
Employee -> Contract -> Attendance -> Leave -> Payroll -> Payslip -> Payment
```

---

# 5. Dependencies

Important Jira links:

```text
HRP-013 Contract Management
blocks HRP-041 Payroll Calculation Service

HRP-021 Calculate Overtime Hours
blocks HRP-041 Payroll Calculation Service

HRP-025 Attendance Summary Services
blocks HRP-041 Payroll Calculation Service

HRP-030 Bonus Management
blocks HRP-041 Payroll Calculation Service

HRP-031 Manual Deduction Management
blocks HRP-041 Payroll Calculation Service

HRP-041 Payroll Calculation Service
blocks HRP-042 Generate Payroll Items

HRP-042 Generate Payroll Items
blocks HRP-050 Payslip View

HRP-042 Generate Payroll Items
blocks HRP-052 Record Employee Payment
```

## 6. Daily Milestones

### Day 1

- HRP-001
- HRP-002
- HRP-003
- ERD freeze

### Day 2

- HRP-010
- HRP-011
- HRP-012
- HRP-020 start
- HRP-040 model start

### Day 3

- HRP-013
- HRP-020
- HRP-021
- HRP-030
- HRP-031

### Day 4

- HRP-022
- HRP-023
- HRP-024
- HRP-025
- HRP-032
- HRP-041 with fixture/mock data

### Day 5

- HRP-041 real integration
- HRP-042

### Day 6

- HRP-043
- HRP-044
- integration fixes

### Day 7

- HRP-050
- HRP-051
- HRP-052
- HRP-060

### Day 8

- HRP-061
- HRP-062
- bug fixing
- UI polish
- documentation

---

# 7. Definition of Ready

A Jira story can enter development when:

- acceptance criteria are clear
- required models are known
- dependencies are identified
- expected UI is understood
- no unresolved business rule blocks implementation

# 8. Definition of Done

- acceptance criteria pass
- migrations committed
- permissions verified
- code reviewed
- merged to `develop`
- no regression in existing flow
- manual or automated tests pass
