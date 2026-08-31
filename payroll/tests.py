from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from employees.models import Employee

from .models import Payroll, PayrollItem


class PayrollConstraintTests(TestCase):
    def setUp(self):
        self.officer = User.objects.create_user(username="officer", password="testpass123")
        self.employee = Employee.objects.create(
            employee_number="EMP-001",
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            hire_date=date(2024, 1, 1),
        )

    def test_only_one_payroll_per_month_year(self):
        Payroll.objects.create(
            period_start=date(2024, 6, 1),
            period_end=date(2024, 6, 30),
            month=6,
            year=2024,
            created_by=self.officer,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Payroll.objects.create(
                    period_start=date(2024, 6, 1),
                    period_end=date(2024, 6, 30),
                    month=6,
                    year=2024,
                    created_by=self.officer,
                )

    def test_only_one_payroll_item_per_employee_per_payroll(self):
        payroll = Payroll.objects.create(
            period_start=date(2024, 6, 1),
            period_end=date(2024, 6, 30),
            month=6,
            year=2024,
            created_by=self.officer,
        )
        PayrollItem.objects.create(
            payroll=payroll, employee=self.employee, basic_salary=Decimal("1500.00")
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PayrollItem.objects.create(
                    payroll=payroll, employee=self.employee, basic_salary=Decimal("1500.00")
                )
