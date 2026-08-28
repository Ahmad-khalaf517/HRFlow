# HRP AI-Assisted Development Guide

## 1. Purpose

This guide defines a repeatable workflow for developers using repository-aware coding agents or free consumer web assistants such as ChatGPT or Claude.

AI improves drafting and review speed; it does not own business decisions, security approval, testing, or merge authority.

## 2. Canonical Context

Every AI task starts with `AI_CONTEXT.md`. Detailed authority is split deliberately:

| Concern | Source |
|---|---|
| Project invariants and change rules | `AI_CONTEXT.md` |
| Payroll and HR behavior | `business-rules.md` |
| Unresolved decisions | `open-questions.md` |
| Accepted decisions | `decisions/` |
| Security and permitted AI data | `security-and-data-policy.md` |
| Verification expectations | `testing-strategy.md` |
| Task scope | Current task brief/Jira ticket |

Do not paste all project documents into every conversation. Supply the canonical context, task brief, and only the files relevant to the task.

## 3. What Prompts Cannot Enforce

A prompt cannot guarantee compliance. Important rules need layered enforcement:

```text
Written rule
-> exact acceptance criterion
-> model/service validation
-> database constraint where possible
-> automated test
-> human review and CI
```

Examples:

- `Decimal` is a written rule and a code-review/test requirement.
- One attendance record per employee/date is also a database unique constraint.
- Approved payroll immutability is enforced by transition services, permissions, and tests.
- Employee-only payslip access is enforced by object-level authorization tests.

## 4. Task Sizing

Give an AI one bounded, independently reviewable outcome. A good task usually:

- touches one domain or public interface;
- names the allowed files;
- has three to eight acceptance criteria;
- includes relevant tests;
- can be reviewed in one pull request;
- has no unresolved blocking decision.

Good:

```text
Implement Contract validation and tests for only one active contract per employee.
```

Too broad:

```text
Build the HR and payroll system.
```

Split broad tickets before prompting. Smaller tasks reduce hallucination, context loss, and unsafe unrelated refactors.

## 5. Preparing a Task

1. Copy `task-brief-template.md` into the Jira ticket or a temporary local task file.
2. Fill in outcome, scope, acceptance criteria, permissions, interfaces, allowed files, and tests.
3. Check `open-questions.md` for blockers.
4. Attach accepted decision IDs.
5. Select the minimum source files and tests needed.
6. Review all selected material under `security-and-data-policy.md`.
7. Use synthetic examples only.

If a decision is missing, stop calculation implementation. The AI may help compare options or draft a decision record, but it must not choose company policy.

## 6. Web Chat Workflow

Free web ChatGPT/Claude cannot be assumed to see the repository or follow `CLAUDE.md`/`AGENTS.md` automatically.

Use one new conversation per ticket. Supply:

1. `AI_CONTEXT.md`.
2. The completed task brief.
3. Relevant approved decisions/business-rule sections.
4. Relevant source files.
5. Existing tests and interfaces.

Do not use a months-long general project chat. Old implementation details and stale decisions contaminate later answers.

### Step A — Context check

Prompt:

```text
Read the supplied HRP context and task files. Do not write code yet.

Return:
1. your understanding of the requested outcome;
2. the binding rules and acceptance criteria;
3. the files and interfaces you received;
4. contradictions, missing context, or pending decision IDs;
5. a minimal implementation and test plan.

Do not invent payroll, tax, leave, permission, or security policy.
```

The employee verifies the response. If the model missed a critical rule, correct the context before proceeding.

### Step B — Implementation draft

Prompt:

```text
Implement the approved plan.

- Change only the allowed files.
- Preserve canonical names and public interfaces.
- Add validation, permissions, constraints, and tests required by the brief.
- Use Decimal for all money.
- Do not fabricate missing files or claim to run commands.
- Return a unified diff or complete contents only for changed files.
- Finish with assumptions, commands to run, and remaining risks.
```

For large files, unified diffs are usually easier to review. Never accept `...existing code...` placeholders as an applicable patch.

### Step C — Local verification

The employee:

1. creates a feature branch;
2. applies the change manually or through an approved tool;
3. inspects the complete diff;
4. runs targeted tests and checks;
5. manually tests the affected flow;
6. fixes only verified issues;
7. records exact results in the PR.

Never execute generated shell commands without reading them. Never apply destructive database or Git commands from a chat without an approved recovery plan.

### Step D — Independent review

Start a fresh chat or ask a different reviewer. Provide the task, context, changed files/tests, and diff.

```text
Review this diff against AI_CONTEXT.md and the task acceptance criteria.

Prioritize:
- incorrect calculations or rounding;
- authorization and object-access failures;
- missing database constraints or transaction boundaries;
- payroll snapshot/history violations;
- unsafe status transitions;
- sensitive-data exposure;
- missing boundary and regression tests.

Do not rewrite the feature. Report evidence-backed findings by severity and file/location.
```

The original author decides each finding using code, tests, and confirmed policy—not model confidence.

## 7. Repository-Aware Agent Workflow

A coding agent that can inspect the repository should still receive a bounded task. Require it to:

1. read `AI_CONTEXT.md` and relevant sources;
2. inspect existing code/tests before planning;
3. identify files and dependencies;
4. make a minimal diff;
5. run targeted checks;
6. inspect its own diff;
7. report results and risks.

Repository access reduces manual context packaging but does not grant permission to change unrelated files, expose Restricted data, install arbitrary dependencies, merge, deploy, or make policy decisions.

## 8. Context Bundle Helper

`tools/build-ai-context.ps1` creates a single Markdown bundle from:

- `AI_CONTEXT.md`;
- a completed task file;
- explicitly selected relevant files.

Example:

```powershell
.\tools\build-ai-context.ps1 `
  -TaskFile .ai\tasks\HRP-013.md `
  -IncludeFiles docs\business-rules.md,employees\models.py,employees\tests\test_contracts.py `
  -ConfirmSanitized
```

The output is written to the operating-system temporary directory by default. The script rejects paths outside the repository and common secret/private-data file types. This is a guardrail, not automatic anonymization. The employee must review the generated bundle before upload.

## 9. Context Maintenance

Context must match the code revision.

- Put the commit hash or context version in the task brief.
- Update `business-rules.md` and an accepted decision in the same change.
- Update service-interface documentation when signatures change.
- Begin a new web chat after a material decision or merged interface change.
- Do not rely on the model to remember a correction from an old chat.

## 10. Pull Request Workflow

```text
Ready task
-> context check
-> small implementation
-> local tests
-> independent review
-> human diff review
-> PR/CI
-> merge
```

PR description:

```text
Ticket / outcome:
Decision IDs:
Files changed:
AI assistance used:
Tests and exact results:
Manual checks:
Migrations:
Security/privacy review:
Known risks or follow-ups:
```

No AI-generated change goes directly to `develop` or `main`.

## 11. Review Checklist

- [ ] Task has no unresolved blocking decision.
- [ ] Diff stays within declared scope.
- [ ] Canonical model and field names are preserved.
- [ ] Money uses `Decimal` with approved rounding.
- [ ] Date/calendar behavior follows an accepted decision.
- [ ] Permissions are enforced server-side and at object level.
- [ ] Database constraints protect critical invariants.
- [ ] Services own calculations and transitions.
- [ ] Payroll snapshot contains reproducible historical values.
- [ ] Duplicate payroll items and payments are prevented.
- [ ] Tests cover failure, permission, and boundary cases.
- [ ] Logs, fixtures, prompts, and diff contain no Restricted data.
- [ ] Exact test results and unverified risks are reported honestly.

## 12. Debugging Workflow

For a bug:

1. Provide the failing behavior, expected behavior, traceback with sensitive data removed, and relevant code/test.
2. Ask for root-cause analysis before a patch.
3. Add a failing regression test.
4. Apply the smallest root-cause fix.
5. Run the regression test and related suite.
6. Reject unrelated cleanup unless separately scoped.

## 13. Productivity Habits for the Team

- Keep a shared library of approved task briefs and prompts rather than personal prompt folklore.
- Spend five minutes improving acceptance criteria before spending thirty minutes correcting generated code.
- Use synthetic examples with exact expected numbers.
- Let one developer own updates to canonical business rules during the one-week sprint.
- Review and merge small PRs daily.
- Capture recurring AI mistakes as tests or short rules; do not rely on reminders in chat history.
- Measure useful outcomes: cycle time, review findings, escaped defects, and rework—not number of generated lines.
