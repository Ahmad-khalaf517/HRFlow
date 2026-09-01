# HRFlow — MVP Business Rules

This is the canonical source for target HR and payroll behavior. Planning documents may summarize these rules but must not redefine them. The presence of a model, field default, or migration is not proof that a rule is implemented or approved; `erd.md` records the exact current schema and known gaps.

## 1. Decision Status

Payroll calculation work is blocked until Q-002 through Q-004 are approved. Do not let a developer or AI assistant invent an answer.

| ID | Decision | Recommended default | Status |
|---|---|---|---|
| Q-001 | HRFlow uses synthetic/demo data and is not used for real payroll | Approve | Pending |
| Q-002 | Single currency shown in payroll and payslips | USD | Confirmed |
| Q-003 | Daily rate = salary / 30; hourly rate = daily rate / contract hours; overtime = hourly rate × 1.5 | Approve | Confirmed |
| Q-004 | Leave counts Monday-Friday only; weekends excluded; no holiday calendar | Approve | Confirmed |

Q-002 through Q-004 approved by Ahmad Khalaf on 2026-09-01 using the recommended defaults above, unblocking payroll calculation work (HRF-25). Q-001 remains Pending — resolve separately.

The business owner may resolve all four by approving the recommended defaults. Record the approver and date in this section and change each accepted status to `Confirmed`.

Repository security policy requires synthetic data during development even while the formal product-scope decision Q-001 remains pending. Never use real HR/payroll data to test the pending decision.

## 2. MVP Boundary

- One company, one currency, and monthly payroll only.
- Synthetic employee and payroll data only.
- Whole-day attendance and leave rules.
- One active contract per employee.
- One simple demonstrative tax method.
- One full payment per payroll item.
- No legal-compliance claim.

## 3. Money

- Use Python `Decimal` and Django `DecimalField`; never use `float`.
- Store money with two decimal places and round final components with `ROUND_HALF_UP`.
- Negative salary, bonus, deduction, tax, payment, or net-pay values are invalid.
- Currency conversion is out of scope.

## 4. Employees and Contracts

- `employee_number` is unique; salary and fixed allowances belong to `Contract`.
- An employee may have contract history but only one active contract.
- Contract `end_date` cannot precede `start_date`.
- Payroll includes only active employees with an active contract.
- Referenced historical contracts are deactivated, not deleted.
- Proration, mid-month hires/terminations, and mid-period contract changes are out of scope; demo data avoids them.

## 5. Attendance and Leave

- Only one attendance record exists per employee and local work date.
- Attendance stores check-in, check-out, status, worked hours, and overtime hours—never money.
- Check-out must be after check-in.
- `worked_hours = check_out - check_in`.
- `overtime_hours = max(worked_hours - contract working_hours_per_day, 0)`.
- Leave requests use `pending`, `approved`, `rejected`, or `cancelled`.
- Employees submit leave; HR approves or rejects it; an employee cannot approve their own request.
- Leave end date cannot precede start date, and pending/approved requests may not overlap.
- The system derives `requested_days`; users cannot edit it directly.
- Only approved unpaid leave inside the payroll month affects payroll.
- Overnight shifts, breaks, grace periods, lateness deductions, half days, balances, holidays, and complex cancellations are out of scope.

## 6. Payroll Inputs and Calculation

- Payroll period identity is unique by `month` and `year`; start/end dates are derived from that month.
- Bonuses and manual deductions are included when active/approved and dated inside the payroll month.
- Attendance services provide overtime, absence, and approved unpaid-leave totals. Payroll converts these facts into money.
- One seeded/configured `TaxBracket` selects a matching demonstrative rule; this is not a progressive or legally compliant tax engine.

The phrase `active/approved` above does not authorize inventing a new approval workflow. The current migrated models use `active`/`cancelled`; a task that adds an `approved` state or approval transition must first obtain an explicit owner decision.

```text
Gross = Basic Salary + Allowances + Overtime Pay + Bonuses

Total Deductions =
Absence Deduction
+ Unpaid Leave Deduction
+ Manual Deductions
+ Tax

Net Salary = Gross - Total Deductions
```

Pending Q-003 confirmation:

```text
Daily Rate = Basic Salary / 30
Hourly Rate = Daily Rate / Contract Working Hours Per Day
Overtime Pay = Overtime Hours * Hourly Rate * 1.5
Absence Deduction = Absence Days * Daily Rate
Unpaid Leave Deduction = Unpaid Leave Days * Daily Rate
Tax = Fixed Amount + (Gross * Percentage / 100)
```

## 7. Snapshot and Workflow

- One `PayrollItem` exists per payroll and included employee.
- `PayrollItem` stores every contract input, fact, monetary component, currency, and calculation version required to reproduce the result.
- Payslips render from the saved item. They never recalculate from current contract data.
- Payroll status is `Draft -> Calculated -> Reviewed -> Approved -> Paid`.
- Status changes use explicit services and record the responsible user and timestamp.
- Approved payroll cannot be recalculated or edited through normal flows.
- Correction/reversal runs and enforced separation of duties are out of scope.

## 8. Payment

- Payment is allowed only for an approved payroll item.
- One completed payment must equal the item's net salary.
- Saving that payment marks the item paid; payroll becomes `Paid` after every item is fully paid.
- Partial, excessive, failed, refunded, and reversed payments are out of scope.

## 9. Permissions

| Area | Admin | HR Manager | Payroll Officer | Employee |
|---|---|---|---|---|
| Employees/contracts | Manage | Manage | View | Own only |
| Attendance/leave | Manage | Manage/approve | View | Own/submit |
| Payroll inputs and runs | Manage | No | Manage | No |
| Payslips | All | Limited | All | Own only |
| Payments | Manage | No | Manage | No |

Authorization is enforced server-side and at object level. Navigation visibility is not authorization.

## 10. Explicitly Out of Scope

Recruitment, performance management, multiple companies/countries/currencies, advanced reports, complex shifts or leave, progressive taxes, legal compliance, proration, retroactive corrections, partial payments, bank/accounting integrations, notifications, and a general-purpose audit subsystem.
