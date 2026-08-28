# HRFlow MVP Testing Strategy

## 1. Goal

Protect the core demo flow and the calculations most likely to fail. The team should not attempt enterprise-scale coverage for this focused MVP.

## 2. Required Automated Tests

Prioritize these tests in order:

1. Only one active contract per employee.
2. One attendance record per employee/date.
3. Worked-hours and overtime-hours calculation.
4. Leave date validation, overlap rejection, and HR approval.
5. Unpaid-leave and absence day totals for a month.
6. Payroll formula with exact `Decimal` expected values.
7. PayrollItem snapshot remains unchanged after contract edits.
8. Approved payroll cannot be recalculated normally.
9. Employee cannot access another employee's payslip.
10. Full payment marks all items/payroll paid only when appropriate.

## 3. Small Boundary Set

For payroll calculations, include:

- no overtime/bonus/deduction;
- fractional value that exercises rounding;
- approved versus rejected leave;
- missing active contract;
- duplicate payroll month;
- repeated generation attempt;
- negative input rejection.

Proration, concurrent generation, partial payments, reversals, progressive tax, overnight shifts, and production security testing are outside this MVP.

## 4. Manual End-to-End Check

Before declaring the MVP demo-ready, run one synthetic scenario:

```text
Create employee
-> add active contract
-> record attendance
-> request and approve unpaid leave
-> add bonus and deduction
-> calculate payroll
-> review and approve
-> view employee payslip
-> record full payment
```

Record the exact input and expected gross, deductions, and net salary so every contributor tests the same result.

## 5. Commands

Once the Django project exists:

```text
pytest
ruff check .
python manage.py makemigrations --check --dry-run
python manage.py check
```

Run targeted tests during development and the full suite before merging into the shared integration branch.

## 6. Pull Request Note

Each PR states:

- tests run and result;
- manual check performed;
- anything not tested;
- remaining risk.
