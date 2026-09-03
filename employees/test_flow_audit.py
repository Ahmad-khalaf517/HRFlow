from datetime import date

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from .forms import EmployeeForm, PositionForm
from .models import Contract, Department, Employee, Position


class EmployeeFlowAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = User.objects.create_user("demo-hr")
        cls.manager.groups.add(Group.objects.get(name="HR Manager"))
        cls.department = Department.objects.create(name="Demo Engineering")
        cls.position = Position.objects.create(department=cls.department, title="Demo Engineer")
        cls.employee = Employee.objects.create(
            employee_number="DEMO-001", first_name="Demo", last_name="Employee",
            email="demo@example.test", hire_date=date(2026, 1, 1),
        )

    def employee_data(self, **changes):
        return {
            "employee_number": "DEMO-002", "first_name": "Demo", "last_name": "New",
            "email": "new@example.test", "hire_date": "2026-01-01",
            "employment_status": "active", **changes,
        }

    def test_negative_salary_ranges_are_rejected(self):
        for field in ("min_salary", "max_salary"):
            with self.subTest(field=field):
                form = PositionForm({"department": self.department.pk, "title": "New role",
                                     field: "-0.01"})
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_position_requires_matching_department(self):
        form = EmployeeForm(self.employee_data(position=self.position.pk))
        self.assertFalse(form.is_valid())
        self.assertIn("position", form.errors)

    def test_email_uniqueness_is_case_insensitive(self):
        form = EmployeeForm(self.employee_data(email="DEMO@example.test"))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_employee_number_must_be_a_valid_login_name(self):
        form = EmployeeForm(self.employee_data(employee_number="invalid employee"))
        self.assertFalse(form.is_valid())
        self.assertIn("employee_number", form.errors)

    def test_employment_status_and_active_flag_remain_consistent(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse("employees:employee-create"),
                                    self.employee_data(employment_status="inactive"))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Employee.objects.get(employee_number="DEMO-002").is_active)

    def test_invalid_directory_filters_show_errors_without_crashing(self):
        self.client.force_login(self.manager)
        for filters in ({"department": "²"}, {"department": "9" * 100},
                        {"status": "unknown"}, {"contract_type": "unknown"}):
            with self.subTest(filters=filters):
                response = self.client.get(reverse("employees:employee-list"), filters)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Please correct the following errors.")

    def test_active_contract_filter_and_column_match(self):
        Contract.objects.create(employee=self.employee, start_date=date(2026, 1, 1),
                                basic_salary=1000, contract_type="part_time")
        self.client.force_login(self.manager)
        url = reverse("employees:employee-list")
        self.assertContains(self.client.get(url, {"contract_type": "part_time"}), "DEMO-001")
        self.assertNotContains(self.client.get(url, {"contract_type": "full_time"}), "DEMO-001")

    def test_staff_flag_does_not_grant_directory_access(self):
        user = User.objects.create_user("demo-staff-only", is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("employees:employee-list")).status_code, 403)

    def test_empty_employee_submission_renders_field_errors(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse("employees:employee-create"), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-invalid="true"')
        self.assertEqual(Employee.objects.count(), 1)

    def test_pagination_preserves_search(self):
        for i in range(12):
            Employee.objects.create(employee_number=f"EXTRA-{i}", first_name="Demo",
                                    last_name=f"Extra {i}", email=f"extra{i}@example.test",
                                    hire_date=date(2026, 1, 1))
        self.client.force_login(self.manager)
        response = self.client.get(reverse("employees:employee-list"), {"search": "Extra"})
        self.assertContains(response, 'href="?search=Extra&amp;page=2"')
