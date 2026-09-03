from django import template

register = template.Library()


@register.filter
def startswith(value, prefix):
    """Used by templates/base.html to highlight exactly one sidebar nav item
    per employees sub-section (Employees/Departments/Positions/Contracts),
    since their URL names share the app_name 'employees' but not a prefix
    that Django's template `in` operator could safely check (a substring
    check would also match e.g. "employee-contract-tab" against "contract-").
    """

    if value is None:
        return False

    return str(value).startswith(prefix)


@register.filter
def has_group(user, group_names):
    """Used by templates/base.html to hide the Employees/Contracts nav links
    from users who lack _has_employee_view_access (employees/views.py) so the
    sidebar doesn't offer a link that 403s. `group_names` is comma-separated.
    """

    if not getattr(user, "is_authenticated", False):
        return False

    if user.is_superuser:
        return True

    names = [name.strip() for name in group_names.split(",")]

    return user.groups.filter(name__in=names).exists()


@register.simple_tag(takes_context=True)
def page_url(context, page):
    """Preserve every active list filter when moving between pages."""
    query = context["request"].GET.copy()
    query["page"] = page
    return "?" + query.urlencode()


@register.filter
def masked_account(value):
    return "•••• " + str(value)[-4:] if value else "—"


@register.filter
def in_groups(user, group_names):
    """Group membership or superuser access, mirroring
    employees.views.HRManagementRequiredMixin's allowed_groups check exactly.
    Used to hide the Edit/Deactivate/Terminate actions on the employee
    profile header from anyone those views would actually 403 (including
    the employee viewing their own record).
    """

    if not getattr(user, "is_authenticated", False):
        return False

    if user.is_superuser:
        return True

    names = [name.strip() for name in group_names.split(",")]

    return user.groups.filter(name__in=names).exists()
