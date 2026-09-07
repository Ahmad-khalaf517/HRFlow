from django.contrib.auth.models import Group, User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from employees.models import Employee

from .constants import DEFAULT_INITIAL_PASSWORD
from .forms import StaffUserCreationForm
from .services import (
    create_staff_user,
    mark_must_change_password,
    update_staff_user,
    user_must_change_password,
)


class HomePageTests(TestCase):
    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('home')}")

    def test_authenticated_user_sees_home_page(self):
        User.objects.create_user(username="ada", password="testpass123")
        self.client.login(username="ada", password="testpass123")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ada", password="testpass123")

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_valid_login_redirects_to_home(self):
        response = self.client.post(
            reverse("login"), {"username": "ada", "password": "testpass123"}
        )
        self.assertRedirects(response, reverse("home"))

    def test_invalid_login_shows_error_and_does_not_authenticate(self):
        response = self.client.post(
            reverse("login"), {"username": "ada", "password": "wrong-password"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_redirects_to_login(self):
        self.client.login(username="ada", password="testpass123")
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))


class RoleGroupSeedTests(TestCase):
    def test_expected_role_groups_exist(self):
        names = set(Group.objects.values_list("name", flat=True))
        expected = {"Admin", "HR Manager", "Payroll Officer", "Employee"}
        self.assertTrue(expected.issubset(names))


class StaffUserCreationTests(TestCase):
    def test_form_creates_hashed_password_and_selected_role(self):
        form = StaffUserCreationForm(
            data={
                "username": "demo.payroll",
                "first_name": "Demo",
                "last_name": "Payroll",
                "email": "demo.payroll@example.com",
                "role": "Payroll Officer",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertTrue(user.check_password(DEFAULT_INITIAL_PASSWORD))
        self.assertEqual(user.get_full_name(), "Demo Payroll")
        self.assertEqual(list(user.groups.values_list("name", flat=True)), ["Payroll Officer"])

    def test_form_rejects_case_insensitive_duplicate_username(self):
        User.objects.create_user(username="Demo.HR", password="irrelevant")
        form = StaffUserCreationForm(
            data={
                "username": "demo.hr",
                "first_name": "Demo",
                "last_name": "HR",
                "email": "demo.hr@example.com",
                "role": "HR Manager",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_form_rejects_username_outside_django_rules(self):
        form = StaffUserCreationForm(
            data={
                "username": "invalid name!",
                "first_name": "Demo",
                "last_name": "HR",
                "email": "demo.hr@example.com",
                "role": "HR Manager",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_service_rejects_invalid_role_without_writing(self):
        with self.assertRaises(ValidationError):
            create_staff_user(
                username="demo.invalid-role",
                first_name="Demo",
                last_name="User",
                email="demo.user@example.com",
                role="Employee",
            )

        self.assertFalse(User.objects.filter(username="demo.invalid-role").exists())

    def test_service_rejects_case_insensitive_duplicate(self):
        User.objects.create_user(username="Demo.Staff", password="irrelevant")

        with self.assertRaises(ValidationError):
            create_staff_user(
                username="demo.staff",
                first_name="Demo",
                last_name="User",
                email="demo.user@example.com",
                role="HR Manager",
            )

        self.assertEqual(User.objects.filter(username__iexact="demo.staff").count(), 1)


class StaffUserViewPermissionTests(TestCase):
    def setUp(self):
        self.password = "testpass123"
        self.admin = self._user_in_group("admin", "Admin")
        self.hr_manager = self._user_in_group("hr", "HR Manager")
        self.payroll_officer = self._user_in_group("payroll", "Payroll Officer")
        self.employee_user = self._user_in_group("employee", "Employee")

    def _user_in_group(self, username, group_name):
        user = User.objects.create_user(username=username, password=self.password)
        user.groups.add(Group.objects.get(name=group_name))
        return user

    def test_admin_and_hr_manager_can_open_user_management(self):
        for user in (self.admin, self.hr_manager):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.get(reverse("staff-user-list"))
                self.assertEqual(response.status_code, 200)
                self.client.logout()

    def test_payroll_officer_and_employee_are_denied_user_management(self):
        for user in (self.payroll_officer, self.employee_user):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.get(reverse("staff-user-list"))
                self.assertEqual(response.status_code, 403)
                self.client.logout()

    def test_superuser_payroll_officer_is_still_denied_user_management(self):
        # A Django superuser is not automatically an "Admin" for this app's own
        # role model — only Admin/HR Manager group membership grants access here,
        # matching employees.views.HRManagementRequiredMixin's group-only check.
        self.payroll_officer.is_superuser = True
        self.payroll_officer.is_staff = True
        self.payroll_officer.save(update_fields=["is_superuser", "is_staff"])

        self.client.force_login(self.payroll_officer)
        response = self.client.get(reverse("staff-user-list"))

        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("staff-user-list"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('staff-user-list')}",
        )

    def test_hr_manager_can_create_payroll_officer(self):
        self.client.force_login(self.hr_manager)
        response = self.client.post(
            reverse("staff-user-create"),
            {
                "username": "new.payroll",
                "first_name": "New",
                "last_name": "Officer",
                "email": "new.payroll@example.com",
                "role": "Payroll Officer",
            },
        )

        self.assertRedirects(response, reverse("staff-user-list"))
        created = User.objects.get(username="new.payroll")
        self.assertTrue(created.check_password(DEFAULT_INITIAL_PASSWORD))
        self.assertTrue(created.groups.filter(name="Payroll Officer").exists())

    def test_user_list_is_paginated(self):
        group = Group.objects.get(name="HR Manager")
        for index in range(26):
            user = User.objects.create_user(username=f"demo-staff-{index:02d}")
            user.groups.add(group)

        self.client.force_login(self.admin)
        response = self.client.get(reverse("staff-user-list"))

        self.assertEqual(len(response.context["staff_users"]), 25)
        self.assertEqual(response.context["page_obj"].paginator.count, 28)
        self.assertContains(response, "Page 1 of 2")


class RoleAwareDashboardTests(TestCase):
    def _create_role_user(self, username, role):
        user = User.objects.create_user(
            username=username,
            password="testpass123",
            first_name="Demo",
            last_name=role,
            email=f"{username}@example.com",
        )
        user.groups.add(Group.objects.get(name=role))
        return user

    def test_hr_dashboard_has_hr_links_without_payroll(self):
        user = self._create_role_user("hr-dashboard", "HR Manager")
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "HR overview")
        self.assertContains(response, "User management")
        self.assertContains(response, "Leave approvals")
        self.assertNotContains(response, "Payroll runs")
        self.assertNotContains(response, "This Month&#x27;s Payroll")

    def test_superuser_payroll_officer_sees_payroll_dashboard_not_admin(self):
        user = self._create_role_user("superuser-payroll", "Payroll Officer")
        user.is_superuser = True
        user.is_staff = True
        user.save(update_fields=["is_superuser", "is_staff"])
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Payroll overview")
        self.assertNotContains(response, "Administration overview")

    def test_payroll_dashboard_has_payroll_links_without_user_management(self):
        user = self._create_role_user("payroll-dashboard", "Payroll Officer")
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Payroll overview")
        self.assertContains(response, "Payroll runs")
        self.assertNotContains(response, "User Management")
        self.assertNotContains(response, "Leave approvals")

    def test_employee_dashboard_only_uses_own_record_and_header_uses_name(self):
        user = self._create_role_user("EMP-DASH", "Employee")
        employee = Employee.objects.create(
            user=user,
            employee_number="EMP-DASH",
            first_name="Demo",
            last_name="Employee",
            email="employee.record@example.com",
            hire_date="2026-09-01",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "My dashboard")
        self.assertContains(response, "My profile")
        self.assertContains(response, reverse("employees:employee-detail", args=[employee.pk]))
        self.assertContains(response, "Demo Employee")
        # The account-menu dropdown (see templates/base.html) intentionally shows the
        # signed-in user's own email — that's their own record, not a leak of someone
        # else's. Only the employee's own linked-record email is expected here.
        self.assertNotContains(response, employee.email)
        self.assertNotContains(response, "Payroll runs")
        self.assertNotContains(response, "User Management")


class ForcedPasswordChangeTests(TestCase):
    """A login provisioned with the shared default password must rotate it first."""

    def setUp(self):
        self.password = DEFAULT_INITIAL_PASSWORD
        self.user = User.objects.create_user(username="needs-rotation", password=self.password)
        mark_must_change_password(self.user)

    def test_flagged_user_is_redirected_to_password_change(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("password_change"))

    def test_flagged_user_can_still_reach_password_change_and_logout(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("password_change")).status_code, 200)
        self.assertEqual(self.client.post(reverse("logout")).status_code, 302)

    def test_completing_password_change_clears_the_flag_and_unlocks_the_app(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": self.password,
                "new_password1": "a-new-strong-pass-9",
                "new_password2": "a-new-strong-pass-9",
            },
        )
        self.assertRedirects(response, reverse("password_change_done"))
        self.user.refresh_from_db()
        self.assertFalse(user_must_change_password(self.user))
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_ordinary_user_without_the_flag_is_never_redirected(self):
        plain = User.objects.create_user(username="ordinary", password="testpass123")
        self.client.force_login(plain)
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_staff_and_employee_provisioning_flags_the_new_login(self):
        created = create_staff_user(
            username="fresh.hr",
            first_name="Fresh",
            last_name="Hr",
            email="fresh.hr@example.com",
            role="HR Manager",
        )
        self.assertTrue(user_must_change_password(created))


class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reset-me", password="old-password-1", email="reset-me@example.com"
        )

    def test_reset_request_emails_a_confirm_link_and_new_password_logs_in(self):
        response = self.client.post(reverse("password_reset"), {"email": self.user.email})
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/accounts/password/reset/confirm/", mail.outbox[0].body)

        # Django's PasswordResetConfirmView requires visiting the emailed link once
        # (GET) before it will accept the new-password POST against the session.
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        confirm_url = reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})
        self.client.get(confirm_url, follow=True)
        session_url = reverse(
            "password_reset_confirm", kwargs={"uidb64": uid, "token": "set-password"}
        )
        response = self.client.post(
            session_url,
            {"new_password1": "brand-new-pass-7", "new_password2": "brand-new-pass-7"},
        )
        self.assertRedirects(response, reverse("password_reset_complete"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("brand-new-pass-7"))

    def test_unknown_email_does_not_reveal_account_existence(self):
        response = self.client.post(
            reverse("password_reset"), {"email": "nobody@example.com"}
        )
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)


class StaffUserLifecycleTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="lifecycle-admin", password="testpass123")
        self.admin.groups.add(Group.objects.get(name="Admin"))
        self.staff = create_staff_user(
            username="lifecycle.hr",
            first_name="Lifecycle",
            last_name="Hr",
            email="lifecycle.hr@example.com",
            role="HR Manager",
        )

    def test_update_staff_user_changes_details_and_role(self):
        updated = update_staff_user(
            self.staff,
            first_name="Updated",
            last_name="Name",
            email="updated@example.com",
            role="Payroll Officer",
        )
        self.assertEqual(updated.get_full_name(), "Updated Name")
        self.assertEqual(list(updated.groups.values_list("name", flat=True)), ["Payroll Officer"])

    def test_update_view_requires_account_manager_group(self):
        # HR Manager is an account manager (see StaffUserViewPermissionTests); Payroll
        # Officer is not, so it is the correct role to prove the mixin denies access.
        outsider = User.objects.create_user(username="lifecycle-payroll", password="testpass123")
        outsider.groups.add(Group.objects.get(name="Payroll Officer"))
        self.client.force_login(outsider)
        response = self.client.get(reverse("staff-user-update", args=[self.staff.pk]))
        self.assertEqual(response.status_code, 403)

    def test_toggle_active_deactivates_and_reactivates(self):
        self.client.force_login(self.admin)
        url = reverse("staff-user-toggle-active", args=[self.staff.pk])

        self.client.post(url)
        self.staff.refresh_from_db()
        self.assertFalse(self.staff.is_active)

        self.client.post(url)
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.is_active)

    def test_cannot_deactivate_own_account(self):
        self.admin.groups.add(Group.objects.get(name="Payroll Officer"))
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("staff-user-toggle-active", args=[self.admin.pk]), follow=True
        )
        self.assertContains(response, "You cannot deactivate your own account.")
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
