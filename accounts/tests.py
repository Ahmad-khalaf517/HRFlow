from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse


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
