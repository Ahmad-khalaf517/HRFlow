# HRFlow Task Brief

## Task

- Ticket / title: HRF-24 — Payroll Run
- Owner: Ahmad Khalaf (Person 3 — payroll)
- Context commit: c035acc
- Owning app: payroll
- Depends on tasks/migrations: none (uses existing `payroll.Payroll` model/migration, in particular the `payroll_unique_month_year` constraint)
- Required outcome: Payroll Officer can create a monthly payroll run, which starts in Draft, so employee salaries can later be processed for that period.

## Scope

- In scope: list payroll runs, create a run for a month/year.
- Out of scope: recalculation/review/approval UI (HRF-25/27/28), employee inclusion logic (HRF-25/26).
- Files allowed to change: `payroll/*`.
- Public interfaces added: `payroll.services.create_payroll_run(month, year, created_by)`.
- Shared files requiring coordination: `config/urls.py` (`path("payroll/", include("payroll.urls"))`), `templates/base.html` sidebar link, `static/css/src/input.css` `@source` addition — all already applied.

## Binding Context

- Relevant confirmed rules: business-rules.md §6 "Payroll period identity is unique by month and year; start/end dates are derived from that month."; §7 "Payroll status is Draft -> Calculated -> Reviewed -> Approved -> Paid."
- Relevant models/services/interfaces: `payroll.models.Payroll`; `payroll/forms.py:PayrollRunForm`; `payroll/views.py:run_list/run_create/run_detail`.
- Permission or object-access rule: `require_payroll_manager` gate.
- Pending decision IDs: None.
- Data classification: Synthetic only.

## Acceptance Criteria

- [x] Payroll is monthly.
- [x] Month and year identify the payroll period.
- [x] Only one payroll run can exist for a month and year (DB constraint `payroll_unique_month_year`; form pre-checks for a friendly error, service also catches `IntegrityError` as a race-condition backstop).
- [x] Period start and end are derived from the selected month and year (`calendar.monthrange`).
- [x] New payroll runs start in Draft status (model default).

## Required Review

- Manual workflow review: created Payroll 09/2026 via `/payroll/runs/new/`, confirmed Draft badge and derived period (Sept 1 – Sept 30, 2026) on the detail page; confirmed a second attempt at the same month/year is rejected with a friendly form error.
- Migration or framework command: `python manage.py check`, `makemigrations --check --dry-run`, `ruff check payroll/`.
- Expected observable result: `/payroll/runs/` lists the new run with status/totals columns; dashboard's "This month's payroll" stat (`config/views.py`) picks it up automatically since it already queries `Payroll`.

## Follow-up after teammate merges

- None specific to employees/attendance — this ticket only creates the `Payroll` shell, no employee data is read yet.
