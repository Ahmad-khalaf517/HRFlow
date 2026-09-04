from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .constants import DEFAULT_INITIAL_PASSWORD, STAFF_ACCOUNT_ROLES
from .models import UserSecurityProfile


def user_must_change_password(user) -> bool:
    """True only for logins provisioned with the shared default password."""
    if not user.is_authenticated:
        return False
    profile = getattr(user, "security_profile", None)
    return bool(profile and profile.must_change_password)


def mark_must_change_password(user):
    """Flag a login as still using its guarded-service default password."""
    UserSecurityProfile.objects.update_or_create(
        user=user, defaults={"must_change_password": True}
    )


def clear_must_change_password(user):
    UserSecurityProfile.objects.filter(user=user).update(must_change_password=False)


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
    mark_must_change_password(user)
    return user


@transaction.atomic
def update_staff_user(user, *, first_name, last_name, email, role):
    if role not in STAFF_ACCOUNT_ROLES:
        raise ValidationError({"role": "Select a valid staff role."})
    user.first_name = first_name.strip()
    user.last_name = last_name.strip()
    user.email = email.strip()
    user.full_clean(validate_unique=True, exclude=["password", "username"])
    user.save(update_fields=["first_name", "last_name", "email"])
    user.groups.remove(*Group.objects.filter(name__in=STAFF_ACCOUNT_ROLES))
    user.groups.add(Group.objects.get(name=role))
    return user


def set_staff_user_active(user, *, is_active):
    user.is_active = is_active
    user.save(update_fields=["is_active"])
    return user
