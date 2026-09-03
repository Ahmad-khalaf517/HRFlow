# HRF-030 — Stitch UI alignment and implemented-flow hardening

## Task and ownership

- Request: compare every screen in Stitch project `16509451695928100669`
  (Remix of Zenith HR & Payroll System, updated 2026-09-01) with the application,
  fix mismatches, exercise invalid inputs and messages, and verify the whole app.
- Context commit: `9e81b3b`, branch `codex/new-feature`.
- Integration owner: Codex for this user-authorized review. Changes proceed in
  separate app-sized commits: shared/accounts, Person 1 employees, Person 2
  attendance, Person 3 payroll, then final integration verification. No concurrent
  migration ownership or change to the accounts -> employees -> attendance ->
  payroll dependency direction.
- Dependencies: existing employee/contract, attendance/leave, HRF-21–29 and
  HRF-008 implementations and applied migrations. No migration assumed necessary.

## Scope and interfaces

- Allowed: application templates, shared CSS/JS and navigation, existing views,
  forms/services, tests, and review documentation for confirmed requirements.
- Public attendance service signatures and payroll snapshot semantics remain
  binding. Payroll must not query attendance models directly.
- Follow the reference's Deep Equity layout, typography, colors, tables, status
  feedback and responsive behavior. Keep HRFlow product naming and real data
  from the local synthetic fixture; do not copy mock financial totals as live data.
- Reference-only controls for unimplemented or explicitly excluded features
  (payments, exports, notifications, analytics, advanced approvals) are recorded
  as gaps, not added as dead controls or invented business workflows.
- No new dependencies, remote database writes, real employee data, deployment,
  or changes to Stitch itself.

## Binding decisions and permission cases

- `docs/business-rules.md` is current: Q-002–004 were confirmed on 2026-09-01;
  their Pending labels in TEAM_CONTEXT are stale. Q-001 remains Pending.
- Admin/HR manage employees, contracts, attendance and leave; Payroll Officer
  reads HR facts and manages payroll; Employee sees only their own private data.
- No employee may approve their own leave or reassign records to another employee.
- HR Manager payslip access remains undefined as “Limited”; no new grant is inferred.
- Invalid dates, money, choices, identifiers, duplicates and unauthorized actions
  must fail with useful messages, no unintended writes, and no server errors.
- Money stays Decimal, approved snapshots stay immutable, state changes use POST
  and CSRF, and payslips use stored values.
- Q-001 and the security policy prohibit claiming this work authorizes real payroll
  deployment. Record remaining production blockers accurately.

## Acceptance and verification

- [ ] Map all 15 reference screens to an implemented route/state or explicit gap.
- [ ] Inspect each reference and counterpart; record fixes and justified differences.
- [ ] Shared shell, forms, statuses and feedback use consistent accessible components.
- [ ] Test each changed app before committing; rebuild and include compiled CSS.
- [ ] Exercise valid, invalid, empty and permission-denied paths with synthetic data.
- [ ] Browser-check desktop/mobile layouts, navigation, forms and workflow transitions.
- [ ] Run the complete isolated test suite, Ruff, Django system checks and migration
      drift check; review final diff and record the exact outcomes.
- [ ] Report missing workflows and real-deployment blockers separately from verified fixes.

## Work sequence

1. Capture reference assets and baseline test results; build the screen comparison matrix.
2. Fix and test shared navigation, accessibility, form feedback and loading behavior.
3. Compare and harden employee/contract and account screens and validation.
4. Compare and harden attendance/leave screens, filtering and object permissions.
5. Compare and harden payroll dashboard, run states and payslip screens.
6. Run full synthetic browser/behavior regression, document coverage and limitations,
   and request human review of the resulting commits before any deployment.

## Evidence

Reference assets and disposable databases are in ignored `.ai/` directories.
Only sanitized findings and reproducible tests belong in the repository.

### Step 1 — shared UI

- Baseline: 128 tests and 31 subtests passed on isolated SQLite.
- Added account-template CSS scanning, linked field errors/help, a focusable error
  summary, persistent dismissible feedback and accessible mobile/collapsed navigation.
- Removed destructive page-replacement loading behavior; submit state preserves
  the clicked action and resets on browser Back/Forward.
- Validation: 40 tests and 21 subtests passed (accounts and payslips), CSS rebuilt,
  changed Python lint passed. Browser verified 390px layout without horizontal
  overflow, menu open/Escape/focus return, and visible labeled links when collapsed
  to 80px at desktop size.

### Step 2 — employee directory and forms

- Aligned directory columns, active-contract filter, zebra table and compact forms;
  preserved search parameters during pagination and masked bank account display.
- Rejected invalid employee login names, case-insensitive duplicate emails,
  mismatched department/position and negative salary ranges. Staff flags alone no
  longer grant HR directory access; employment state and active flag agree.
- Validation: 56 tests and 10 subtests passed (employees/accounts), changed Python
  lint passed and CSS rebuilt. Browser checked officer read-only directory and HR
  empty submission: linked field errors, focused summary, and enabled retry.
- Main reconciliation: origin/main fetched on 2026-09-03 at dd12f18. Main checkout
  was clean. Three commits add validation/overlap checks, bonus editing, officer
  read access and deployment/health support; preserve these during integration.

### Step 3 — attendance and leave

- Merged main at dd12f18; all 142 tests and 37 subtests passed after reconciliation.
- Added validated attendance filters, department/search, scoped counts and paging;
  aligned dark tables, alternating rows, leave reason/actions and decision trace.
- Blocked own-record reassignment, staff-only privilege escalation, GET decisions,
  self-review and repeated transitions. Empty/forged forms and extreme date ranges
  return errors. Leave overlap checks serialize saves by employee on PostgreSQL.
- Added the required public attendance fact services; only recorded overtime,
  absences and approved unpaid weekday leave within the period are returned.
- Browser exercised invalid check-out, correction/save (9.50 hours, 1.50 overtime),
  leave submission (2 weekdays), approval, success feedback and approved table.
- Targeted suite: 37 attendance tests and 12 subtests passed. PostgreSQL concurrency
  is not verified by the isolated SQLite suite; no shared database was accessed.

### Step 4 — payroll lifecycle and payslips

- Payroll calculation now consumes the public attendance fact services and records
  calculation version `mvp-2`; historical `mvp-1` runs retain an explicit legacy
  input notice. Approved payroll and payslip snapshots remain immutable.
- Added validated run, breakdown and payslip filters with scoped counts and paging;
  invalid filter values return an empty result rather than silently broadening data.
- Aligned run creation, calculation, review, approval and payslip layouts with the
  reference lifecycle, summary cards, tax totals, actor trace and locked-state cues.
- Replaced illustrative dashboard payroll figures with the current stored cycle and
  aggregate values. Manager payslip search is limited to Admin and Payroll Officer;
  employees retain their existing self-only view.
- Browser exercised duplicate-period rejection, October creation, calculation from
  recorded attendance and approved unpaid leave, review, approval lock, current-cycle
  dashboard, payslip search/detail and the 390px layout using synthetic records.
- Targeted suite: 90 payroll/account tests and 51 subtests passed. Ruff passed for
  changed Python, compiled CSS was rebuilt and `git diff --check` passed.
