from django.conf import settings
from django.db import models


class UserSecurityProfile(models.Model):
    """Tracks whether a login still needs to rotate its initial/reset password.

    Only users provisioned through a guarded service (create_staff_user,
    create_employee_with_account) with the shared default password get a row
    here — a superuser created via createsuperuser has none and is never forced.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="security_profile"
    )
    must_change_password = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} security profile"
