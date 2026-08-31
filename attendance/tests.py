from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase

from employees.models import Employee

from .models import Attendance


class AttendanceConstraintTests(TestCase):
    """docs/testing-strategy.md priority #2: one attendance record per employee/date."""

    def setUp(self):
        self.employee = Employee.objects.create(
            employee_number="EMP-001",
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            hire_date=date(2024, 1, 1),
        )

    def test_one_attendance_record_per_employee_per_date(self):
        Attendance.objects.create(employee=self.employee, date=date(2024, 6, 3), status="present")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Attendance.objects.create(
                    employee=self.employee, date=date(2024, 6, 3), status="present"
                )

    def test_same_employee_different_date_is_allowed(self):
        Attendance.objects.create(employee=self.employee, date=date(2024, 6, 3), status="present")
        Attendance.objects.create(employee=self.employee, date=date(2024, 6, 4), status="present")
        self.assertEqual(self.employee.attendance_records.count(), 2)
