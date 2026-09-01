# HRFlow Task Brief

## Task

- Ticket / title: HRF-21 — Bonus Management
- Owner: Ahmad Khalaf (Person 3 — payroll)
- Context commit: c035acc
- Owning app: payroll
- Depends on tasks/migrations: none (uses existing `payroll.Bonus` model/migration)
- Required outcome: HR/Payroll staff can record and cancel employee bonuses so approved bonuses can be included in payroll calculation.

## Scope

- In scope: list bonuses, create a bonus, cancel a bonus (status flip, no delete).
- Out of scope: an approval workflow for bonuses (business-rules.md §9/TEAM_CONTEXT.md explicitly say `active`/`cancelled` is not an approval workflow — none was added).
- Files allowed to change: `payroll/*`.
- Public interfaces added: `payroll.services.get_active_adjustments_for_period(model, employee, period_start, period_end)` (shared with HRF-22, consumed by HRF-25's calculation).
- Shared files requiring coordination: `templates/base.html` (sidebar Payroll link now points at `payroll:run-list`), `config/urls.py` (`payroll.urls` included), `static/css/src/input.css` (`@source` added for `payroll/templates`).

## Binding Context

- Relevant confirmed rules: business-rules.md §3 (money as Decimal, reject negative — enforced by the existing `bonus_amount_gte_0` DB constraint plus `DecimalField`).
- Relevant models/services/interfaces: `payroll.models.Bonus`; `payroll/forms.py:BonusForm`; `payroll/views.py:bonus_list/bonus_create/bonus_cancel`.
- Permission or object-access rule: business-rules.md §9 — payroll inputs are Manage-only for `Admin`/`Payroll Officer`; enforced by `payroll/views.py:require_payroll_manager`.
- Pending decision IDs: None.
- Data classification: Synthetic only — exercised against `payroll/management/commands/seed_payroll_demo_data.py` output.

## Acceptance Criteria

- [x] Bonuses can be recorded for employees.
- [x] Bonus amount and effective date are required.
- [x] Bonus status is stored (`active`/`cancelled`).
- [x] Payroll can retrieve applicable bonuses for a payroll month (`get_active_adjustments_for_period`, consumed in `calculate_payroll`).
- [x] Negative bonus amounts are rejected (form + model `CheckConstraint`).

## Required Review

- Manual workflow review: logged in as `payroll_demo` (Payroll Officer), recorded a bonus for EMP-1001 via `/payroll/bonuses/new/`, confirmed it appears Active in `/payroll/bonuses/`, confirmed it fed into that employee's `bonus_amount` on the next Calculate (HRF-25).
- Migration or framework command: `python manage.py makemigrations --check --dry-run` (no changes), `python manage.py check`, `ruff check payroll/` — all clean.
- Expected observable result: bonus list shows the new row with an Active badge and a working Cancel action.

## Follow-up after teammate merges

- Employee picker currently lists every `employees.Employee` row (real once Person 1 ships employee CRUD, seeded synthetic data until then via `seed_payroll_demo_data`) — no payroll code change needed when real employees replace the seed rows.
