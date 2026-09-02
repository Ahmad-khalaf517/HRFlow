from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from employees.models import Employee

from .constants import DEFAULT_INITIAL_PASSWORD
from .forms import StaffUserCreationForm


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
        self.assertNotContains(response, user.email)
        self.assertNotContains(response, "Payroll runs")
        self.assertNotContains(response, "User Management")
