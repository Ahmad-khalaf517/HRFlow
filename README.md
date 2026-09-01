# HRFlow

HRFlow is a seven-calendar-day Django HR and payroll MVP. Repository development is restricted to synthetic data while formal product-scope decision Q-001 remains pending. The required demonstration flow is:

```text
Employee -> Contract -> Attendance/Leave -> Payroll -> Payslip -> Payment
```

This repository is an MVP foundation, not a production payroll or legal-compliance system.

## Current baseline

Implemented:

- Django authentication, login/logout, session handling, and four seeded role groups;
- Supabase-hosted PostgreSQL through Django's ORM;
- all current domain models and initial migrations;
- Django Admin registrations for domain models;
- the authenticated dashboard shell;
- the shared Tailwind CSS design system and compiled stylesheet;
- initial authentication and database-constraint tests.

Not implemented yet:

- custom employee and contract screens;
- attendance calculation and leave workflow services;
- payroll calculation and guarded status-transition services;
- object-level role enforcement across domain views;
- employee payslip and payment workflows;
- complete synthetic fixtures and an end-to-end demo.

Payroll calculation work is blocked by pending decisions Q-002 through Q-004 in `docs/business-rules.md`.

## Technology

- Python 3.12+ and Django 5.x
- PostgreSQL hosted by Supabase
- `psycopg`, `dj-database-url`, and `python-dotenv`
- Django Templates, `django-widget-tweaks`, and `django-filter`
- Node.js 20+ and Tailwind CSS 4 CLI
- Pytest, pytest-django, and Ruff
- Alpine.js or HTMX only when a small interaction clearly needs it; neither is currently installed

Supabase is used as the PostgreSQL host, not as the authentication provider. Django users live in `public.auth_user`; they do not appear in Supabase Auth's `auth.users` screen.

## Local setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

On macOS or Linux, activate it with `source .venv/bin/activate` and copy the environment file with `cp .env.example .env`.

Set `DATABASE_URL` in `.env` to the Supabase session-pooler connection string, including `sslmode=require`. Never commit `.env`.

Apply the schema and build the CSS:

```powershell
python manage.py migrate
npm ci
npm run build:css
```

Create a synthetic/demo administrator in the configured Supabase database and run the application:

```powershell
python manage.py createsuperuser
python manage.py runserver
```

Open `http://localhost:8000/`. The generated `static/css/dist/output.css` is intentionally tracked so a fresh checkout retains the design; rebuild and commit it whenever `static/css/src/input.css` or template classes change.

## Validation

```powershell
npm run build:css
python manage.py makemigrations --check --dry-run
python manage.py check
pytest
ruff check .
```

The configured Supabase role may not be allowed to create Django's temporary test database. If `pytest` fails during test-database creation, use a dedicated PostgreSQL test database/role rather than running destructive tests against shared data.

## Architecture

HRFlow is one Django monolith with four primary apps and a one-way dependency direction:

```text
accounts -> employees -> attendance -> payroll
```

| Area | Responsibility |
|---|---|
| `accounts` | Django authentication UI, roles, and permission entry points |
| `employees` | Departments, positions, employees, and contracts |
| `attendance` | Attendance facts, leave requests, and future monthly fact services |
| `payroll` | Adjustments, tax configuration, payroll snapshots, payslips, and payments |
| `config` | Settings, root URLs, and the cross-domain dashboard |
| `templates` | Shared Django page shells and reusable template components |
| `static/css/src` | Tailwind source tokens and component utilities |

Keep views thin. Put calculations and workflow transitions in explicit services. Payroll may consume attendance only through public attendance service functions.

## Documentation map

For a teammate handoff, share `TEAM_CONTEXT.md`; it is self-contained. Repository contributors can then use these focused references:

1. `TEAM_CONTEXT.md` — single context for teammates, browser AI, and repository-integrated agents.
2. `docs/business-rules.md` — authoritative target behavior and unresolved decisions.
3. `docs/erd.md` — exact schema produced by the current migrations and known gaps against the rules.
4. `docs/design-system.md` — UI tokens, component utilities, and layout rules.
5. `docs/delivery-plan.md` — current implementation status, three-person sequence, ownership, and cut line.
6. `docs/security-and-data-policy.md` — synthetic-data and credential-handling requirements.
7. `docs/task-brief-template.md` — required scope/acceptance template for one change.

The Django migrations are the only executable schema source of truth. Do not maintain or run a parallel SQL schema.

## Team workflow

For each reviewable task:

1. create a branch and complete `docs/task-brief-template.md`;
2. identify relevant business rules and pending decision IDs;
3. make the smallest change that satisfies the acceptance criteria;
4. add migrations, constraints, permissions, and tests when applicable;
5. run the validation commands and manually exercise the affected workflow;
6. inspect the full diff for secrets, real HR data, and unrelated changes;
7. request review before merging.

Use synthetic data only. Never commit credentials or expose real employee, payroll, tax, payment, or bank information.
