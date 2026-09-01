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
