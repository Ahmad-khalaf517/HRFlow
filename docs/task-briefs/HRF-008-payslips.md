# HRF-008 — Printable payslips

## Task and ownership

- Context commit: `8a67cac`; branch: `codex/new-feature`.
- Owner: Person 3 / payroll. The implementation agent owns the shared-file
  integration queue for this branch during this task.
- Outcome: authenticated, printable HTML payslips from saved payroll items.
- Dependencies: HRF-25/26/28; payroll migration 0002; the remaining HRF-007
  snapshot protections are the first prerequisite commit.
- Follow accounts -> employees -> attendance -> payroll. Employee/contract
  models are read-only dependencies; attendance internals are not modified.

## Scope and interfaces

- Allowed: payroll models/services/admin/migrations/tests/URLs/templates;
  this brief and the relevant schema documentation.
- Shared integration: templates/base.html, config/views.py, static/css/src/input.css,
  static/css/dist/output.css, and narrowly scoped dashboard regression tests.
- Public read interface: payslip_items_for_user(user); payroll:payslip-list and
  payroll:payslip-detail. Existing calculation/transition signatures remain stable.
- No PDF storage/generation, payment workflow, notifications, new framework,
  attendance implementation, or real record data.
- Render from PayrollItem without writing Payslip metadata on GET.

## Binding requirements and decisions

- business-rules.md sections 3, 7, 9 and delivery-plan.md HRF-007/008.
- Q-002/003/004 are confirmed in the canonical business rules (2026-09-01).
  TEAM_CONTEXT.md's decision table and baseline descriptions are stale.
- Q-001 remains Pending; this task neither resolves it nor uses real data.
- Proposed publication rule: approved/paid items only, consistent with the
  accepted implementation plan; no draft-preview or separate publishing workflow.
- Admin/Payroll Officer: all published slips. Employee: own linked records only.
- HR Manager's "Limited" access is undefined; clarification requested before
  implementing any HR-specific grant. No department-wide permission is inferred.
- Snapshot migrations leave previously unknown values empty; historical values
  are never reconstructed from today's contract. Incomplete historical items
  cannot be represented as complete issued payslips.
- Attendance inputs are still mocked. Rendering tests use explicit synthetic
  facts; connecting actual attendance remains Person 2's separate dependency.

## Steps and acceptance criteria

1. Snapshot prerequisite: save employee identity, currency, contract/rate/tax
   inputs and calculation version alongside existing monetary facts. Reject
   negative components/net. Guard approved/paid records in ordinary model/admin
   operations; serialize service transitions against the current stored status.
   Test saved values, rollback, stale objects, admin denial and legacy migration.
2. Payslip read workflow: user-scoped list/detail, approved/paid eligibility,
   complete snapshots only; no reads from current contract for displayed values.
   Test anonymous, own/other employee, manager, missing-profile, unpublished,
   missing record and no-write GET behavior.
3. UI integration: identity/period/USD, all earnings and deductions, gross and net,
   history, navigation, print control and printable layout. Use Deep Equity
   tokens. Verify desktop/mobile, browser print output and denied URL access.

Exact synthetic example: basic 3000.00, allowances 150.00, overtime 1 hour = 18.75,
bonus 0.00, absence 1 day = 100.00, unpaid leave/manual deduction 0.00,
tax 316.88, gross 3168.75, total deductions 416.88, net 2751.87 USD.
Changing contract/profile/tax configuration must not change the issued slip.

## Validation and review

- Each code step: focused behavior tests, lint, migration check and diff review;
  commit only after its checks pass.
- Full suite at baseline and final integration; synthetic isolated test database.
- UI step: browser workflow, mobile layout and print inspection; rebuild CSS.
- Record executed checks below. No shared/production database commands.
- Another person's review remains required before merge.

## Execution record

- Baseline: Ruff passes; 97 tests and 4 subtests passed on isolated SQLite.
- Step 1: 43 payroll tests and 10 subtests passed, including migration of a
  legacy approved item without fabricated historical inputs. Django check,
  migration drift check, Ruff and diff whitespace checks pass. Reviewed generated
  migration operations and SQLite SQL. Browser: synthetic Admin opens an approved
  item in view-only mode with the expected values and no Save/Delete controls.
- Database note: SQLite validates behavior/migration/constraints here; actual
  PostgreSQL concurrency has not been exercised. Model/Admin guards do not claim
  protection against direct SQL or bulk ORM writes outside the workflow.
- Step 2: 57 payroll tests and 21 subtests passed. Browser: Admin history shows
  all three synthetic approved slips; Employee history shows only their own;
  guessed coworker URL returns 404 without identity/amounts. The detail matches
  the documented example. CSS rebuilt; friendly unavailable page added after
  browser review. HR-specific grants remain pending clarification.
- Step 3: full regression suite passes: 128 tests and 31 subtests. Django check,
  makemigrations --check --dry-run, Ruff and git diff --check pass; CSS rebuilt
  with npm run build:css. No shared database was accessed or migrated.
- Browser checks: employee dashboard/sidebar -> own history -> detail; manager
  history; coworker URL denial; Admin read-only item; desktop and 390px mobile
  detail/history; mobile menu open/close. Fixed table-label overflow and verified
  document width equals the 390px viewport. As Payroll Officer, reviewed and
  approved a disposable calculated run, then followed its newly available
  payslip link and confirmed net USD 2751.87.
- Print verification limit: clicked Print payslip; the call entered native print
  handling, which the in-app browser cannot inspect. Dismissed it and verified
  the loaded print stylesheet (hidden navigation/controls, page margins and two
  columns). Native print preview/page count still requires a human browser check.
- Migration 0003 will reject pre-existing negative monetary/fact values rather
  than repair them silently. Legacy approved items with unknown inputs remain
  unavailable as payslips; any recovery requires a separate owner-approved task.

## Reproducing automated checks

Use the installed requirements with an isolated test database. The checks above
set `DATABASE_URL=sqlite:///:memory:` and `PYTHON_DOTENV_DISABLED=1` and applied
`MD5PasswordHasher` only in the test process to keep synthetic account tests fast.
Application password settings are unchanged. Executed pytest at baseline, for
each affected payroll step, and across all configured testpaths at integration.

Before merge: define HR Manager's Limited permission, inspect native print
preview, and obtain the required second-person review. Real attendance integration
and PostgreSQL concurrency verification remain separate outstanding dependencies.
