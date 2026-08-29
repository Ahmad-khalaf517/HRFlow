# HRFlow Documentation

Documentation and AI-assisted delivery pack for the focused HR and payroll Django MVP.

Start with [`AI_CONTEXT.md`](AI_CONTEXT.md). It defines the project invariants, document authority, safe change process, and required references.

## Running the Project Locally

Requires Python 3.12+, Node.js (for the Tailwind build), and Docker (for local PostgreSQL) — or a PostgreSQL 16 instance reachable via the `DB_*` variables below.

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env            # fill in local values; never commit .env

docker compose up -d            # starts PostgreSQL on localhost:5432
python manage.py migrate

npm install
npm run build:css               # one-off build; use `npm run watch:css` while developing

python manage.py createsuperuser
python manage.py runserver
```

Then visit `http://localhost:8000`. Run `pytest` for the test suite and `ruff check .` for linting.

The four Django apps (`accounts`, `employees`, `attendance`, `payroll`) are scaffolded and registered but intentionally empty — see `docs/jira-plan.md` for what each ticket adds next.

## Why Each Document Exists

You do not need to read every document for every task. Use this map to select the smallest reliable context.

| Document | Why we need it | Main users |
|---|---|---|
| `docs/HRFlow-Business-Requirements-Document.docx` | Aligns sponsors and the delivery team on the business problem, scope, requirements, and approval decisions. | Sponsor, product owner, HR, technical lead |
| `AI_CONTEXT.md` | Gives repository-aware AI tools a short, canonical set of rules and invariants before they change anything. | Developers and AI agents |
| `docs/project-plan.md` | Connects scope, architecture, ownership areas, delivery sequence, and the definition of done. | Delivery team |
| `docs/business-rules.md` | Prevents conflicting implementations by keeping calculations and behavioral rules in one authoritative place. | Product owner, developers, testers |
| `docs/open-questions.md` | Makes unresolved owner decisions visible so neither people nor AI invent company policy. | Sponsor, product owner, developers |
| `docs/decisions/` | Records accepted architecture and business decisions so later work does not reopen or contradict them. | Delivery team and AI agents |
| `docs/erd.md` | Defines entities, relationships, and database constraints before models and migrations are written. | Backend developers and reviewers |
| `docs/modules.md` | Defines application boundaries, responsibilities, public interfaces, and permissions to reduce duplicated or circular logic. | Developers and reviewers |
| `docs/user-flows.md` | Describes what each role does from start to finish, making UI and acceptance testing coherent. | Product owner, designers, developers, testers |
| `docs/jira-plan.md` | Turns the approved scope into bounded, ordered stories with dependencies and acceptance criteria. | Delivery team |
| `docs/testing-strategy.md` | States the minimum evidence needed to trust calculations, permissions, constraints, and the end-to-end flow. | Developers, testers, reviewers |
| `docs/security-and-data-policy.md` | Defines safe application behavior and what data may or may not be shared with web AI tools. | Everyone |
| `docs/tools-and-libraries.md` | Keeps technology choices consistent and discourages unnecessary dependencies. | Developers |
| `docs/ai-agent-guide.md` | Provides the repeatable workflow for preparing, prompting, checking, and reviewing AI-assisted work. | Teammates using ChatGPT, Claude, or coding agents |
| `docs/team-ai-context-prompt.md` | Provides a standalone project explanation that can be pasted into a new web-AI conversation. | Teammates using web AI |
| `docs/task-brief-template.md` | Gives each AI session a bounded outcome, allowed files, acceptance criteria, and verification requirements. | Developers and AI agents |
| `AGENTS.md` and `CLAUDE.md` | Act as small tool-specific entry points that direct agents to the canonical context instead of duplicating it. | Repository-aware AI agents |

## Suggested Reading by Task

- Business or scope review: BRD, `business-rules.md`, `open-questions.md`, and `user-flows.md`.
- Backend implementation: `AI_CONTEXT.md`, the task brief, relevant business rules, `erd.md`, `modules.md`, and tests.
- Planning and coordination: `project-plan.md`, `jira-plan.md`, `open-questions.md`, and accepted decisions.
- Web ChatGPT or Claude work: `team-ai-context-prompt.md`, a completed task brief, and only the relevant source files and rules.

## Important

HRFlow remains an MVP specification. Before calculation work begins, answer the blocking items in `docs/open-questions.md`, record accepted decisions, and update the related Jira acceptance criteria and tests.

Never use real employee, salary, bank, tax, payment, credential, or production data in consumer web AI tools. See `docs/security-and-data-policy.md`.
