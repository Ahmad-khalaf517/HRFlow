# HRFlow Feature and Access-Control Handbook

This handbook documents the behavior currently implemented in HRFlow and the approved target
rules that govern it. It covers feature logic, data models, workflows, user flows, validation,
and role-based access control (RBAC, also referred to as RAC).

Last reviewed against the repository: 2026-09-04.

## 1. How to read this document

### 1.1 Source precedence

When sources disagree, use this order:

1. Django migrations are the executable database-schema source.
2. Current models, forms, services, views, URLs, and tests describe implemented behavior.
3. `docs/business-rules.md` defines approved target business rules.
4. This handbook explains the first three sources but does not replace them.

`TEAM_CONTEXT.md`, `README.md`, and `docs/erd.md` contain some baseline statements that predate
the current feature implementation. A model alone also does not prove that a complete workflow
exists.

### 1.2 Status labels

| Label | Meaning |
|---|---|
| Implemented | A custom application flow or service exists and is covered by repository code. |
| Partial | Some behavior exists, but a target rule or end-to-end flow remains incomplete. |
| Admin only | The model is exposed through Django Admin, with no custom application workflow. |
| Target | Approved business behavior that is not completely enforced yet. |
| Pending | Requires an owner decision and must not be treated as approved. |
| Out of scope | Explicitly excluded from this MVP. |

### 1.3 Product boundary

HRFlow is a one-company, monthly-payroll demonstration system. Development and demonstration use
synthetic data only. It is not production payroll, a banking system, or a legal-compliance engine.
Formal product-scope decision Q-001 remains Pending, although the security policy independently
requires synthetic data.

Approved decisions Q-002 through Q-004 establish:

- one currency: USD;
- daily salary rate = basic salary / 30;
- hourly rate = daily rate / contract working hours per day;
- overtime rate = hourly rate x 1.5;
- leave days count Monday through Friday, without a holiday calendar.

## 2. Architecture and end-to-end flow

HRFlow is a Django monolith backed by PostgreSQL. Supabase hosts PostgreSQL only; authentication
uses Django's standard user, group, permission, and session tables.

```text
accounts -> employees -> attendance -> payroll
```

Payroll consumes attendance facts only through these public functions:

```python
get_employee_overtime_hours(employee, start_date, end_date)
get_absence_days(employee, start_date, end_date)
get_unpaid_leave_days(employee, start_date, end_date)
```

The intended business sequence is:

```text
User/role
  -> Employee -> Contract
  -> Attendance + approved Leave
  -> Bonus/Deduction + Tax configuration
  -> Payroll Draft -> Calculated -> Reviewed -> Approved
  -> Published payslip
  -> Payment -> Paid (target; not implemented end to end)
```

## 3. Roles and implemented access control

Four group names are seeded: `Admin`, `HR Manager`, `Payroll Officer`, and `Employee`. The seed
migration creates names only; it does not assign Django model permissions. Custom views authorize
mostly by checking group names, while Django Admin continues to use Django staff/superuser/model
permission behavior.

Legend: **Manage** means create/change/state actions, **View all** means directory-wide access,
**Own** means the linked `Employee.user` object only, and **Denied** means the custom application
returns 403 or hides unauthorized objects with 404.

| Feature | Admin | HR Manager | Payroll Officer | Employee |
|---|---|---|---|---|
| Staff user provisioning | Manage | Manage | Denied | Denied |
| Departments and positions | Manage | Manage | View | View |
| Employee directory | Manage | Manage | View all | Own profile only |
| Contracts | Manage | Manage | View all | Own history only |
| Attendance | Manage | Manage | View all | Own create/view/edit |
| Leave types | Manage | Manage | View | Denied |
| Leave requests | Manage/approve | Manage/approve | View all | Own submit/view |
| Bonuses/deductions/tax | Manage | Denied | Manage | Denied |
| Payroll runs/items | Manage | Denied | Manage | Denied |
| Published payslips | View all | Denied | View all | Own only |
| Payments | No custom flow | No custom flow | No custom flow | No custom flow |

Important implementation details:

- A user may belong to multiple groups; a matching privileged group is enough for most checks.
- `is_staff` alone grants no custom application privilege.
- Superuser behavior is not uniform. Payroll, attendance, and employee-directory viewing recognize
  superusers. Account and employee management mixins require the corresponding group even for a
  superuser. A superuser still needs Django Admin access rules for `/admin/`.
- Unauthenticated users are redirected to login for protected pages. `/health/` is public.
- Unauthorized employee, attendance, and leave object lookups often return 404 to avoid exposing
  whether another person's record exists. Some module-wide denials return a branded 403.
- Navigation visibility is convenience only; server-side view/service checks are authoritative.
- State-changing application actions are intended to use POST and Django CSRF middleware.

## 4. Authentication and account provisioning

**Status:** Implemented, with security gaps noted below.

### Logic and data model

- Uses Django `auth.User`; there is no custom user model.
- Passwords are stored using Django password hashing.
- Login uses `LoginView`, `AuthenticationForm`, `ModelBackend`, database sessions, and
  `AuthenticationMiddleware`.
- `Employee.user` optionally links one employee profile to one Django user.
- Groups hold roles. The application does not use Supabase Auth.

### Workflows and user flows

Login:

1. User opens `/accounts/login/`.
2. Django validates username and password.
3. A valid login creates a database-backed session and redirects to `/`.
4. Logout is submitted to `/accounts/logout/` and redirects to login.

Staff provisioning:

1. Admin or HR Manager opens `/accounts/users/`.
2. They select **New user** and enter username, name, email, and either HR Manager or Payroll
   Officer role.
3. The service creates the user atomically, hashes the initial password, and assigns one group.
4. The user appears in the staff list. Admin and Employee accounts are not created by this form.

Employee provisioning is coupled to employee creation and is described in section 8.

### Validation

- Username is trimmed, checked with Django username validators, and checked case-insensitively.
- Service validation allows only `HR Manager` and `Payroll Officer` staff roles.
- Database write and group assignment occur in one transaction.
- Email receives Django email-format validation but is not unique on `auth.User`.
- All provisioned accounts currently receive the shared initial password defined in code.

### RBAC and gaps

- Only members of Admin or HR Manager groups can list/create staff users.
- Payroll Officer, Employee, ungrouped staff, and a superuser without one of those groups are
  denied by the custom account-management views.
- There is no custom password-change, password-reset, forced-first-login change, account-disable,
  role-edit, user-delete, Admin-provisioning, or Employee-account-management screen.
- A shared default initial password without forced rotation is demonstration-only and is a
  production blocker.

## 5. Role-aware dashboard

**Status:** Implemented.

### Logic and workflow

The authenticated `/` dashboard derives its variant from group membership:

- Admin: company employee, present-today, pending-leave, and current-payroll summary.
- HR Manager: employee, attendance, and pending-leave summary.
- Payroll Officer: active-employee, present-today, current-payroll, and payroll-cycle summary.
- Other users: own employment, today's attendance, and own pending-leave summary when linked to an
  employee.

Quick links follow the same role split. Admin and Payroll Officer see the all-payslips entry;
Employee sees **My payslips**. The dashboard does not replace authorization checks on destination
views.

### Validation, RBAC, and gaps

- Login is required.
- Dashboard queries use the current local date supplied by Django, while project `TIME_ZONE` is
  currently UTC.
- The first matching branch wins: Admin, then HR Manager, then Payroll Officer, then employee-like
  fallback. Multiple roles can therefore produce a dashboard different from another module's
  union-of-groups permissions.
- An ungrouped user receives the fallback dashboard; without an employee link it contains only a
  generic account status.

## 6. Organization: departments

**Status:** Implemented.

### Data model

`Department` contains unique `name`, `description`, optional `manager -> Employee` (`SET_NULL`),
`is_active`, and create/update timestamps. A department contains positions and may contain
employees through their foreign keys.

### Logic and user flow

1. Any authenticated user can list and view departments.
2. Admin/HR Manager can create or edit name, description, and manager.
3. Admin/HR Manager can deactivate a department with POST.
4. Lists can search by name and filter active/inactive state.

Deactivation is a soft state change. It does not move employees, deactivate positions, clear the
manager, or prevent the department from being selected elsewhere.

### Validation and RBAC

- Form rejects a blank/whitespace name and case-insensitive duplicate name.
- Database enforces exact-value uniqueness on name.
- Manager is optional and protected only by normal foreign-key validity; the manager is not
  required to belong to the department.
- View: every authenticated user. Manage/deactivate: Admin or HR Manager group only.
- There is no reactivate route or hard-delete route in the custom UI.

## 7. Organization: positions

**Status:** Implemented.

### Data model

`Position` contains required `department`, `title`, optional `code`, optional `description`,
optional `min_salary`/`max_salary`, `is_active`, and timestamps. `(department, title)` is unique at
the database level.

### Logic and user flow

1. Any authenticated user can list/view positions and salary ranges.
2. Admin/HR Manager can create or edit a position.
3. Admin/HR Manager can deactivate it with POST.
4. Lists support title/code search and department/status filters.

### Validation and RBAC

- Form rejects negative salary bounds.
- Form requires maximum salary to be at least minimum salary.
- Form checks title uniqueness case-insensitively inside the selected department.
- Database uniqueness is exact/case-sensitive according to database collation and has no salary
  range check constraint.
- Employee assignment validates that the selected position belongs to the selected department.
- The position salary range is advisory: contract salary is not validated against it.
- View: every authenticated user. Manage/deactivate: Admin or HR Manager only.
- There is no custom reactivate or delete flow.

## 8. Employees and employee accounts

**Status:** Implemented.

### Data model

`Employee` contains optional one-to-one `user`, unique `employee_number`, first/last name, unique
email, phone, optional date of birth, address, hire date, optional department/position,
`employment_status` (`active`, `inactive`, `terminated`), synthetic-demo bank name/account number,
`is_active`, and timestamps.

`is_active` is an employee-domain flag; it is separate from `auth.User.is_active`.

### Logic and workflows

Create:

1. Admin/HR Manager completes the employee form.
2. A transaction saves the employee and creates a linked Django user.
3. Username is the employee number; first name, last name, and email are copied.
4. Password is set using Django hashing and the Employee group is assigned.
5. Any failure rolls back both records.

Update:

1. Admin/HR Manager edits the profile.
2. Employee fields are saved.
3. Linked username, name, and email are synchronized in the same transaction.

Lifecycle:

- **Deactivate** sets employment status inactive and employee `is_active=False`.
- **Reactivate** sets employment status active and employee `is_active=True`.
- **Terminate** sets employment status terminated and employee `is_active=False`.
- These actions do not disable the linked login, end/deactivate contracts, or alter historical
  attendance/payroll data.

### User flow

- Admin/HR Manager browse, filter, create, view, edit, deactivate/reactivate/terminate.
- Payroll Officer can browse the full employee directory and contract information read-only.
- Employee cannot open the directory list but may open their own profile and contract tab by URL.
- Search supports name, employee number, or email; filters cover department, employment status,
  and active contract type.

### Validation and RBAC

- Employee number and email are trimmed and checked case-insensitively against employees.
- Employee number must also satisfy Django username validators and must not collide with another
  username.
- Database enforces unique employee number and email, subject to database collation semantics.
- Position must belong to the selected department.
- Form saves keep `employment_status` and employee `is_active` consistent.
- There is no validation for future birth/hire dates, age, hire-before-birth, department active
  state, position active state, or position salary range.
- Bank fields are plaintext and may contain synthetic values only. Real bank data is prohibited.
- Manage: Admin/HR Manager. View all: Admin/HR Manager/Payroll Officer or superuser. Own detail:
  linked user. Unauthorized object access returns 404.

## 9. Contracts

**Status:** Implemented.

### Data model

`Contract` contains employee, type (`full_time`, `part_time`, `contract`, `probation`), start/end
dates, basic salary, default allowances, working hours/day, working days/week, optional probation
end date, status (`active`, `inactive`, `terminated`), and timestamps.

Database rules:

- one active contract per employee through a conditional unique constraint;
- end date is null or not before start date;
- basic salary is nonnegative;
- employee deletion is protected while referenced.

### Logic and workflow

1. Admin/HR Manager creates a contract for an employee.
2. Contract history is preserved as multiple non-overlapping rows.
3. A contract may be deactivated, reactivated, or terminated by POST.
4. Payroll selects the employee's active contract; employees without one are skipped.

### Validation

- End date cannot precede start date.
- Basic salary and allowances cannot be negative in the form.
- Working hours/day must be greater than zero in the form.
- Working days/week must be 1 through 7 in the form.
- Only one active contract is checked in form and database.
- Model validation rejects overlapping date ranges for the same employee regardless of contract
  status when using normal validated forms.
- Overlap, allowances, hours, and 1-7 working-day rules are not all backed by database constraints.
- Reactivation directly saves status after checking only for another active contract; it does not
  re-run the full date-overlap validation.
- Probation end date has no ordering validation.
- Payroll does not currently verify that the active contract dates cover the payroll period.

### RBAC

- Manage/state actions: Admin/HR Manager.
- Full list: Admin/HR Manager/Payroll Officer or superuser.
- Detail/history: same full-view roles, plus employee's linked user for their own contract.

## 10. Attendance

**Status:** Implemented.

### Data model

`Attendance` contains employee, local work date, optional check-in/check-out, derived worked and
overtime hours, status (`present`, `absent`, `late`, `leave`, `holiday`, `weekend`), notes, and
timestamps.

Database rules enforce one row per employee/date, check-out after check-in when both exist, and
nonnegative worked/overtime hours.

### Logic

- Missing either time produces `0.00` worked and overtime hours.
- With both times, worked hours are the same-day time difference, rounded to two decimals using
  `ROUND_HALF_UP`.
- Standard daily hours come from the employee's active contract; without one the threshold is
  zero.
- Overtime is `max(worked_hours - working_hours_per_day, 0)`, rounded to two decimals.
- Attendance stores hours/facts only; it never stores money.
- Overnight shifts are rejected because check-out must be later on the same date.

### User flow

1. Admin/HR Manager can create or edit a record for any employee.
2. An employee with a linked profile can create and edit their own record; the employee choice is
   restricted to that profile.
3. Payroll Officer can view all records and the aggregate summary but cannot manage records for
   others.
4. Lists support date, department, employee, and status filters. Summary reports total rows,
   present/absent counts, worked hours, and overtime hours.

### Validation and RBAC

- Form and database both reject duplicate employee/date rows.
- Model and database reject check-out at/before check-in.
- Derived hours are recalculated during normal model save, so posted hour values are not accepted.
- There is no semantic validation tying status to time fields: for example, an absent record may
  still contain times.
- There is no shift, break, grace-period, lateness deduction, holiday-calendar, future-date, or
  timesheet-approval rule.
- Manage all: Admin/HR Manager or superuser. View all: those roles plus Payroll Officer. Own
  create/view/edit: linked employee user. Unauthorized object detail/edit returns 404.

## 11. Leave types

**Status:** Implemented.

### Data model and logic

`LeaveType` contains unique name, nonnegative annual allowance, `is_paid`, `requires_approval`, and
`is_active`.

Admin/HR Manager can list, create, and edit types. Payroll Officer can list them read-only.
Employees cannot access the leave-type list. New requests show active types only.

### Validation and gaps

- Name is trimmed, required, and unique at the database level.
- Annual allowance uses a positive integer field.
- There is no delete route; types are deactivated through edit.
- Annual allowance is configuration only: balances and allowance consumption are not enforced.
- `requires_approval` is stored but does not change the request workflow; every new request starts
  Pending and needs the normal review transition.

## 12. Leave requests and approval

**Status:** Implemented, without cancellation/balance workflows.

### Data model

`LeaveRequest` contains employee, leave type, start/end dates, system-derived requested days,
reason, status (`pending`, `approved`, `rejected`, `cancelled`), approver, approval timestamp, and
create/update timestamps.

### Logic

- Requested days count inclusive Monday-Friday days and exclude weekends.
- No holiday calendar or half-day calculation is used.
- Pending/approved ranges for one employee may not overlap during normal validated saves.
- Review service locks the request, accepts only Pending -> Approved or Pending -> Rejected,
  records actor/time, and rejects self-review.
- Rejected leave does not affect payroll.
- Public payroll facts count only approved, unpaid leave intersecting the payroll period.

### User flows

Employee:

1. Opens **My Leave Requests** and selects **New request**.
2. Chooses an active leave type, dates, and optional reason; employee identity is forced to self.
3. System derives weekday count and saves Pending.
4. Employee can view only their own request/detail.

Admin/HR Manager:

1. Can create a request for any employee.
2. Opens the pending approval queue.
3. Approves or rejects using POST.
4. Decision records reviewer and time.

Payroll Officer can read all leave requests and the pending queue but cannot approve or reject.

### Validation and RBAC

- End date cannot precede start date at model and database layers.
- Requested days are nonnegative and not editable in the form.
- Durations above the `Decimal(5,2)` supported maximum are rejected.
- Overlap prevention is application-level with an employee row lock; there is no PostgreSQL
  exclusion constraint.
- Employees cannot forge another employee ID through the request form.
- A reviewer cannot approve/reject a request linked to their own user.
- There is no request-edit or cancellation route even though `cancelled` is a model choice.
- No past-date, notice-period, attachment, leave-balance, manager hierarchy, or delegated approval
  validation exists.

## 13. Bonuses

**Status:** Implemented as a simple active/cancelled payroll input.

### Data model and payroll logic

`Bonus` contains employee, free-text type, nonnegative amount, effective date, description, status
(`active`, `cancelled`), creator, and timestamps. During calculation, all active bonuses for the
employee whose effective dates fall inside the payroll period are summed.

### User flow

1. Admin/Payroll Officer records a bonus.
2. A future/today bonus may be edited.
3. A future/today bonus may be cancelled with POST.
4. Once its effective date is before today, the custom UI blocks edit and cancellation.
5. Active in-period bonuses are copied into the payroll snapshot on calculation.

### Validation, RBAC, and gaps

- Amount is nonnegative in form and database.
- Creator is set from the current user.
- Only Admin/Payroll Officer or superuser can access bonus pages.
- There is no approval state, restoration route, delete route, uniqueness rule, currency field, or
  protection against editing an input after a Draft/Calculated run already consumed it. A later
  recalculation will use the latest still-active inputs.

## 14. Manual deductions

**Status:** Implemented as a simple active/cancelled payroll input.

### Data model and payroll logic

`ManualDeduction` contains employee, type (`loan`, `insurance`, `advance_repayment`,
`disciplinary`, `other`), nonnegative amount, effective date, description, active/cancelled status,
creator, and timestamps. Active in-period deductions are summed during payroll calculation.

Absence and unpaid leave are not manual deductions; payroll derives those from attendance facts.

### User flow, validation, and RBAC

- Admin/Payroll Officer or superuser can list, create, and cancel deductions.
- Amount is nonnegative in form and database; creator is recorded.
- Cancellation uses POST. Unlike bonuses, the current UI allows cancelling past-effective
  deductions.
- There is no custom edit, restore, delete, approval, installment/loan-balance, or uniqueness flow.

## 15. Tax configuration

**Status:** Implemented as a demonstrative non-progressive selector.

### Data model and calculation

`TaxBracket` contains name, minimum amount, optional maximum, percentage, fixed amount, active
flag, and timestamps.

For each employee gross salary, payroll chooses the first active bracket ordered by minimum amount
where `min <= gross` and maximum is null or `max >= gross`:

```text
Tax = fixed amount + (gross salary * percentage / 100)
```

If no bracket matches, tax is zero. This is one selected bracket, not progressive taxation and not
legal tax compliance.

### User flow and validation

1. Admin/Payroll Officer creates a bracket.
2. They can toggle it active/inactive with POST.
3. Active matching configuration is snapshotted during payroll calculation.

- Minimum and percentage are nonnegative in form and database.
- Maximum, when supplied, must be at least minimum in form and database.
- Fixed amount is nonnegative in the form, but the current database has no matching fixed-amount
  check constraint.
- Overlapping or duplicate ranges are not rejected. With overlaps, the lowest ordered minimum may
  win, which can make another matching bracket unreachable.
- There is no custom update route; configuration is changed by adding/toggling brackets.

## 16. Payroll runs and calculation

**Status:** Implemented through approval. Payment-to-Paid is incomplete.

### Data model

`Payroll` contains derived period start/end, month/year, status (`draft`, `calculated`, `reviewed`,
`approved`, `paid`), total gross/deductions/net, USD currency, creator, reviewer/approval actors and
timestamps, and creation timestamp. `(month, year)` is unique.

`PayrollItem` is one employee snapshot per run and contains:

- employee and protected contract references;
- employee number/name, currency, and calculation version snapshots;
- JSON calculation inputs with Decimal values serialized as strings;
- salary, allowance, overtime, bonus, absence, unpaid-leave, manual-deduction, tax, totals, and
  timestamps.

### Run creation

1. Admin/Payroll Officer selects month and year.
2. Service validates month 1-12 and year 2000-2100.
3. It derives the first and last calendar dates and creates a Draft run.
4. Database rejects a second run for the same month/year.

Direct model writes do not independently enforce valid month range or period/month consistency;
the custom service is the supported creation interface.

### Calculation eligibility and inputs

Calculation includes employees where both employee flags indicate active and an active contract
exists. It skips employees without an active contract. It does not currently test contract date
coverage against the payroll period.

For each included employee it reads:

- basic salary, allowances, and standard hours from the active contract;
- overtime hours, absence days, and approved unpaid-leave days from attendance services;
- active in-period bonuses and manual deductions;
- the first matching active tax bracket.

### Formula

All monetary components use `Decimal`, two decimal places, and `ROUND_HALF_UP` for calculated
money:

```text
Daily rate = Basic salary / 30
Hourly rate = Daily rate / Contract hours per day
Overtime pay = Overtime hours * Hourly rate * 1.5

Gross = Basic salary + Allowances + Overtime pay + Bonuses

Total deductions =
  Absence days * Daily rate
  + Unpaid leave days * Daily rate
  + Manual deductions
  + Fixed tax amount + (Gross * tax percentage / 100)

Net = Gross - Total deductions
```

### Calculation workflow

- Draft -> Calculated creates or updates one item per eligible employee.
- Calculated -> Calculated recalculates the snapshots and removes items for employees who are no
  longer eligible.
- Calculation rejects negative inputs, nonpositive contract hours, negative tax inputs, and net
  salary below zero.
- Run totals are aggregated from saved items in the same transaction.
- An empty eligible population is not explicitly rejected; the run can calculate with zero items.

### Review and approval workflow

```text
Draft --calculate--> Calculated --review--> Reviewed --approve--> Approved
```

- Only Calculated can be reviewed; reviewer and timestamp are recorded.
- Only Reviewed can be approved; approver and timestamp are recorded.
- Admin/Payroll Officer or superuser may perform every step.
- Separation of duties is out of scope, so creator, reviewer, and approver may be the same user.
- There is no rollback/reopen/reject transition from Reviewed or Approved.

### Immutability and validation

- Approved/Paid `Payroll` normal saves reject amount/actor/date edits and unauthorized status
  changes; approved may advance to paid without changing other fields.
- Approved/Paid runs cannot be deleted through normal model deletion.
- `PayrollItem` normal save/delete locks its parent and rejects changes under Approved/Paid.
- All item numeric fact/money fields have a combined nonnegative database check.
- Admin makes Payroll and PayrollItem read-only by disabling add/change/delete.
- There is no database immutability trigger; direct SQL and bulk ORM updates are outside the
  authorized interface and can bypass model guards.

### RBAC

All run list/create/detail/calculate/review/approve pages require Admin or Payroll Officer; the
shared helper also recognizes superuser. HR Manager and Employee receive 403.

## 17. Payslips

**Status:** Implemented as read-only rendering from complete approved snapshots.

### Data model and publication rule

`Payslip` is optional one-to-one file metadata for a PayrollItem. The custom payslip pages do not
require or generate that file; the authoritative display is rendered directly from saved
PayrollItem fields.

An item is published only when:

- parent payroll is Approved or Paid;
- contract snapshot reference exists;
- calculation version, currency, employee number, and employee name snapshots are present; and
- calculation input JSON contains contract, period, daily/hourly rates, multiplier, and tax keys.

Legacy/incomplete items remain unavailable instead of being reconstructed from current live data.

### User flow

1. After approval, Admin/Payroll Officer sees all published items and can filter by period,
   status, current department, employee name, or number.
2. Employee sees only published items linked through `PayrollItem.employee.user`; filters cannot
   widen that scope.
3. Detail renders saved earnings and deductions and can be printed by the browser.
4. Pages accept safe methods only and are marked `never_cache`.

### RBAC and gaps

- All published payslips: Admin/Payroll Officer or superuser.
- Own published payslips: active authenticated Employee-group user. The employee domain record may
  be inactive as long as the login remains active.
- HR Manager is denied because the target word **Limited** has not been defined by the owner.
- `is_staff` alone grants no access. Unauthorized/missing/unpublished item detail returns the
  unavailable 404 response.
- No PDF/file generation, email delivery, acknowledgement, or employee download audit is
  implemented.

## 18. Payments and Paid status

**Status:** Model registered in Django Admin only; target workflow not implemented.

### Current data model

`Payment` contains payroll item, nonnegative amount, date, free-text method/reference, status
(`pending`, `completed`, `failed`, `cancelled`), creator, and creation timestamp. The relation is a
normal foreign key, so the database permits multiple payments per item.

### Current behavior

- Payment is registered in Django Admin.
- There is no custom payment form, URL, service, or role-aware application page.
- There is no service that requires an Approved parent, enforces exactly one completed payment,
  compares amount with net salary, records a completion transition, or advances the payroll to
  Paid after all items are paid.
- The model only enforces nonnegative amount. Direct Admin behavior depends on Django Admin
  permissions and does not implement the target payroll payment invariants.

### Target workflow

The approved target rule is one completed payment equal to the item's net salary, permitted only
for an Approved item. After every item has that payment, the payroll becomes Paid. Partial,
excessive, refunded, reversed, and correction payments are out of scope. This target must not be
described as implemented.

## 19. Django Admin

**Status:** Implemented as an operator/developer interface, not the primary guarded workflow.

- All domain models are registered.
- Payroll and PayrollItem disable Admin add/change/delete so their service workflow remains the
  normal write path.
- Bonus, deduction, tax, payslip metadata, payment, employee, attendance, leave, and organization
  models remain editable according to Django Admin permissions and model validation behavior.
- Custom group-name checks used by application views do not automatically grant Django Admin
  model permissions.
- Admin must not be treated as a substitute for object-level application authorization or missing
  payment/workflow services.

## 20. Cross-cutting validation and security

### Validation layers

| Layer | Responsibility |
|---|---|
| Browser widgets | Input hints such as date controls and `min=0`; never trusted alone. |
| Django forms | Friendly field/cross-field errors and restricted querysets. |
| Models/services | Derived values, state transitions, authorization, locks, and transactions. |
| Database | Foreign keys, uniqueness, selected check constraints, and durable integrity. |

Not every form rule has a matching database constraint. Supported custom views/services must be
used; bulk updates and direct SQL are not authorized domain interfaces.

### Security controls

- Django session authentication and password hashing.
- CSRF middleware; important state actions use POST.
- Object scoping for own-profile, own-attendance, own-leave, and own-payslip access.
- Transactions and row locks around leave decisions, leave-overlap serialization, payroll
  calculation/transitions, and payroll snapshot edits.
- `PROTECT` preserves referenced employee, contract, payroll, and payroll-item history.
- Synthetic data only. Do not put real employee, salary, leave-reason, bank, tax, payment, or
  payslip data in this MVP.
- Do not log or commit credentials, `.env`, database URLs, tokens, cookies, dumps, or production
  data.

### Production-readiness blockers

- Plaintext demo bank-account field.
- Shared initial password and no forced password rotation/reset flow.
- No complete permission assignments or unified authorization policy.
- No immutable general audit history.
- No payment invariant service.
- No sensitive-field encryption/masking policy beyond display helpers.
- No jurisdiction/legal payroll rules, retention, backup, monitoring, incident, or operational
  security review.

## 21. End-to-end user journeys

### 21.1 HR setup and leave journey

```text
Admin/HR creates department and position
  -> creates employee + linked Employee login
  -> creates active contract
  -> Admin/HR or employee records attendance
  -> employee submits leave
  -> Admin/HR approves or rejects
  -> approved unpaid leave becomes a payroll fact
```

### 21.2 Payroll journey

```text
Admin/Payroll Officer configures tax and adjustments
  -> creates monthly Draft run
  -> calculates eligible employee snapshots
  -> checks employee breakdown and totals
  -> marks Reviewed
  -> approves and locks the run
  -> published payslips become visible by role
  -> payment/Paid completion is not implemented
```

### 21.3 Employee self-service journey

```text
Employee signs in with employee-number username
  -> sees own dashboard
  -> views own profile and contract history
  -> creates/views/edits own attendance
  -> submits/views own leave
  -> views own complete payslips after payroll approval
```

## 22. Explicitly out of scope

Recruitment, performance management, multiple companies/countries/currencies, legal-compliance
tax/payroll, progressive tax, proration, mid-period contract rules, advanced shifts, breaks,
overnight attendance, holiday calendars, half days, leave balances, notifications, bank/accounting
integrations, partial payments, reversals/corrections, and a general-purpose audit subsystem are
outside this MVP.

## 23. Maintainer checklist

Update this handbook when a feature changes:

1. Confirm migrations and models.
2. Confirm service formulas/transitions and public boundaries.
3. Confirm form and database validation separately.
4. Test allowed and denied roles, including object-level access.
5. Mark target behavior as implemented only when the end-to-end workflow exists.
6. Preserve Pending decisions and record owner/date before relying on a new policy.
7. Use synthetic examples only and review the diff for Restricted data.
