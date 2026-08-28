# HRFlow Architecture and Business Decision Records

Use a short decision record whenever a choice affects calculations, data shape, security, permissions, or multiple modules.

Filename format:

```text
NNNN-short-title.md
```

Template:

```markdown
# NNNN — Decision title

- Status: Proposed | Accepted | Superseded
- Date: YYYY-MM-DD
- Owner:
- Related questions/tickets:

## Context

What must be decided and why?

## Decision

State the exact approved behavior, including examples where calculations are involved.

## Consequences

What becomes easier, harder, required, or out of scope?

## Verification

Which constraints, tests, pages, and documents prove the decision is implemented?
```

Accepted decisions override summaries in older planning documents. Update `business-rules.md` at the same time so implementers do not need to reconstruct policy from multiple files.
