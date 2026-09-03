# HRF-030 — Stitch screen comparison matrix

Reference project: **Remix of Zenith HR & Payroll System (updated Sep 1)**,
project `16509451695928100669`. The reference was reviewed with synthetic data only.
“Aligned” means the implemented screen follows the reference information hierarchy,
state cues and visual system while preserving the approved HRFlow routes and rules.

| Stitch screen | Current counterpart | Review outcome |
|---|---|---|
| Approved Payroll (`3f9455…`) | `/payroll/runs/<id>/` in Approved state | Aligned lifecycle, totals, tax, actor trace and locked-state notice. Payment actions are absent because the payment workflow remains a documented gap. |
| Leave (`00b68…`) | `/attendance/leave-requests/` | Aligned summary cards, dark table header, status badges, actions and paging. Added validated employee/status filters and direct employee-profile links. |
| Employee Management (`158c…`) | `/employees/` | Aligned search/filter controls, directory columns, avatars, status treatment, alternating rows and paging. Filters preserve state and reject invalid values. |
| Calculation (`346647…`) | `/payroll/runs/<id>/` in Calculated state | Aligned summary cards and employee breakdown. Calculations now consume the documented attendance fact services; values remain `Decimal` snapshots. |
| Payment Details (`7391…`) | No route | **Gap.** The repository has payment schema elements but no approved end-to-end create/complete UI or service. No dead control was added. |
| Payslip Details (`5d610…`) | `/payroll/payslips/<id>/` | Aligned earnings/deductions sections and prominent net-pay footer. It renders only saved payroll-item values and preserves employee object-level access. |
| Payroll Officer Dashboard (`910e…`) | `/` for Payroll Officer | Replaced illustrative values with the current stored payroll cycle, employee count and gross/deduction/net totals. Quick links follow the officer’s allowed workflows. |
| Payroll Review (`09ab…`) | `/payroll/runs/<id>/` in Reviewed state | Aligned lifecycle stepper, review heading, actor trace, totals and approval action. State changes remain POST/CSRF protected. |
| Attendance (`9b0acc…`) | `/attendance/` | Aligned summary cards, filters, dark table and status badges. Added date/department/status/employee validation, scoped paging and safe invalid-filter behavior. |
| Contract Details (`dda70…`) | `/employees/contracts/<id>/` and `/employees/<id>/contract/` | Aligned employee/contract hierarchy, monetary details, duration and allowed actions. Existing contract-overlap and date rules remain authoritative. |
| Payments (`7f6ba…`) | No route | **Gap.** Full-payment behavior is specified in `docs/business-rules.md`, but the current implementation lacks the service, authorization and lifecycle UI required to expose it safely. |
| Create Payroll (`8ba2…`) | `/payroll/runs/new/` | Aligned compact period form, helper text and action hierarchy. Duplicate periods, invalid months/years and unauthorized service calls are rejected. |
| Payslips Management (`ef0a…`) | `/payroll/payslips/` | Aligned searchable/filterable table, employee/status/period context and detail action. Reference Download/Send controls are omitted: notifications are explicitly out of scope and no approved PDF/export requirement exists. |
| Employee Profile (`cf28…`) | `/employees/<id>/` | Aligned profile header, status/actions and overview/contract sections. Added authorized links to attendance, leave and payslips; HR Manager still receives no payslip grant. Reference Documents has no approved requirement or data model. |
| Payroll Overview (`f3c…`) | `/payroll/runs/` | Aligned run filters, lifecycle badges, totals including tax, employee counts and paging. Invalid filters return no rows with visible errors instead of broadening the result. |

## Shared behavior verified

- Desktop and 390px layouts keep page content within the viewport; wide data tables
  scroll inside their container.
- Navigation, form fields, error summaries, toasts, status badges and buttons use the
  shared accessible components and the deep-equity Stitch token set.
- Synthetic browser flows covered login, role navigation, invalid account and employee
  forms, attendance correction, leave submission/approval, payroll duplicate rejection,
  creation, calculation, review, approval lock, payslip filtering and detail display.
- Automated tests cover invalid identifiers, dates, times, money, choices, duplicates,
  forged object IDs, role denial, object scoping, repeated transitions and immutable
  approved snapshots.

## Deliberate limitations

- Payments remain incomplete and are not represented by nonfunctional controls.
- Separation of duties, corrections/reversals, notifications, PDF/export, advanced
  reports, leave balances, documents and legal payroll compliance were not invented.
- HR Manager “Limited” payslip access is unresolved, so no access was granted.
- PostgreSQL row-lock concurrency was not exercised by the isolated SQLite suite.
- Q-001 and the production-readiness items in `docs/security-and-data-policy.md`
  remain unresolved; this work does not authorize real employee or payroll data.
