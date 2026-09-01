# HRFlow Task Brief

## Task

- Ticket / title: HRF-23 — Tax Configuration
- Owner: Ahmad Khalaf (Person 3 — payroll)
- Context commit: c035acc
- Owning app: payroll
- Depends on tasks/migrations: none (uses existing `payroll.TaxBracket` model/migration)
- Required outcome: configurable demonstrative tax brackets that payroll calculation matches against gross salary.

## Scope

- In scope: list tax brackets, create a bracket, activate/deactivate a bracket.
- Out of scope: a progressive/legally compliant tax engine (explicitly out of scope per business-rules.md §10); editing an existing bracket's numbers in place (only create + toggle active, to keep historical calculations reproducible from the bracket that was active at calculation time — no versioning was requested).
- Files allowed to change: `payroll/*`.
- Public interfaces added: `payroll.services.get_matching_tax_bracket(gross_salary)` — first active bracket where `min_amount <= gross <= (max_amount or ∞)`, ordered by `min_amount`.
- Shared files requiring coordination: none beyond what HRF-21/22/24 already touched.

## Binding Context

- Relevant confirmed rules: business-rules.md §6 — `Tax = Fixed Amount + (Gross * Percentage / 100)` (Q-003, confirmed 2026-09-01); §3 money rules (`taxbracket_min_amount_gte_0`, `taxbracket_percentage_gte_0`, `taxbracket_max_amount_gte_min_amount` DB constraints).
- Relevant models/services/interfaces: `payroll.models.TaxBracket`; `payroll/forms.py:TaxBracketForm`; `payroll/views.py:tax_bracket_list/tax_bracket_create/tax_bracket_toggle`.
- Permission or object-access rule: `require_payroll_manager` gate.
- Pending decision IDs: None (Q-003 confirmed in `docs/business-rules.md` as part of this work — see HRF-25's brief for the full decision record).
- Data classification: Synthetic only — seeded 3 brackets (No tax / Standard / High) via `seed_payroll_demo_data`.

## Acceptance Criteria

- [x] Tax brackets can be configured.
- [x] Minimum and optional maximum amounts are supported.
- [x] Percentage and fixed amount are supported.
- [x] The matching bracket is selected based on gross salary (`get_matching_tax_bracket`).
- [x] Tax uses the defined demonstrative formula.
- [x] Negative tax values are not allowed (DB constraints on the bracket's own fields; `calculate_payroll` never produces a negative `tax_amount` from non-negative inputs).
- [x] The system does not claim legal tax compliance (no such language anywhere in the UI/docs).

## Required Review

- Manual workflow review: verified `/payroll/tax-brackets/` list, create, and toggle; confirmed the seeded "Standard" bracket (10%, 1000–4999.99) was the one matched for every seeded employee's gross salary during the HRF-25 calculation smoke test.
- Migration or framework command: `python manage.py check`, `makemigrations --check --dry-run`, `ruff check payroll/`.
- Expected observable result: bracket list shows Active/Inactive badges and correct min/max/percentage/fixed columns.

## Follow-up after teammate merges

- None — this ticket has no dependency on employees or attendance work landing.
