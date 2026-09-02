from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

from .constants import DEFAULT_INITIAL_PASSWORD


@transaction.atomic
def create_staff_user(*, username, first_name, last_name, email, role):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username=username,
        password=DEFAULT_INITIAL_PASSWORD,
        first_name=first_name,
        last_name=last_name,
        email=email,
    )
    user.groups.add(Group.objects.get(name=role))
    return user
