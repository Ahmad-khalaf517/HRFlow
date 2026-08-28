# HR & Payroll Management System — Recommended Free Tools & Libraries

## 1. Core Backend

### Python

Free and open source.

Recommended version:

```text
Python 3.12+
```

### Django

Free and open source.

Recommended:

```text
Django 5.x
```

Use Django for:

- ORM
- authentication
- permissions
- forms
- templates
- admin
- validation

### PostgreSQL

Free and open source.

Use PostgreSQL instead of SQLite for the team project because it is closer to a real production relational database and reduces surprises around relational behavior.

---

# 2. Frontend

## Tailwind CSS

Free and open source.

Recommended for:

- layout
- forms
- tables
- cards
- responsive design

## Alpine.js

Free and open source.

Use only for small interactions such as:

- dropdowns
- modals
- toggles
- tabs

Do not add a large JavaScript framework for this project.

## HTMX

Free and open source.

Optional.

Good use cases:

- filter tables without full reload
- dependent dropdowns
- inline approval actions
- modal forms

Do not use HTMX everywhere just because it is available.

## Icons

Recommended free options:

- Lucide Icons
- Heroicons

Both work well for professional admin interfaces.

---

# 3. Django UI Helpers

## django-widget-tweaks

Free and open source.

Useful for adding Tailwind classes to Django form fields without writing a custom rendering system immediately.

Recommended for this deadline.

## django-filter

Free and open source.

Useful for employee, attendance, and payroll filtering.

Optional but valuable.

---

# 4. Environment / Configuration

## python-dotenv

Free and open source.

Alternative: `django-environ`.

Recommendation:

Use `django-environ` if the team already knows it; otherwise use `python-dotenv` for simplicity.

Do not commit secrets.

Example values:

```text
SECRET_KEY
DEBUG
DATABASE_URL
```

---

# 5. PDF Payslips

## WeasyPrint

Free and open source.

Recommended if the environment can install its system dependencies.

Advantages:

- HTML/CSS to PDF
- easy to reuse payslip template

Potential issue:

- native/system dependencies may be annoying on some Windows setups

## xhtml2pdf

Free and open source.

Simpler fallback but weaker CSS support.

## ReportLab

Free/open-source core.

Very reliable, but PDF layout is coded manually rather than using normal HTML templates.

### Recommendation for one week

Use a printable HTML payslip first. Try WeasyPrint only after the complete flow works; if installation causes problems, keep PDF generation out of the MVP.

---

# 6. Testing

## pytest

Free and open source.

## pytest-django

Free and open source.

Recommended over relying only on Django's default test runner if the team is comfortable with pytest.

## factory_boy

Free and open source.

Optional.

Useful for generating test employees/contracts but not necessary for the MVP.

---

# 7. Code Quality

## Ruff

Free and open source.

Recommended for:

- linting
- import sorting
- formatting support

It replaces several older Python tooling combinations.

## pre-commit

Free and open source.

Optional but recommended if setup is quick.

Possible hooks:

- Ruff
- whitespace checks
- end-of-file fixer

Do not create a complicated quality pipeline for a one-week project.

---

# 8. Database / ERD Tools

Since Figma is not being used, use documentation-driven design.

Recommended free ERD options:

### Mermaid

Free and works directly inside Markdown on GitHub and many editors.

Use Mermaid in `erd.md` as the source of truth.

### dbdiagram.io

Has a free tier and is convenient for manually visualizing the ERD.

Optional.

### DBeaver Community

Free and open source database GUI.

Useful for:

- inspecting PostgreSQL
- checking rows
- debugging relations
- running SQL

---

# 9. API / Request Testing

If you do not build a REST API, these are not required.

If you add endpoints:

### Bruno

Free/open-source API client.

### Postman

Has a free tier but is not necessary for the MVP.

Recommendation: Bruno if needed.

---

# 10. Project Management

## Jira

Use the team/education/free option available to your team.

Track:

- epics
- stories
- dependencies
- status
- assignee
- daily blockers

## GitHub

Free for private/public repositories within common team needs.

Use:

- issues if needed
- pull requests
- branches
- code review

---

# 11. AI Development Tools

Use whichever assistants the team already has access to.

Tool choice does not override `security-and-data-policy.md`. Free/personal web accounts may receive only a manually reviewed, sanitized, bounded context bundle. Real employee, payroll, bank, tax, payment, credential, production, and other Restricted data are prohibited.

Recommended usage style rather than product dependence:

- Claude Code / Claude in IDE for scoped implementation and repository reasoning
- GitHub Copilot if already available
- ChatGPT for architecture, debugging, tests, review, documentation, and prompts

Do not depend on paid AI features for something the project cannot function without.

The repository must remain understandable and maintainable without AI.

Standardize the workflow rather than relying on individual prompt habits:

```text
task brief
-> sanitized context bundle
-> context check
-> bounded implementation
-> local tests
-> independent review
-> human-reviewed PR
```

See `ai-agent-guide.md` and `../AI_CONTEXT.md`.

---

# 12. Recommended Minimal Dependency Set

Keep dependencies small.

Example:

```text
Django
psycopg[binary]
django-widget-tweaks
django-filter
python-dotenv
pytest
pytest-django
```

Optional:

```text
weasyprint
ruff
```

Frontend:

```text
Tailwind CSS
Alpine.js
Lucide Icons
```

Only add HTMX when a specific interaction benefits from it.

---

# 13. Recommended Development Environment

- VS Code
- Git
- GitHub
- PostgreSQL
- DBeaver Community
- Node.js only for Tailwind build tooling
- Python virtual environment

Suggested commands:

```text
python -m venv .venv
pip install -r requirements.txt
npm install
python manage.py migrate
python manage.py runserver
```

---

# 14. Tool Selection Principle

For a one-week deadline, every library must answer this question:

> Does this remove more work than it creates?

If not, do not add it.
