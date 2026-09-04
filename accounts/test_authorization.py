from django.contrib.auth.models import Group, User
from django.test import TestCase

from .authorization import (
    can_manage_accounts,
    can_manage_hr_records,
    can_view_directory,
    in_groups,
    in_groups_or_superuser,
)


class AuthorizationPrimitiveTests(TestCase):
    def setUp(self):
        self.hr_manager = User.objects.create_user(username="auth-hr", password="testpass123")
        self.hr_manager.groups.add(Group.objects.get(name="HR Manager"))
        self.bare_superuser = User.objects.create_user(
            username="auth-superuser", password="testpass123", is_superuser=True
        )
        self.outsider = User.objects.create_user(username="auth-outsider", password="testpass123")

    def test_in_groups_ignores_superuser_status(self):
        self.assertTrue(in_groups(self.hr_manager, ["HR Manager"]))
        self.assertFalse(in_groups(self.bare_superuser, ["HR Manager"]))
        self.assertFalse(in_groups(self.outsider, ["HR Manager"]))

    def test_in_groups_or_superuser_accepts_either(self):
        self.assertTrue(in_groups_or_superuser(self.hr_manager, ["HR Manager"]))
        self.assertTrue(in_groups_or_superuser(self.bare_superuser, ["HR Manager"]))
        self.assertFalse(in_groups_or_superuser(self.outsider, ["HR Manager"]))

    def test_inactive_account_fails_both_checks_even_with_the_right_group(self):
        self.hr_manager.is_active = False
        self.hr_manager.save(update_fields=["is_active"])
        self.assertFalse(in_groups(self.hr_manager, ["HR Manager"]))
        self.assertFalse(in_groups_or_superuser(self.hr_manager, ["HR Manager"]))

    def test_named_policies_match_business_rules_groups(self):
        self.assertTrue(can_manage_accounts(self.hr_manager))
        self.assertTrue(can_manage_hr_records(self.hr_manager))
        self.assertTrue(can_view_directory(self.hr_manager))

        self.assertFalse(can_manage_accounts(self.bare_superuser))
        self.assertFalse(can_manage_hr_records(self.bare_superuser))
        self.assertTrue(can_view_directory(self.bare_superuser))  # directory view keeps the bypass

        self.assertFalse(can_manage_accounts(self.outsider))
        self.assertFalse(can_manage_hr_records(self.outsider))
        self.assertFalse(can_view_directory(self.outsider))
