# HRP Task Brief Template

Copy this template into the Jira ticket or a temporary task file. One task brief should describe one reviewable change.

## Identity

- **Ticket:** HRP-___
- **Title:**
- **Owner:**
- **Context version/commit:**
- **Related decision IDs:**

## Outcome

Describe the user-visible or system outcome in one or two sentences.

## Acceptance Criteria

- [ ]
- [ ]
- [ ]

Use exact examples for calculations, permissions, and status changes.

## In Scope

-

## Out of Scope

-

## Business Rules and Invariants

Reference confirmed rules in `business-rules.md`. Repeat the critical rules that directly constrain this task.

-

## Permissions

| Action | Admin | HR Manager | Payroll Officer | Employee |
|---|---:|---:|---:|---:|
| Example | Yes | No | No | Own only |

Include object-level rules such as "employee may access only their own record."

## Inputs and Outputs

- Inputs:
- Outputs:
- Validation failures:
- Side effects/audit events:

## Interfaces and Dependencies

- Models:
- Public service functions:
- Templates/pages:
- Blocking tickets or decisions:

## Files Provided to the AI

List every file included in the context bundle. Do not assume a web AI can inspect the repository.

- `AI_CONTEXT.md`
- this task brief
-

## Files Allowed to Change

-

Changes outside this list require explicit approval.

## Required Tests

- Happy path:
- Boundary cases:
- Permission failures:
- Database constraints:
- Regression case:

## Manual Verification

1.
2.

## Definition of Done

- [ ] Acceptance criteria pass.
- [ ] Validation and permissions are tested.
- [ ] Migration is included if required.
- [ ] Targeted tests pass.
- [ ] Diff contains no unrelated changes or sensitive data.
- [ ] Documentation is updated when an interface or rule changed.
- [ ] Human review is complete.

## Open Questions

Do not let an AI invent answers. Reference `open-questions.md` or create a decision proposal.

- None / Q-___

