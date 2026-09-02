from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from accounts.constants import DEFAULT_INITIAL_PASSWORD, EMPLOYEE_GROUP


def create_employee_with_account(form):
    """Save an Employee and its Django login as one transaction."""

    try:
        with transaction.atomic():
            employee = form.save()
            user = get_user_model().objects.create_user(
                username=employee.employee_number,
                password=DEFAULT_INITIAL_PASSWORD,
                first_name=employee.first_name,
                last_name=employee.last_name,
                email=employee.email,
            )
            user.groups.add(Group.objects.get(name=EMPLOYEE_GROUP))
            employee.user = user
            employee.save(update_fields=["user", "updated_at"])
            return employee
    except IntegrityError as exc:
        raise ValidationError(
            {"employee_number": "A user with this employee number already exists."}
        ) from exc


def update_employee_and_account(form):
    """Save an Employee and keep its linked login's username/name/email in sync."""

    try:
        with transaction.atomic():
            employee = form.save()
            if employee.user_id:
                user = employee.user
                user.username = employee.employee_number
                user.first_name = employee.first_name
                user.last_name = employee.last_name
                user.email = employee.email
                user.save(update_fields=["username", "first_name", "last_name", "email"])
            return employee
    except IntegrityError as exc:
        raise ValidationError(
            {"employee_number": "A user with this employee number already exists."}
        ) from exc
