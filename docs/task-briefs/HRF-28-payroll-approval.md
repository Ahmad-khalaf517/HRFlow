# HRFlow Task Brief

## Task

- Ticket / title: HRF-28 — Payroll Approval
- Owner: Ahmad Khalaf (Person 3 — payroll)
- Context commit: c035acc
- Owning app: payroll
- Depends on tasks/migrations: HRF-27 (a payroll run must be `reviewed` first).
- Required outcome: reviewed payroll can be approved by an authorized user so it can proceed to payslips and payment (both out of scope for this ticket batch).

## Scope

- In scope: `payroll.services.approve_payroll`, the "Approve" action on the run detail page, `reviewed` → `approved` transition, the authorization check.
- Out of scope: payslip/payment generation (separate `Payslip`/`Payment` models, not part of HRF-21..28).
- Files allowed to change: `payroll/*`.
- Public interfaces added: `payroll.services.approve_payroll(payroll, actor)`; `payroll.services.user_in_groups(user, group_names)` (also used by `require_payroll_manager`).
- Shared files requiring coordination: none new.

## Binding Context

- Relevant confirmed rules: business-rules.md §7 — "Approved payroll cannot be recalculated or edited through normal flows."; §9 permission table (payroll runs are Manage-only for Admin/Payroll Officer).
- Relevant models/services/interfaces: `payroll.models.Payroll.{status,approved_by,approved_at}`; `payroll/views.py:run_approve`.
- Permission or object-access rule: enforced **twice** — the view-level `require_payroll_manager` decorator (business-rules.md §9: "Authorization is enforced server-side and at object level. Navigation visibility is not authorization.") and again inside `approve_payroll` itself via `user_in_groups(actor, ["Admin", "Payroll Officer"])`, so the rule holds even if `approve_payroll` is ever called from another code path.
- Pending decision IDs: None.
- Data classification: Synthetic only.

## Acceptance Criteria

- [x] Only authorized users can approve payroll (group check, service-level + view-level).
- [x] Approval records the responsible user (`approved_by`).
- [x] Approval timestamp is recorded (`approved_at`).
- [x] Approved payroll cannot be recalculated through the normal UI (`calculate_payroll` guard rejects `status == "approved"`; the "Calculate"/"Recalculate" button is also hidden once approved).
- [x] Payroll follows the defined status workflow (`draft → calculated → reviewed → approved`; re-approving or approving out of order raises `ValidationError`).

## Required Review

- Manual workflow review, two passes:
  1. As `payroll_demo` (Payroll Officer): approved Payroll 09/2026 from Reviewed; confirmed Approved badge, `approved_by`/`approved_at` recorded, "Locked — approved payroll cannot be recalculated." message, no action buttons left. Confirmed a second `calculate_payroll`/`approve_payroll` call on the same run is rejected with a `ValidationError`.
  2. As `regular_employee_demo` (Employee group only, no Payroll Officer/Admin): `GET /payroll/runs/` returned **403 Forbidden** — confirmed the group gate blocks the entire module, not just Approve.
- Migration or framework command: `python manage.py check`, `ruff check payroll/`.
- Expected observable result: Approved badge, locked message, no further status-changing actions.

## Follow-up after teammate merges

- None specific — this ticket's authorization check depends only on Django's `auth_group` membership (seeded by `accounts`' existing migration), not on employees/attendance data.
