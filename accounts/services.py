from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .constants import DEFAULT_INITIAL_PASSWORD, STAFF_ACCOUNT_ROLES


@transaction.atomic
def create_staff_user(*, username, first_name, last_name, email, role):
    username = username.strip()
    if role not in STAFF_ACCOUNT_ROLES:
        raise ValidationError({"role": "Select a valid staff role."})

    user_model = get_user_model()
    if user_model.objects.filter(username__iexact=username).exists():
        raise ValidationError({"username": "A user with this username already exists."})

    user = user_model(
        username=username,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        email=email.strip(),
    )
    user.set_password(DEFAULT_INITIAL_PASSWORD)
    user.full_clean(validate_unique=True)
    try:
        user.save()
    except IntegrityError as exc:
        raise ValidationError(
            {"username": "A user with this username already exists."}
        ) from exc
    user.groups.add(Group.objects.get(name=role))
    return user
