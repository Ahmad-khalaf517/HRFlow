# HRFlow — MVP Business Rules

## 1. Scope

These rules are intentionally limited to a focused MVP. The objective is a reliable demonstration of one complete payroll flow, not a production payroll platform.

Advanced cases are explicitly excluded so that developers and AI assistants do not expand the project accidentally.

## 2. MVP Assumptions

- One company.
- One configurable currency.
- Monthly payroll only.
- Synthetic/demo employee data only.
- Whole-day attendance and leave rules.
- One active contract per employee.
- One simple tax calculation method.
- One full payment per payroll item.
- No legal-compliance claim.

The few owner decisions still required are listed in `open-questions.md`.

## 3. Money

- Use Python `Decimal` and Django `DecimalField`; never use `float`.
- Store monetary values with two decimal places.
- Round final component amounts using `ROUND_HALF_UP`.
- Negative salary, bonus, deduction, tax, payment, or net-pay values are invalid.
- Currency conversion is out of scope.

## 4. Employees and Contracts

- `employee_number` is unique.
- Salary belongs to `Contract`.
- An employee can have contract history but only one contract marked active.
- Contract `end_date` cannot precede `start_date`.
- Only active employees with an active contract are included in payroll.
- Mid-month hires, terminations, contract changes, suspension, and salary proration are out of scope. Demo data must avoid these cases.
- Historical contracts are deactivated, not deleted when referenced.

## 5. Attendance

- One attendance record exists per employee and date.
- Attendance stores check-in, check-out, worked hours, overtime hours, and status.
- Attendance never stores overtime pay or monetary deductions.
- `worked_hours` is calculated from check-in/check-out.
- `overtime_hours = max(worked_hours - contract working_hours_per_day, 0)`.
- Check-out must be after check-in.
- Overnight shifts, breaks, grace periods, lateness deductions, biometric devices, and overtime approval are out of scope.

## 6. Leave

- Leave requests use `pending`, `approved`, `rejected`, or `cancelled`.
- Employees submit requests; HR approves or rejects them.
- An employee cannot approve their own request.
- End date cannot precede start date.
- Overlapping pending or approved requests are rejected.
- `requested_days` is calculated by the system and is not manually editable.
- Only approved unpaid leave affects payroll.
- Half days, leave balances, holiday calendars, carry-over, and complex cancellation rules are out of scope.

For the MVP, leave day counting follows the approved answer to Q-004.

## 7. Payroll Period

- Payroll is monthly.
- Use `month` and `year` as the unique period identity.
- `period_start` and `period_end` are derived as the first and last calendar dates of that month.
- Only one payroll run may exist for a month/year.
- One payroll item exists per included employee.

## 8. Payroll Calculation

High-level formula:

```text
Gross = Basic Salary + Allowances + Overtime Pay + Bonuses

Total Deductions =
Absence Deduction
+ Unpaid Leave Deduction
+ Manual Deductions
+ Tax

Net Salary = Gross - Total Deductions
```

Recommended MVP formula, pending Q-003 confirmation:

```text
Daily Rate = Basic Salary / 30
Hourly Rate = Daily Rate / Contract Working Hours Per Day
Overtime Pay = Overtime Hours * Hourly Rate * 1.5
Absence Deduction = Absence Days * Daily Rate
Unpaid Leave Deduction = Unpaid Leave Days * Daily Rate
```

Allowances use the active contract's fixed monthly allowance. Bonuses and manual deductions are included when their effective date falls inside the payroll month and their status is active/approved.

### Simple demonstrative tax

`TaxBracket` selects one matching bracket using gross salary:

```text
min_amount <= gross_salary <= max_amount
```

`max_amount = NULL` means no upper limit.

```text
Tax = fixed_amount + (gross_salary * percentage / 100)
```

This is a simple demonstrative rule, not a progressive or legally compliant tax engine.

## 9. Payroll Snapshot

`PayrollItem` stores the values used for that employee and month:

- basic salary and allowances;
- overtime hours and amount;
- bonuses;
- absence and unpaid-leave days/deductions;
- manual deductions and tax;
- gross, total deductions, and net salary.

Old payslips use these saved values. They must never recalculate from the employee's current contract.

## 10. Payroll Workflow

```text
Draft -> Calculated -> Reviewed -> Approved -> Paid
```

- Payroll Officer may calculate, review, and approve in the MVP.
- Admin may perform all payroll actions.
- Each transition records the responsible user and timestamp where the model provides the field.
- Approved payroll cannot be recalculated through the normal UI.
- Correction/reversal workflows and separation of duties are out of scope.
- If approved payroll is wrong during the demo, an Admin corrects the demo data and recreates the run before payment.

## 11. Payments

- Payment is allowed only for an approved payroll item.
- MVP payment amount must equal the payroll item's net salary.
- Saving the completed payment marks the item paid.
- Payroll becomes `Paid` after every payroll item has one completed full payment.
- Partial payments, overpayments, failed-payment processing, refunds, and reversals are out of scope.

## 12. Permissions

- Admin: full access.
- HR Manager: employees, contracts, attendance, and leave approval.
- Payroll Officer: payroll inputs, calculation, review, approval, payslips, and payments.
- Employee: own profile, attendance, leave requests, and payslips only.

Permissions are enforced server-side. Hiding a navigation item is not authorization.

## 13. Explicitly Out of Scope

- Real payroll/legal compliance.
- Multiple companies, countries, currencies, or pay frequencies.
- Proration and mid-period contract changes.
- Progressive taxes, exemptions, benefits, and social contributions.
- Complex shifts, breaks, holidays, and leave balances.
- Separate reviewer/approver enforcement.
- Payroll corrections, reversals, and retroactive adjustments.
- Partial or failed payment workflows.
- Bank integration, accounting integration, and notifications.
- General-purpose audit-log subsystem.
