from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Contract, Employee


class ContractConstraintTests(TestCase):
    """docs/business-rules.md §4: only one active contract per employee."""

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
