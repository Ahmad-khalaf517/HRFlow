"""Single source of truth for HRFlow's role-group access checks (business-rules.md §9).

Before this module, accounts/employees/attendance each hand-rolled their own
`user.groups.filter(name__in=[...])` predicates. They had quietly drifted: employees'
and accounts' own management actions deliberately do not treat a Django superuser as
an automatic HRFlow role (see StaffUserViewPermissionTests.
test_superuser_payroll_officer_is_still_denied_user_management), but attendance's
equivalent checks did — a bare superuser could approve leave or manage attendance for
other employees while the identical action in employees/accounts would 403 them. That
gap is closed here by giving attendance's management checks the same policy.

Two membership styles are kept, both deliberate:

- `in_groups_or_superuser` — a Django superuser always passes. For read-mostly/
  directory-style access (browsing records, dashboards, payroll).
- `in_groups` — HRFlow's own role groups are the only source of truth; a bare
  superuser does NOT pass. For HRFlow's management/role actions (creating or editing
  employees, contracts, leave decisions, and staff accounts), so access always traces
  back to an assigned role rather than the separate is_superuser flag.

Both require an authenticated, active login, so deactivating an account
(accounts.views.StaffUserToggleActiveView) revokes access immediately even against a
still-live session — some of the checks replaced here previously skipped that check.
"""

from .constants import ACCOUNT_MANAGER_GROUPS, ADMIN_GROUP, HR_MANAGER_GROUP, PAYROLL_OFFICER_GROUP

# Distinct policies that happen to share the same two groups today (business-rules.md
# §9's "Employees/contracts: Manage" row vs. accounts' own staff-login management) —
# kept as separate names so one can diverge from the other without silently changing
# the other's meaning.
HR_MANAGEMENT_GROUPS = (ADMIN_GROUP, HR_MANAGER_GROUP)
DIRECTORY_VIEW_GROUPS = (ADMIN_GROUP, HR_MANAGER_GROUP, PAYROLL_OFFICER_GROUP)


def _authenticated_active(user) -> bool:
    return bool(user and user.is_authenticated and user.is_active)


def in_groups(user, group_names) -> bool:
    return _authenticated_active(user) and user.groups.filter(name__in=group_names).exists()


def in_groups_or_superuser(user, group_names) -> bool:
    return _authenticated_active(user) and (user.is_superuser or in_groups(user, group_names))


def can_manage_accounts(user) -> bool:
    """Create, edit, or deactivate HR Manager / Payroll Officer login accounts."""
    return in_groups(user, ACCOUNT_MANAGER_GROUPS)


def can_manage_hr_records(user) -> bool:
    """Manage employees, contracts, departments, positions, attendance, and leave
    decisions for people other than oneself."""
    return in_groups(user, HR_MANAGEMENT_GROUPS)


def can_view_directory(user) -> bool:
    """Browse the full employee/contract/attendance/leave directory, not just one's
    own record."""
    return in_groups_or_superuser(user, DIRECTORY_VIEW_GROUPS)
