# HRFlow Task Brief

## Task

- Ticket / title: HRF-22 — Manual Deduction Management
- Owner: Ahmad Khalaf (Person 3 — payroll)
- Context commit: c035acc
- Owning app: payroll
- Depends on tasks/migrations: none (uses existing `payroll.ManualDeduction` model/migration)
- Required outcome: HR/Payroll staff can record and cancel manual employee deductions (loan, insurance, advance repayment, disciplinary, other) so they can be included in payroll calculation.

## Scope

- In scope: list deductions, create a deduction, cancel a deduction (status flip, no delete).
- Out of scope: absence/unpaid-leave deductions — those are derived during payroll calculation (HRF-25) from mock/real attendance facts, never stored as `ManualDeduction` rows (model docstring enforces this by convention, not by a DB constraint).
- Files allowed to change: `payroll/*`.
- Public interfaces added: reuses `payroll.services.get_active_adjustments_for_period` from HRF-21.
- Shared files requiring coordination: same as HRF-21 (`templates/base.html`, `config/urls.py`, `static/css/src/input.css`) — already applied, no further changes needed for this ticket.

## Binding Context

- Relevant confirmed rules: business-rules.md §3 (Decimal money, reject negative — `manualdeduction_amount_gte_0` DB constraint).
- Relevant models/services/interfaces: `payroll.models.ManualDeduction`; `payroll/forms.py:ManualDeductionForm`; `payroll/views.py:deduction_list/deduction_create/deduction_cancel`.
- Permission or object-access rule: business-rules.md §9 — `require_payroll_manager` gate (Admin/Payroll Officer only).
- Pending decision IDs: None.
- Data classification: Synthetic only.

## Acceptance Criteria

- [x] Manual deductions can be recorded for employees.
- [x] Amount and effective date are required.
- [x] Deduction status is stored.
- [x] Payroll can retrieve applicable deductions for a payroll month.
- [x] Negative deduction amounts are rejected.
- [x] Absence and unpaid-leave deductions are not stored as manual deductions (never written by any payroll code path — they're computed fields on `PayrollItem` instead).

## Required Review

- Manual workflow review: verified list/create/cancel at `/payroll/deductions/` the same way as HRF-21's bonus flow.
- Migration or framework command: `python manage.py check`, `makemigrations --check --dry-run`, `ruff check payroll/` — all clean.
- Expected observable result: deduction list shows the new row, Active badge, working Cancel action.

## Follow-up after teammate merges

- Same employee-picker note as HRF-21: swap seeded demo employees for real ones once Person 1 ships employee CRUD — zero payroll code changes required.
