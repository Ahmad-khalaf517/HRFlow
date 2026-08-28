# HRFlow MVP Security and AI Data Rules

## 1. MVP Boundary

HRFlow is an MVP demonstration using synthetic data. Production security, legal retention, bank-data encryption, compliance certification, and incident operations are out of scope.

The following minimum rules still apply because they prevent easy mistakes and do not require a separate subsystem.

## 2. Never Put in Consumer Web AI

- Real employee names, contact details, salaries, leave reasons, bank data, tax data, or payslips.
- Passwords, cookies, API keys, access tokens, private keys, or `.env` files.
- Production database rows, dumps, logs, or screenshots.
- Proprietary code when company policy does not allow it.

Use synthetic examples such as `EMP-001`, `Demo Employee`, and invented salary values.

Turning off model training or using a temporary chat does not authorize uploading sensitive information.

## 3. Safe AI Workflow

- Use only organization-approved AI services.
- Upload the smallest relevant, sanitized context.
- Review every file and prompt before uploading.
- Treat generated code and commands as untrusted until reviewed.
- Never merge generated changes without tests and human review.
- Report accidental sensitive-data uploads immediately.

## 4. Application Minimums

- Use Django authentication, Groups, and Permissions.
- Enforce permissions in views/services, not only templates.
- Employees may access only their own profile, attendance, leave, and payslips.
- Use POST and CSRF protection for state-changing actions.
- Do not commit secrets; use environment variables.
- Keep `DEBUG=False`, HTTPS, and secure cookies as deployment requirements.
- Do not log passwords, tokens, bank data, or complete payroll objects.
- Use only synthetic seed/demo data.

## 5. Lightweight Traceability

Use existing actor and timestamp fields rather than building a generic audit-log subsystem:

- leave: `approved_by`, `approved_at`;
- payroll: `created_by`, `reviewed_by`, `approved_by`, and corresponding timestamps;
- bonus/deduction/payment: `created_by`, `created_at`;
- common models: `created_at`, `updated_at`.

A full immutable audit trail is a future production feature.

## 6. Before Any Real Deployment

Stop and perform a separate production-readiness review covering jurisdiction, real payroll rules, sensitive-field encryption/masking, audit logging, retention, backups, monitoring, and organizational access controls.
