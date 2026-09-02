from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse


class SharedInterfaceTests(TestCase):
    def test_login_errors_are_associated_with_inputs(self):
        response = self.client.post(reverse("login"), {"username": "", "password": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-invalid="true"', count=2)
        self.assertContains(response, 'id="id_username_feedback"')
        self.assertContains(response, 'aria-describedby="id_username_feedback"')

    def test_multiple_roles_do_not_duplicate_attendance_navigation(self):
        user = User.objects.create_user("demo-multirole")
        user.groups.add(*Group.objects.filter(name__in=["Admin", "HR Manager"]))
        self.client.force_login(user)
        response = self.client.get(reverse("home"))
        self.assertContains(response, f'href="{reverse("attendance:attendance_list")}"', count=1)
        self.assertContains(response, 'aria-label="Main navigation"')

    def test_payroll_officer_can_find_read_only_leave_screen(self):
        user = User.objects.create_user("demo-officer")
        user.groups.add(Group.objects.get(name="Payroll Officer"))
        self.client.force_login(user)
        response = self.client.get(reverse("home"))
        self.assertContains(response, f'href="{reverse("attendance:leave_request_list")}"')
        self.assertNotContains(response, f'href="{reverse("attendance:leave_approval_list")}"')

    def test_invalid_staff_form_has_error_summary(self):
        user = User.objects.create_user("demo-admin")
        user.groups.add(Group.objects.get(name="Admin"))
        self.client.force_login(user)
        response = self.client.post(reverse("staff-user-create"), {})
        self.assertContains(response, 'class="form-error-summary')
        self.assertContains(response, 'href="#id_email"')
        self.assertEqual(User.objects.count(), 1)
