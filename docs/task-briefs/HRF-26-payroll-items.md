# HRFlow Task Brief

## Task

- Ticket / title: HRF-26 — Payroll Items
- Owner: Ahmad Khalaf (Person 3 — payroll)
- Context commit: c035acc
- Owning app: payroll
- Depends on tasks/migrations: HRF-25 (the calculation service writes the snapshot; this ticket is mostly the *display* of it plus the storage guarantees already built into `calculate_payroll`).
- Required outcome: `PayrollItem` stores a snapshot of each employee's calculated salary so historical payroll remains unchanged, and that snapshot is visible on the payroll run detail page.

## Scope

- In scope: itemized table on `/payroll/runs/<id>/` (`payroll/templates/payroll/run_detail.html`), the `update_or_create` snapshot-write logic inside `calculate_payroll`.
- Out of scope: payslip rendering (`Payslip` model, out of scope for this ticket batch), payment (`Payment` model, out of scope for this ticket batch).
- Files allowed to change: `payroll/*`.
- Public interfaces added: none beyond `calculate_payroll` (HRF-25).
- Shared files requiring coordination: none new.

## Binding Context

- Relevant confirmed rules: business-rules.md §7 — "One PayrollItem exists per payroll and included employee." / "PayrollItem stores every contract input, fact, monetary component ... required to reproduce the result." / "Payslips render from the saved item. They never recalculate from current contract data."
- Relevant models/services/interfaces: `payroll.models.PayrollItem` (existing `payrollitem_unique_payroll_employee` constraint enforces one row per employee per run); `payroll.services.calculate_payroll`'s `update_or_create`.
- Permission or object-access rule: `require_payroll_manager` gate on the detail view.
- Pending decision IDs: None.
- Data classification: Synthetic only.

## Acceptance Criteria

- [x] One payroll item exists per included employee.
- [x] Only active employees with an active contract are included (`Employee.objects.filter(is_active=True, employment_status="active")` + `contracts.filter(status="active").first()`).
- [x] Calculated salary components are stored (every `PayrollItem` field the formula produces).
- [x] Gross salary, deductions, and net salary are stored.
- [x] Historical payroll items do not recalculate from the employee's current contract (a `PayrollItem` is only ever touched again by a manual Recalculate action while the run is still `draft`/`calculated` — nothing reads live `Contract` data outside `calculate_payroll`).
- [x] Duplicate employee payroll items within one payroll run are prevented (`payrollitem_unique_payroll_employee` DB constraint + `update_or_create`).

## Required Review

- Manual workflow review: same Calculate run as HRF-25 — confirmed exactly one row per active employee with an active contract in the items table, values matching the hand-verified formula.
- Migration or framework command: `python manage.py check`, `makemigrations --check --dry-run` — no new migrations needed, `PayrollItem` schema was already complete.
- Expected observable result: items table on the run detail page, one row per eligible employee.

## Follow-up after teammate merges

- **Immutability gap (pre-existing, out of scope for this batch)**: business-rules.md §7 wants an immutable snapshot once approved; `docs/business-rules.md`/TEAM_CONTEXT.md §10 already flag that `PayrollItem` has no DB-level immutability enforcement or currency/version identity fields. `calculate_payroll` is application-level-gated (blocked once `approved`/`paid`) but there's no DB constraint stopping a direct ORM/admin edit post-approval. Flag for a future ticket if that hardening is wanted — not part of HRF-21..28.
- Same employees/attendance mock-data follow-up as HRF-25.
