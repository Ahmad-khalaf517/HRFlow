# HRP Remaining MVP Questions

Only four owner decisions remain. Everything else is deliberately fixed or excluded for the one-week MVP.

| ID | Question | Recommended default |
|---|---|---|
| Q-001 | Confirm that the one-week MVP uses synthetic/demo data and is not used for real payroll. | Yes. |
| Q-002 | Which single currency code should appear in the UI and payslip? | USD, matching the existing demo scenario. |
| Q-003 | Approve the simple rate rules: salary ÷ 30 for daily rate, daily rate ÷ contract hours/day for hourly rate, and overtime at 1.5×. | Approve. |
| Q-004 | Should leave count Monday–Friday only, excluding Saturday/Sunday, with no holiday calendar? | Yes. |

Replying “approve all MVP defaults” resolves all four questions.

After approval:

1. Add one accepted decision record in `decisions/0001-mvp-payroll-policy.md`.
2. Change the relevant wording in `business-rules.md` from recommended to confirmed.
3. Use the decision ID in payroll-related task briefs.

