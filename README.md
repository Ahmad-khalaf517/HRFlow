# HRFlow

HRFlow is a focused HR and payroll Django MVP with a **seven-calendar-day delivery constraint**.

The required demonstration flow is:

```text
Employee -> Contract -> Attendance/Leave -> Payroll -> Payslip -> Payment
```

## Running the Project Locally

Requires Python 3.12+, Node.js (for the Tailwind build), and a PostgreSQL connection string — this project targets [Supabase](https://supabase.com) and does not run a local database service.

The Django ORM migrations under `accounts/`, `employees/`, `attendance/`, and `payroll/` are the source of truth for the domain tables.

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env            # set DATABASE_URL to your Supabase connection string; never commit .env

python manage.py migrate        # creates auth/admin/sessions tables and all domain tables
```

```bash
npm install
npm run build:css               # one-off build; use `npm run watch:css` while developing

python manage.py createsuperuser
python manage.py runserver
```

Then visit `http://localhost:8000`. Run `pytest` for the test suite and `ruff check .` for linting.

## Start Here

| Document | Purpose |
|---|---|
| `docs/delivery-plan.md` | Seven-day scope, work packages, sequence, cut line, and definition of done |
| `docs/business-rules.md` | Canonical calculations, permissions, workflow rules, and pending decisions |
| `docs/erd.md` | Minimum entities, relationships, and database constraints |
| `database/legacy_neon_schema.sql` | Stale, pre-ORM draft schema; kept for historical reference only |
| `docs/security-and-data-policy.md` | Application security and safe use of consumer web AI |
| `AI_CONTEXT.md` | Short repository context and non-negotiable rules for coding agents |
| `docs/team-ai-context-prompt.md` | Standalone prompt for teammates using web ChatGPT or Claude |
| `docs/task-brief-template.md` | Bounded task specification for one implementation change |

`AGENTS.md` and `CLAUDE.md` are intentionally tiny adapters that direct compatible coding agents to `AI_CONTEXT.md`.

## Locked Technology

- Python 3.12+ and Django 5.x
- PostgreSQL
- Django Templates and Tailwind CSS
- Alpine.js only for small interactions
- HTMX only when a specific interaction clearly benefits
- Ruff

Do not add a large frontend framework. Use Django Admin for low-value support-data management when a custom screen is not required for the demo.

## Team AI Workflow

For each task:

1. Complete `docs/task-brief-template.md`.
2. Give the AI `AI_CONTEXT.md`, the task brief, and only the relevant sanitized files.
3. Ask the AI to restate constraints and identify missing decisions before producing code.
4. Review the full diff and manually exercise the affected workflow.
5. Use a separate review pass before merge.

Never send real employee, salary, bank, tax, payment, credential, log, database, or production data to consumer web AI tools.

## Immediate Decision Gate

The decision table at the top of `docs/business-rules.md` must be resolved before payroll calculation work begins. Until then, AI assistants and developers must not invent currency, rate, overtime, or leave-calendar policy.
