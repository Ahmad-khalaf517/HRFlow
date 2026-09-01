from datetime import date
from decimal import Decimal


from django.contrib.auth.models import Group, User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from employees.forms import (
    ContractForm,
    DepartmentForm,
    EmployeeForm,
    PositionForm,
)

from employees.models import (
    Contract,
    Department,
    Employee,
    Position,
)
class ContractConstraintTests(TestCase):
    """docs/testing-strategy.md priority #1: only one active contract per employee."""

    def setUp(self):
        self.employee = Employee.objects.create(
            employee_number="EMP-001",
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            hire_date=date(2024, 1, 1),
        )

    def test_only_one_active_contract_per_employee(self):
        Contract.objects.create(
            employee=self.employee,
            start_date=date(2024, 1, 1),
            basic_salary=Decimal("1500.00"),
            status="active",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Contract.objects.create(
                    employee=self.employee,
                    start_date=date(2024, 6, 1),
                    basic_salary=Decimal("1600.00"),
                    status="active",
                )

    def test_inactive_contract_history_is_allowed_alongside_an_active_one(self):
        Contract.objects.create(
            employee=self.employee,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            basic_salary=Decimal("1400.00"),
            status="inactive",
        )
        Contract.objects.create(
            employee=self.employee,
            start_date=date(2024, 1, 1),
            basic_salary=Decimal("1500.00"),
            status="active",
        )
        self.assertEqual(self.employee.contracts.count(), 2)

class DepartmentFormTests(TestCase):

    def test_duplicate_department_name_is_a_form_error(self):
        Department.objects.create(
            name="Human Resources"
        )

        form = DepartmentForm(
            data={
                "name": "Human Resources",
                "description": "Duplicate department",
                "manager": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
        self.assertEqual(
            form.errors["name"][0],
            "A department with this name already exists.",
        )

    def test_unique_department_name_is_valid(self):
        form = DepartmentForm(
            data={
                "name": "Information Technology",
                "description": "IT Department",
                "manager": "",
            }
        )

        self.assertTrue(form.is_valid())

class PositionFormTests(TestCase):

    def setUp(self):
        self.it_department = Department.objects.create(
            name="Information Technology"
        )

        self.hr_department = Department.objects.create(
            name="Human Resources"
        )

    def test_duplicate_position_title_in_same_department_is_invalid(self):
        Position.objects.create(
            department=self.it_department,
            title="Software Engineer",
        )

        form = PositionForm(
            data={
                "department": self.it_department.id,
                "title": "Software Engineer",
                "code": "",
                "description": "",
                "min_salary": "",
                "max_salary": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_same_position_title_in_different_department_is_valid(self):
        Position.objects.create(
            department=self.it_department,
            title="Software Engineer",
        )

        form = PositionForm(
            data={
                "department": self.hr_department.id,
                "title": "Software Engineer",
                "code": "",
                "description": "",
                "min_salary": "",
                "max_salary": "",
            }
        )

        self.assertTrue(form.is_valid())

    def test_max_salary_cannot_be_less_than_min_salary(self):
        form = PositionForm(
            data={
                "department": self.it_department.id,
                "title": "Senior Developer",
                "code": "",
                "description": "",
                "min_salary": "5000.00",
                "max_salary": "3000.00",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("max_salary", form.errors)
        self.assertEqual(
            form.errors["max_salary"][0],
            "Maximum salary must be greater than or equal to minimum salary.",
        )

class EmployeeFormTests(TestCase):

    def setUp(self):
        self.it_department = Department.objects.create(
            name="Information Technology"
        )

        self.hr_department = Department.objects.create(
            name="Human Resources"
        )

        self.developer_position = Position.objects.create(
            department=self.it_department,
            title="Software Developer",
        )

        self.hr_position = Position.objects.create(
            department=self.hr_department,
            title="HR Specialist",
        )

    def get_valid_employee_data(self):
        return {
            "employee_number": "EMP-001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "",
            "date_of_birth": "",
            "address": "",
            "hire_date": "2026-09-01",
            "department": self.it_department.id,
            "position": self.developer_position.id,
            "employment_status": "active",
            "bank_name": "",
            "bank_account_number": "",
        }

    def test_duplicate_employee_number_is_a_form_error(self):
        Employee.objects.create(
            employee_number="EMP-001",
            first_name="Existing",
            last_name="Employee",
            email="existing@example.com",
            hire_date="2026-01-01",
            department=self.it_department,
            position=self.developer_position,
        )

        form = EmployeeForm(
            data=self.get_valid_employee_data()
        )

        self.assertFalse(form.is_valid())
        self.assertIn("employee_number", form.errors)

        self.assertEqual(
            form.errors["employee_number"][0],
            "An employee with this employee number already exists.",
        )

    def test_position_must_belong_to_selected_department(self):
        data = self.get_valid_employee_data()

        data["position"] = self.hr_position.id

        form = EmployeeForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("position", form.errors)

        self.assertEqual(
            form.errors["position"][0],
            "The selected position does not belong to the selected department.",
        )

    def test_valid_employee_form_is_valid(self):
        form = EmployeeForm(
            data=self.get_valid_employee_data()
        )

        self.assertTrue(form.is_valid())

class ContractFormTests(TestCase):

    def setUp(self):
        self.department = Department.objects.create(
            name="Contract Test Department"
        )

        self.position = Position.objects.create(
            department=self.department,
            title="Contract Test Position",
        )

        self.employee = Employee.objects.create(
            employee_number="CONTRACT-EMP-001",
            first_name="John",
            last_name="Contract",
            email="contract.employee@example.com",
            hire_date=date(2026, 1, 1),
            department=self.department,
            position=self.position,
        )

    def get_valid_contract_data(self):
        return {
            "employee": self.employee.id,
            "contract_type": "full_time",
            "start_date": "2026-01-01",
            "end_date": "",
            "basic_salary": "2000.00",
            "allowances_default": "0.00",
            "working_hours_per_day": "8.00",
            "working_days_per_week": "5",
            "probation_end_date": "",
            "status": "active",
        }

    def test_end_date_before_start_date_is_rejected(self):
        data = self.get_valid_contract_data()

        data["start_date"] = "2026-09-10"
        data["end_date"] = "2026-09-01"

        form = ContractForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("end_date", form.errors)

        self.assertEqual(
            form.errors["end_date"][0],
            "End date cannot be before the start date.",
        )

    def test_second_active_contract_is_rejected(self):
        Contract.objects.create(
            employee=self.employee,
            contract_type="full_time",
            start_date=date(2026, 1, 1),
            basic_salary=Decimal("2000.00"),
            allowances_default=Decimal("0.00"),
            working_hours_per_day=Decimal("8.00"),
            working_days_per_week=5,
            status="active",
        )

        form = ContractForm(
            data=self.get_valid_contract_data()
        )

        self.assertFalse(form.is_valid())
        self.assertIn("employee", form.errors)

        self.assertEqual(
            form.errors["employee"][0],
            "This employee already has an active contract.",
        )

    def test_valid_contract_form_is_valid(self):
        form = ContractForm(
            data=self.get_valid_contract_data()
        )

        self.assertTrue(form.is_valid())




class DepartmentURLTests(TestCase):

    def test_department_list_url(self):
        url = reverse("employees:department-list")

        self.assertEqual(
            url,
            "/employees/departments/",
        )

    def test_department_create_url(self):
        url = reverse("employees:department-create")

        self.assertEqual(
            url,
            "/employees/departments/create/",
        )

    def test_department_detail_url(self):
        url = reverse(
            "employees:department-detail",
            kwargs={"pk": 1},
        )

        self.assertEqual(
            url,
            "/employees/departments/1/",
        )


class DepartmentViewPermissionTests(TestCase):

    def setUp(self):
        self.admin_group, _ = Group.objects.get_or_create(
            name="Admin"
        )

        self.hr_group, _ = Group.objects.get_or_create(
            name="HR Manager"
        )

        self.employee_group, _ = Group.objects.get_or_create(
            name="Employee"
        )

        self.admin_user = User.objects.create_user(
            username="admin_test",
            password="password123",
        )

        self.admin_user.groups.add(
            self.admin_group
        )

        self.hr_user = User.objects.create_user(
            username="hr_test",
            password="password123",
        )

        self.hr_user.groups.add(
            self.hr_group
        )

        self.employee_user = User.objects.create_user(
            username="employee_test",
            password="password123",
        )

        self.employee_user.groups.add(
            self.employee_group
        )

        self.department = Department.objects.create(
            name="Test Department"
        )

    def test_employee_cannot_access_department_create(self):
        self.client.login(
            username="employee_test",
            password="password123",
        )

        response = self.client.get(
            reverse("employees:department-create")
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_hr_manager_can_access_department_create(self):
        self.client.login(
            username="hr_test",
            password="password123",
        )

        response = self.client.get(
            reverse("employees:department-create")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_employee_can_view_department_list(self):
        self.client.login(
            username="employee_test",
            password="password123",
        )

        response = self.client.get(
            reverse("employees:department-list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_department_deactivate_is_post_only(self):
        self.client.login(
            username="hr_test",
            password="password123",
        )

        url = reverse(
            "employees:department-deactivate",
            kwargs={
                "pk": self.department.pk
            },
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            405,
        )

        self.department.refresh_from_db()

        self.assertTrue(
            self.department.is_active
        )

    def test_hr_manager_can_deactivate_department(self):
        self.client.login(
            username="hr_test",
            password="password123",
        )

        response = self.client.post(
            reverse(
                "employees:department-deactivate",
                kwargs={
                    "pk": self.department.pk
                },
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.department.refresh_from_db()

        self.assertFalse(
            self.department.is_active
        )