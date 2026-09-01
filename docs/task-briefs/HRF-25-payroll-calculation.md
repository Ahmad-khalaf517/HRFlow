# HRFlow Task Brief

## Task

- Ticket / title: HRF-25 — Payroll Calculation
- Owner: Ahmad Khalaf (Person 3 — payroll)
- Context commit: c035acc
- Owning app: payroll
- Depends on tasks/migrations: HRF-21/22/23/24 (bonuses, deductions, tax brackets, payroll run must exist); attendance facts are **mocked** — see Follow-up.
- Required outcome: payroll calculated from approved inputs so each employee receives an accurate demonstrative net salary.

## Decision record (blocker resolved)

`docs/business-rules.md` §1 stated: *"Payroll calculation work is blocked until Q-002 through Q-004 are approved. Do not let a developer or AI assistant invent an answer."* Before this ticket was implemented, you (Ahmad Khalaf) were asked explicitly and chose to approve the documented recommended defaults. `docs/business-rules.md` was updated accordingly:

- Q-002 (currency): USD — Confirmed.
- Q-003 (rate formula): Daily rate = salary/30; hourly = daily/contract hours; overtime = hourly × 1.5 — Confirmed.
- Q-004 (leave counting): Monday–Friday only, no holiday calendar — Confirmed.
- Approved by Ahmad Khalaf on 2026-09-01 (recorded in `docs/business-rules.md` §1). Q-001 (synthetic/demo scope) remains separately Pending — not needed to unblock this ticket.

## Scope

- In scope: `payroll.services.calculate_payroll` — the full formula, PayrollItem snapshot writes (this doubles as HRF-26), payroll totals, `draft`/`calculated` → `calculated` transition.
- Out of scope: attendance's real overtime/absence/unpaid-leave calculation (Person 2's app) — mocked for now, see Follow-up.
- Files allowed to change: `payroll/*`.
- Public interfaces added: `payroll.services.calculate_payroll(payroll, actor)`; `payroll.attendance_facts.{get_employee_overtime_hours,get_absence_days,get_unpaid_leave_days}` (mock stand-ins for the attendance app's documented public contract).
- Shared files requiring coordination: none new.

## Binding Context

- Relevant confirmed rules: business-rules.md §6 formula (see below); §3 (Decimal, 2dp, `ROUND_HALF_UP`, reject negative); §4 ("Payroll includes only active employees with an active contract").
- Formula implemented exactly as documented:
  ```
  daily_rate = basic_salary / 30
  hourly_rate = daily_rate / contract.working_hours_per_day
  overtime_amount = overtime_hours * hourly_rate * 1.5
  absence_deduction = absence_days * daily_rate
  unpaid_leave_deduction = unpaid_leave_days * daily_rate
  gross_salary = basic_salary + allowances + overtime_amount + bonus_amount
  tax_amount = matching_bracket.fixed_amount + gross_salary * matching_bracket.percentage / 100
  total_deductions = absence_deduction + unpaid_leave_deduction + manual_deduction_amount + tax_amount
  net_salary = gross_salary - total_deductions
  ```
- Relevant models/services/interfaces: `payroll.models.{Payroll,PayrollItem}`, `employees.models.{Employee,Contract}` (read-only), `payroll.attendance_facts` (mock), `payroll.services.{get_active_adjustments_for_period,get_matching_tax_bracket}`.
- Permission or object-access rule: `require_payroll_manager` gate on the `run-calculate` view; recalculation itself is blocked in the service once `status` is `approved`/`paid` (business-rules.md §7 "Approved payroll cannot be recalculated").
- Pending decision IDs: None (Q-002/003/004 confirmed above). Q-001 unrelated, still Pending.
- Data classification: Synthetic only.

## Acceptance Criteria

- [x] Basic salary and allowances are included.
- [x] Overtime pay is calculated.
- [x] Bonuses are included.
- [x] Absence deductions are calculated.
- [x] Unpaid leave deductions are calculated.
- [x] Manual deductions are included.
- [x] Tax is calculated.
- [x] Gross salary is calculated.
- [x] Total deductions are calculated.
- [x] Net salary is calculated.
- [x] Decimal values are used for monetary calculations.
- [x] Monetary values are rounded using ROUND_HALF_UP.
- [x] Negative monetary values are rejected (all inputs come from non-negative-constrained sources; no path produces a negative component).

## Required Review

- Manual workflow review: ran `calculate_payroll` both via `python manage.py shell` (see commands below) and via the browser (`/payroll/runs/2/calculate/` as `payroll_demo`, a Payroll Officer). Verified one employee's numbers by hand (EMP-1001: basic 3000, allowance 150, overtime 1h → 18.75, absence 1d → 100.00 deduction, gross 3168.75, Standard bracket 10% tax → 316.88, total deductions 416.88, net 2751.87) — matched the UI exactly. Confirmed `EMP-1005` (inactive employee/contract) is correctly excluded — only 4 of 5 seeded employees got a `PayrollItem`.
- Migration or framework command: `python manage.py check`, `makemigrations --check --dry-run`, `ruff check payroll/` — all clean. No new migrations needed; `PayrollItem` already had every field the formula writes.
- Expected observable result: `Payroll.status` becomes `calculated`, `total_gross`/`total_deductions`/`total_net` populated, one `PayrollItem` per active employee with an active contract.

## Follow-up after teammate merges

- **Attendance (Person 2)**: `payroll/attendance_facts.py` currently returns deterministic mock values (`employee.id % 6` overtime hours, `employee.id % 3` absence days, etc.) because `attendance/services.py` doesn't exist yet. Once Person 2 ships `get_employee_overtime_hours`/`get_absence_days`/`get_unpaid_leave_days` with the documented signatures, swap the import in `payroll/services.py` (`from .attendance_facts import ...` → `from attendance.services import ...`) — no other code should need to change. Re-run Calculate on any Draft/Calculated payroll runs created against the mock data; do not trust `PayrollItem` rows calculated before the swap for anything beyond demo purposes.
- **Employees (Person 1)**: employee/contract data is currently `seed_payroll_demo_data` output; swap for real employee CRUD data with no payroll code changes.
