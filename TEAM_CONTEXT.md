# HRFlow Team Context and Development Prompt

This is the single self-contained onboarding context for HRFlow teammates and their AI tools.

## How to use this file

### Repository-integrated AI agent

Send this message:

```text
Read TEAM_CONTEXT.md completely before acting. Then inspect the current task's relevant code and migrations. Follow the three-person ownership boundaries, report any conflict with the context, and do not implement rules marked Pending. Start by returning your task understanding, dependencies, allowed files, public interfaces, acceptance criteria, and verification plan before editing.
```

The repository's `AGENTS.md`/`CLAUDE.md` adapters may add tool-specific instructions, but this file contains the complete project onboarding context.

### Browser-based AI

Paste this entire file into a new conversation, followed by one completed task brief and only the smallest relevant sanitized code excerpts. Never paste `.env`, database URLs, credentials, real employee data, production rows, logs, or screenshots.

### Human teammate

Read the current baseline, three-person task split, pending decisions, and schema gaps before selecting work. Use `docs/task-brief-template.md` for the branch/PR.

---

## 1. Project mission

HRFlow is a seven-calendar-day Django HR and payroll MVP. It uses synthetic demonstration data and is not production payroll or a legal-compliance system.

Required end-to-end flow:

```text
Employee -> Contract -> Attendance/Leave -> Payroll -> Payslip -> Payment
```

Primary apps and dependency direction:

```text
accounts -> employees -> attendance -> payroll
```

Do not reverse this direction. Payroll may consume attendance facts only through public attendance service functions.

## 2. Current implementation baseline

Implemented now:

- Django project/settings and Supabase PostgreSQL connection;
- Django login/logout, password hashing, database sessions, and login-required dashboard;
- four role-group names seeded by migration: Admin, HR Manager, Payroll Officer, Employee;
- all current domain models, initial migrations, and Django Admin registrations;
- base authenticated/auth templates, login page, dashboard shell, and reusable form field partial;
- Tailwind 4 design tokens/component utilities and tracked compiled CSS;
- 13 foundational tests for auth/dashboard/groups and selected uniqueness constraints.

Not implemented yet:

- role permission assignments and comprehensive object-level authorization;
- custom employee/contract forms, views, URLs, templates, and services;
- attendance hour calculation services and custom workflows;
- leave requested-day calculation, overlap prevention, and guarded approval/rejection services;
- payroll input workflows beyond Django Admin;
- payroll calculation, complete snapshots, immutability, and guarded transitions;
- own-record payslip and one-full-payment workflows;
- complete synthetic fixtures and end-to-end integration scenario.

Current application routes:

```text
/                         authenticated dashboard
/accounts/login/          Django LoginView
/accounts/logout/         POST Django LogoutView
/admin/                   Django Admin
```

Do not claim an incomplete workflow is already implemented merely because its database model exists.

## 3. Three-person delegation plan

Use exclusive app ownership to avoid task and migration coupling.

| Person | Owns | First task wave | Must not do |
|---|---|---|---|
| Person 1 | `employees` | Employee/contract forms, services, permissions, URLs, screens, tests | Edit attendance/payroll internals or their migrations |
| Person 2 | `attendance` | Attendance calculations; leave submit/approve/overlap workflow; public fact services | Calculate money or edit payroll internals |
| Person 3 | `payroll` | Bonus/deduction/tax workflows and payroll state scaffolding | Start payroll formulas before Q-002–Q-004 and attendance contracts are ready |

### Dependency-safe start sequence

1. All three people agree on canonical model names and the public service signatures below.
2. Each person creates a task brief and branch from the same integration commit.
3. Each person owns migrations for only their app; no competing migration files in one app.
4. Shared files use a short integration queue with one temporary owner at a time.
5. Merge small prerequisite/interface PRs before dependent implementation PRs.
6. Rebase/merge the integration branch frequently; run all tests after each integration.

Shared files requiring queue ownership include:

```text
config/settings.py
config/urls.py
config/views.py
templates/base.html
templates/auth_base.html
static/css/src/input.css
static/css/dist/output.css
```

### Required public attendance boundary

Person 2 owns and tests functions with stable signatures such as:

```python
get_employee_overtime_hours(employee, start_date, end_date)
get_absence_days(employee, start_date, end_date)
get_unpaid_leave_days(employee, start_date, end_date)
```

Person 3 imports these functions from the public attendance service module. Payroll must not directly query `Attendance` or `LeaveRequest`, import attendance forms/views, or reproduce attendance rules.

Person 1 publishes only the smallest employee/contract helpers needed by Persons 2 and 3. Avoid a generic “shared utilities” dumping ground.

### Suggested merge order

1. Person 1 merges any required employee/contract interface adjustment.
2. Person 2 merges public attendance service contracts and contract tests.
3. Person 3 integrates those services into payroll only after Q-002–Q-004 are confirmed.
4. Shared URL/navigation/template integration is performed by the current integration owner.

## 4. Technology and library rationale

### Python/server

| Library | Version policy | Purpose |
|---|---|---|
| Python | 3.12+ | Runtime and Decimal-based domain logic |
| Django | `>=5.0,<6.0` | ORM, migrations, auth, sessions, Admin, forms, templates, security middleware |
| `psycopg[binary]` | `>=3.1` | PostgreSQL driver |
| `dj-database-url` | requirements lock | Parses `DATABASE_URL` into Django settings |
| `python-dotenv` | requirements lock | Loads local `.env`; secrets remain uncommitted |
| `django-widget-tweaks` | requirements lock | Applies design classes to Django form widgets in templates |
| `django-filter` | requirements lock | Planned reusable list filtering |
| pytest + pytest-django | requirements lock | Test runner and Django integration |
| Ruff | requirements lock | Linting/import/style checks; Python target 3.12, line length 100 |

### Frontend

| Library | Version | Purpose |
|---|---|---|
| Node.js | 20+ | Required by locked Tailwind dependency tree |
| Tailwind CSS | 4.3.3 | CSS-first tokens/utilities and template scanning |
| `@tailwindcss/cli` | 4.3.3 | Builds source CSS into tracked output |
| Hanken Grotesk | 400/600/700 | Primary UI typeface |
| JetBrains Mono | 400 | Currency, IDs, and aligned numeric data |

Alpine.js and HTMX are not installed. Add one only for a clearly scoped small interaction and only with approval. Do not add React, Vue, another primary app, or another auth system.

## 5. Supabase and authentication

Supabase is used only as the PostgreSQL host. The application does not use Supabase Auth.

```text
Login form
  -> Django LoginView / AuthenticationForm
  -> Django ModelBackend
  -> public.auth_user in Supabase PostgreSQL
  -> Django password-hash verification
  -> public.django_session
  -> AuthenticationMiddleware restores request.user
```

Consequences:

- users created by `python manage.py createsuperuser` are written to the configured Supabase database;
- Django users appear in `public.auth_user`, not Supabase Auth's `auth.users` dashboard;
- roles use Django `auth_group`/permissions;
- never add Supabase client-side auth alongside Django auth without an approved architecture change.

## 6. Repository structure

```text
HRP/
├── AGENTS.md / CLAUDE.md       tool-specific pointers
├── TEAM_CONTEXT.md             this self-contained team handoff
├── README.md                   setup and documentation map
├── manage.py
├── requirements.txt
├── pyproject.toml              Ruff and pytest configuration
├── package.json / lock         Tailwind build tooling
├── config/
│   ├── settings.py             environment, apps, middleware, DB, static settings
│   ├── urls.py                 root routes
│   └── views.py                cross-domain dashboard
├── accounts/
│   ├── forms.py / urls.py      Django login/logout UI
│   ├── migrations/             role-group seed
│   └── tests.py
├── employees/
│   ├── models.py / admin.py
│   ├── migrations/
│   ├── tests.py
│   └── views.py                placeholder
├── attendance/
│   ├── models.py / admin.py
│   ├── migrations/
│   ├── tests.py
│   └── views.py                placeholder
├── payroll/
│   ├── models.py / admin.py
│   ├── migrations/
│   ├── tests.py
│   └── views.py                placeholder
├── templates/
│   ├── base.html               authenticated app shell
│   ├── auth_base.html          centered auth shell
│   ├── home.html               dashboard
│   ├── accounts/login.html
│   └── components/field.html   reusable Django field renderer
├── static/css/
│   ├── src/input.css           Tailwind tokens and component utilities
│   └── dist/output.css         generated, tracked deployable CSS
├── docs/
│   ├── business-rules.md       canonical target rules/pending decisions
│   ├── erd.md                  exact current migrated schema/gaps
│   ├── design-system.md        full UI usage guide
│   ├── delivery-plan.md        roadmap and work packages
│   ├── security-and-data-policy.md
│   └── task-brief-template.md
└── tools/build-ai-context.ps1  sanitized bounded-context bundler
```

## 7. Exact repository migration state

Django migrations are the only executable schema source. There is no parallel SQL schema. `makemigrations --check --dry-run` must report no drift.

### Global conventions

- Every custom table has a `BigAutoField`/PostgreSQL bigint primary key named `id`.
- `decimal(p,s)` means Django `DecimalField(max_digits=p, decimal_places=s)`.
- `?` means nullable; quoted/number values after `=` are ORM defaults.
- All `created_at`/`updated_at` fields are ORM-managed.
- Choices are application metadata, not PostgreSQL checks.
- Foreign keys and unique constraints are indexed automatically.

### Accounts/framework schema

There is no custom User model. Django creates `auth_user`, `auth_group`, `auth_permission`, join tables, `django_session`, `django_admin_log`, `django_content_type`, and `django_migrations`.

The accounts migration seeds group names `Admin`, `HR Manager`, `Payroll Officer`, and `Employee`; it assigns no permissions.

### Employees models

```text
Department
  name varchar(150) unique
  description text = ""
  manager FK -> Employee? SET_NULL
  created_at, updated_at

Position
  department FK -> Department PROTECT
  title varchar(150)
  code varchar(50) = ""
  description text = ""
  min_salary decimal(12,2)?
  max_salary decimal(12,2)?
  is_active bool = true
  created_at, updated_at
  UNIQUE(department, title)

Employee
  user one-to-one -> auth.User? SET_NULL
  employee_number varchar(30) unique
  first_name varchar(100)
  last_name varchar(100)
  email varchar(254) unique
  phone varchar(30) = ""
  date_of_birth date?
  address text = ""
  hire_date date
  department FK -> Department? SET_NULL
  position FK -> Position? SET_NULL
  employment_status varchar(20) = active [active, inactive, terminated]
  bank_name varchar(150) = ""
  bank_account_number varchar(50) = ""
  is_active bool = true
  created_at, updated_at

Contract
  employee FK -> Employee PROTECT
  contract_type varchar(30) = full_time [full_time, part_time, contract, probation]
  start_date date
  end_date date?
  basic_salary decimal(12,2)
  allowances_default decimal(12,2) = 0
  working_hours_per_day decimal(4,2) = 8
  working_days_per_week positive smallint = 5
  probation_end_date date?
  status varchar(20) = active [active, inactive, terminated]
  created_at, updated_at
  UNIQUE(employee) WHERE status=active
  CHECK(end_date is null or end_date >= start_date)
  CHECK(basic_salary >= 0)
```

### Attendance models

```text
Attendance
  employee FK -> Employee PROTECT
  date date
  check_in time?
  check_out time?
  worked_hours decimal(5,2) = 0
  overtime_hours decimal(5,2) = 0
  status varchar(20) = present [present, absent, late, leave, holiday, weekend]
  notes text = ""
  created_at, updated_at
  UNIQUE(employee, date)
  CHECK(check_in or check_out null, otherwise check_out > check_in)
  CHECK(worked_hours >= 0 and overtime_hours >= 0)

LeaveType
  name varchar(100) unique
  annual_allowance positive integer = 0
  is_paid bool = true
  requires_approval bool = true
  is_active bool = true
  no timestamp fields

LeaveRequest
  employee FK -> Employee PROTECT
  leave_type FK -> LeaveType PROTECT
  start_date date
  end_date date
  requested_days decimal(5,2) = 0, non-editable in generated model forms
  reason text = ""
  status varchar(20) = pending [pending, approved, rejected, cancelled]
  approved_by FK -> auth.User? SET_NULL
  approved_at datetime?
  created_at, updated_at
  CHECK(end_date >= start_date)
  CHECK(requested_days >= 0)
  no overlap constraint yet
```

### Payroll models

```text
Bonus
  employee FK -> Employee PROTECT
  bonus_type varchar(50) = ""
  amount decimal(12,2)
  effective_date date
  description text = ""
  status varchar(20) = active [active, cancelled]
  created_by FK -> auth.User? SET_NULL
  created_at, updated_at
  CHECK(amount >= 0)

ManualDeduction
  employee FK -> Employee PROTECT
  deduction_type varchar(30) = other
    [loan, insurance, advance_repayment, disciplinary, other]
  amount decimal(12,2)
  effective_date date
  description text = ""
  status varchar(20) = active [active, cancelled]
  created_by FK -> auth.User? SET_NULL
  created_at, updated_at
  CHECK(amount >= 0)

TaxBracket
  name varchar(100)
  min_amount decimal(12,2)
  max_amount decimal(12,2)?
  percentage decimal(5,2)
  fixed_amount decimal(12,2) = 0
  is_active bool = true
  created_at, updated_at
  CHECK(min_amount >= 0)
  CHECK(percentage >= 0)
  CHECK(max_amount is null or max_amount >= min_amount)

Payroll
  period_start date
  period_end date
  month positive smallint
  year positive smallint
  status varchar(20) = draft [draft, calculated, reviewed, approved, paid]
  total_gross decimal(14,2) = 0
  total_deductions decimal(14,2) = 0
  total_net decimal(14,2) = 0
  currency_code varchar(3) = USD (schema default only; Q-002 remains Pending)
  created_by FK -> auth.User PROTECT
  reviewed_by FK -> auth.User? SET_NULL
  approved_by FK -> auth.User? SET_NULL
  created_at
  reviewed_at datetime?
  approved_at datetime?
  UNIQUE(month, year)

PayrollItem
  payroll FK -> Payroll PROTECT
  employee FK -> Employee PROTECT
  basic_salary decimal(12,2)
  allowances decimal(12,2) = 0
  overtime_hours decimal(5,2) = 0
  overtime_amount decimal(12,2) = 0
  bonus_amount decimal(12,2) = 0
  gross_salary decimal(12,2) = 0
  absence_days decimal(5,2) = 0
  absence_deduction decimal(12,2) = 0
  unpaid_leave_days decimal(5,2) = 0
  unpaid_leave_deduction decimal(12,2) = 0
  manual_deduction_amount decimal(12,2) = 0
  tax_amount decimal(12,2) = 0
  total_deductions decimal(12,2) = 0
  net_salary decimal(12,2) = 0
  created_at, updated_at
  UNIQUE(payroll, employee)
  no nonnegative checks or database immutability enforcement yet

Payslip
  payroll_item one-to-one -> PayrollItem PROTECT
  file FileField/varchar(100)? upload_to=payslips/
  generated_at

Payment
  payroll_item FK -> PayrollItem PROTECT (not unique)
  amount decimal(12,2)
  payment_date date
  payment_method varchar(30) = ""
  reference_number varchar(100) = ""
  status varchar(20) = pending [pending, completed, failed, cancelled]
  created_by FK -> auth.User? SET_NULL
  created_at
  CHECK(amount >= 0)
```

## 8. Target business rules

`docs/business-rules.md` is canonical. The essential target invariants are:

- use `Decimal`/`DecimalField`, never float, for money;
- reject negative salary, adjustment, tax, payment, and net values;
- only one active contract per employee;
- one attendance row per employee/local work date;
- attendance stores facts/hours, never money;
- employees may access only their own private records/payslips;
- leave approval/rejection and payroll transitions use explicit services and record actor/time;
- pending/approved leave requests for one employee may not overlap;
- `PayrollItem` is a complete immutable historical snapshot;
- approved payroll cannot be recalculated or normally edited;
- one completed payment equals the PayrollItem net salary;
- payroll becomes Paid only after all items are paid;
- authorization is enforced server-side and at object level, not just in navigation.

Target payroll flow:

```text
Draft -> Calculated -> Reviewed -> Approved -> Paid
```

Target formula shape after decisions are confirmed:

```text
Gross = Basic Salary + Allowances + Overtime Pay + Bonuses

Total Deductions =
  Absence Deduction
  + Unpaid Leave Deduction
  + Manual Deductions
  + Tax

Net Salary = Gross - Total Deductions
```

## 9. Pending decisions — hard stop

Do not implement or silently confirm these decisions. The business owner must record approver/date and change status in `docs/business-rules.md`.

| ID | Decision | Recommended value | Status |
|---|---|---|---|
| Q-001 | Synthetic/demo product scope only | Approve | Pending |
| Q-002 | Single currency | USD | Pending |
| Q-003 | Salary/30 daily rate, hourly rate, overtime x1.5 | Approve | Pending |
| Q-004 | Monday-Friday leave days, no holiday calendar | Approve | Pending |

Repository security policy still prohibits real data during development while Q-001 is pending. Q-002 through Q-004 block payroll calculation work.

The business-rule phrase `active/approved` for bonuses/deductions does not define an approval workflow. Current models use `active`/`cancelled`; obtain an owner decision before adding another status/transition.

## 10. Known implementation gaps

These gaps are not permission to expand a task. Address only through an approved brief.

| Target | Current state |
|---|---|
| Leave overlap prevention | Not implemented in model validation or PostgreSQL exclusion constraint |
| One exact full payment | Payment is many-to-one and exact-net/approved-parent checks are absent |
| Complete immutable snapshot | PayrollItem lacks currency, version, contract/rate identity and immutability enforcement |
| All money nonnegative | Only selected fields have checks |
| Month-derived payroll dates | Stored directly; calendar consistency checks absent |
| Roles/own-record permissions | Group names exist; permission assignment/object checks absent |
| Confirmed currency | USD is only a field default; Q-002 is Pending |
| Render-only payslip concept | A Payslip file-metadata model exists |

## 11. Design system — Deep Equity

Goal: a compact, precise, calm administrative UI. Avoid consumer-style decoration.

### Visual rules

- flat tonal layers and subtle one-pixel borders;
- no gradients, glass effects, or routine shadows;
- 4px spacing rhythm and 4px default radius;
- semantic colors only for status/error feedback;
- shared utilities before one-off styling;
- keyboard-visible focus and server-rendered validation errors.

### Core color tokens

```text
background/surface          #F8F9FF
surface-container-lowest    #FFFFFF
surface-container-low       #EFF4FF
surface-container           #E6EEFF
surface-container-high      #DCE9FF
surface-container-highest   #D5E3FC
on-surface/on-background    #0D1C2E
on-surface-variant          #41484B
outline                     #71787C
outline-variant             #C1C7CB

primary                     #00222C
on-primary                  #FFFFFF
primary-container           #0C3846
on-primary-container        #7BA1B2
secondary                   #18677A
secondary-container         #A3E7FE
on-secondary-container      #1C697D
tertiary                    #00222B
tertiary-container          #003945

error                       #BA1A1A
on-error                    #FFFFFF
error-container             #FFDAD6
on-error-container          #93000A
```

Use Tailwind token utilities (`bg-primary`, `text-on-surface`, `border-outline-variant`), not raw hex values in templates.

### Typography utilities

```text
text-display       Hanken Grotesk 32/40, 700
text-headline-lg   Hanken Grotesk 24/32, 600
text-headline-md   Hanken Grotesk 20/28, 600
text-body-lg       Hanken Grotesk 16/24, 400
text-body-md       Hanken Grotesk 14/20, 400
text-body-sm       Hanken Grotesk 13/18, 400
text-label-caps    Hanken Grotesk 12/16, 700, uppercase, tracking
text-data-mono     JetBrains Mono 13/18, 400
```

Use `text-data-mono` for currency, numeric payroll data, and identifiers.

### Layout

- authenticated pages extend `templates/base.html`;
- auth pages extend `templates/auth_base.html`;
- desktop sidebar is 240px and primary-colored;
- header is 64px;
- page padding is 16px, increasing to 24px at `md`;
- cards/controls use 4px radius;
- current sidebar hides below `md`; mobile replacement navigation is not implemented.

### Shipped utilities/components

```text
btn-primary
btn-secondary
btn-ghost
card
input
badge
templates/components/field.html
```

`card`: white, outline-variant border, 24px padding, no shadow.
`input`: white, outline-variant border, secondary 2px focus border, no glow.
`badge`: structural utility paired with semantic background/text tokens.

### CSS workflow

Tailwind 4 is CSS-first; tokens/utilities live in `static/css/src/input.css`.

Repository-wide auto-detection is disabled so class-like words in documentation cannot alter production CSS. The source file explicitly scans the root `templates` directory and safelists shared utilities. Register any new app-local template directory with `@source` when it is introduced.

```powershell
npm run build:css
```

Always commit the rebuilt `static/css/dist/output.css` with source/template-class changes and visually review the affected page.

## 12. Security and data rules

- Synthetic values only; never use real employee/payroll/bank/tax/payment data.
- Never share or commit `.env`, `DATABASE_URL`, Supabase keys/URLs, passwords, tokens, cookies, private keys, dumps, logs, or production screenshots.
- `Employee.bank_account_number` is plaintext demo-only and blocks real deployment.
- Use POST plus CSRF for state changes.
- Enforce permissions in views/services and at object level.
- Do not log complete payroll objects or sensitive fields.
- Real deployment requires a separate review for jurisdiction, encryption, audit, retention, backups, monitoring, HTTPS, secure cookies, and `DEBUG=False`.

## 13. Local setup

PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Set the Supabase session-pooler DATABASE_URL in .env; do not share/commit it.
npm ci
npm run build:css
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

macOS/Linux activation/copy equivalents:

```bash
source .venv/bin/activate
cp .env.example .env
```

The configured Supabase database is remote. `migrate` and `createsuperuser` modify that configured database.

## 14. Validation

```powershell
npm run build:css
python manage.py makemigrations --check --dry-run
python manage.py check
pytest
ruff check .
```

Do not run tests against shared/production data. Django normally creates a temporary test database; use a dedicated test database/role if the Supabase role cannot create one.

Every task also needs a manual workflow check and full diff review.

## 15. Task workflow for humans and AI agents

Before code:

1. Read this file and the current implementation/migrations.
2. Complete `docs/task-brief-template.md`.
3. State the owning person/app, dependency task IDs, migration prerequisites, shared files, and public interfaces.
4. Identify applicable business rules and Pending IDs.
5. Restate exact acceptance criteria and allowed/denied permission cases.
6. Stop if a pending decision materially affects the task.

During code:

- edit only owned/allowed files;
- keep views thin and business logic in services;
- preserve dependency direction and public contracts;
- use `Decimal`, transactions where appropriate, and explicit transitions;
- add server-side validation, permissions, tests, and database constraints;
- generate migrations for model changes; never hand-edit an already-applied migration;
- coordinate shared-file edits through the integration owner;
- avoid unrelated refactors.

Before completion:

- run proportionate tests/checks;
- manually exercise success and denied paths;
- inspect the complete diff and migration SQL/operations;
- verify no secrets or real data;
- rebuild/visually check CSS when UI changes;
- report exact commands/results, changed files, migrations, assumptions, and risks;
- request another person's review.

## 16. Required first response from an AI agent

Before editing, return:

1. bounded task outcome;
2. owning person/app and dependency direction;
3. files/interfaces received and files proposed for change;
4. relevant target rules and current-schema facts;
5. pending decisions/blockers;
6. exact acceptance and permission cases;
7. minimal implementation, test, migration, and manual-review plan.

Do not fabricate files, policies, test results, or completed actions. Report contradictions and ask for approval when a rule/policy decision is required.

## 17. Explicitly out of scope

Recruitment, performance management, multiple companies/countries/currencies, progressive/legal tax compliance, proration, complex shifts/leave, holiday calendars, half days, corrections/reversals, partial payments, bank/accounting integrations, notifications, a large frontend framework, and a general audit subsystem.

Keep the seven-day MVP narrow and make the required end-to-end flow reliable first.
