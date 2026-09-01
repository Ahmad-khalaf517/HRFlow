# HRFlow Task Brief

## Task

- Ticket / title: HRF-27 — Payroll Review
- Owner: Ahmad Khalaf (Person 3 — payroll)
- Context commit: c035acc
- Owning app: payroll
- Depends on tasks/migrations: HRF-25/26 (a payroll run must be `calculated` first).
- Required outcome: calculated payroll can be reviewed — totals and employee-level breakdown checked — before approval.

## Scope

- In scope: `payroll.services.mark_reviewed`, the "Mark reviewed" action on the run detail page, `calculated` → `reviewed` transition.
- Out of scope: approval itself (HRF-28).
- Files allowed to change: `payroll/*`.
- Public interfaces added: `payroll.services.mark_reviewed(payroll, actor)`.
- Shared files requiring coordination: none new.

## Binding Context

- Relevant confirmed rules: business-rules.md §7 — "Status changes use explicit services and record the responsible user and timestamp."
- Relevant models/services/interfaces: `payroll.models.Payroll.{status,reviewed_by,reviewed_at}`; `payroll/views.py:run_review`.
- Permission or object-access rule: `require_payroll_manager` gate (same as the rest of the module — business-rules.md §9 doesn't carve out a narrower reviewer role).
- Pending decision IDs: None.
- Data classification: Synthetic only.

## Acceptance Criteria

- [x] Calculated payroll can be reviewed.
- [x] Employee-level payroll breakdown is visible (full per-employee column set on the run detail page: basic, overtime, bonus, gross, each deduction component, tax, total deductions, net).
- [x] Total gross salary is displayed.
- [x] Total deductions are displayed.
- [x] Total net salary is displayed.
- [x] Payroll can move from Calculated to Reviewed (`mark_reviewed`, guarded to only accept `status == "calculated"`).

## Required Review

- Manual workflow review: clicked "Mark reviewed" on Payroll 09/2026 after calculating it; confirmed status badge changed to Reviewed, `reviewed_by`/`reviewed_at` recorded, Calculate/Recalculate action disappeared (only Approve remained).
- Migration or framework command: `python manage.py check`, `ruff check payroll/`.
- Expected observable result: Reviewed badge, Approve button only.

## Follow-up after teammate merges

- None specific — this ticket doesn't touch employee/attendance data directly, only the `Payroll` state machine.
