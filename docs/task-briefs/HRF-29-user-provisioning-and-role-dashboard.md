# HRFlow Task Brief

## Task

- Ticket / title: HRF-29 — User provisioning and role-aware dashboard
- Owner: Person 1 / current shared-file integration owner
- Context commit: Current local working tree (no commit requested)
- Owning app: `accounts` and `employees`
- Depends on tasks/migrations: `accounts.0001_seed_role_groups`, `employees.0003`
- Required outcome: Provision a Django login for each newly created employee, allow authorized
  managers to create HR Manager and Payroll Officer accounts from a separate screen, and show
  dashboard/navigation content that matches each authenticated role.

## Scope

- In scope: Employee login provisioning with the requested initial password; separate staff-user
  list/create screens; group assignment; server-side access checks; role-aware dashboard cards and
  links; display name beside the header avatar; focused tests.
- Out of scope: Password-reset/change-password workflow, invitations, email delivery, employee
  backfill, payslip implementation, generic audit logging, and payroll/attendance business logic.
- Files allowed to change: `accounts/**`, `employees/forms.py`, `employees/services.py`,
  `employees/views.py`, `employees/tests.py`, `templates/base.html`, `templates/home.html`,
  `config/views.py`, and this task brief.
- Public interfaces added/changed: `employees.services.create_employee_with_account`; account user
  list/create URL names; dashboard context keys `dashboard_title`, `dashboard_intro`, `stats`, and
  `quick_links`.
- Shared files requiring coordination: `templates/base.html`, `templates/home.html`,
  `config/views.py` (treated as owned by this integration task).

## Binding Context

- Relevant confirmed rules: Django authentication/groups; employees may access only their own
  private records; Admin and HR Manager manage employees; Payroll Officer manages payroll and has
  view-only employee/attendance access; authorization is enforced server-side.
- Relevant models/services/interfaces: Django `User`/`Group`; nullable `Employee.user` one-to-one;
  existing role groups; existing employee form and create view.
- Permission or object-access rule: Admin and HR Manager can provision HR Manager or Payroll
  Officer accounts; Payroll Officer and Employee cannot access those screens. New employee users
  receive only the Employee group. Dashboard data and links are scoped to the current role.
- Pending decision IDs: Q-001 does not affect this implementation; synthetic data only.
- Data classification: Synthetic only / no record data required.

## Acceptance Criteria

- [ ] Creating an employee atomically creates and links an active Django user whose username is the
      employee number, whose name/email mirror the employee, whose password verifies as
      `password1`, and whose only role is Employee.
- [ ] A username collision is a form error and creates neither an employee nor a partial account.
- [ ] Admin and HR Manager can open the separate user-management screen and create an HR Manager
      or Payroll Officer account; Payroll Officer, Employee, and anonymous users are denied or
      redirected.
- [ ] Admin/HR Manager, Payroll Officer, and Employee dashboards expose only their allowed stats and
      links; direct protected views remain server-enforced.
- [ ] The app header renders the user's full name, falling back to username, and never uses email as
      the identity label.

## Required Review

- Manual workflow review: Create a synthetic employee, log in with employee number/initial
  password, compare the sidebar/dashboard for Employee, HR Manager, and Payroll Officer, and verify
  denied staff-user management access.
- Migration or framework command: `python manage.py makemigrations --check --dry-run`,
  `python manage.py check`, focused tests, full `pytest`, and `ruff check .`.
- Expected observable result: No migration drift; all checks/tests pass; role-specific links are
  visible only to eligible roles; header shows a human name.

## AI Context Package

Provide only:

- `TEAM_CONTEXT.md`;
- this completed brief;
- relevant source files and public interfaces;
- any task-specific source that changed after the context file was generated.

Never include real employee/payroll data, secrets, `.env` files, database dumps, or production logs.

## Expected AI Output

Before code, the AI must restate the outcome, constraints, received files, blockers, and minimal
plan. After implementation, it must return changed files/diff, commands to run, assumptions, and
remaining risks without claiming unperformed work.
