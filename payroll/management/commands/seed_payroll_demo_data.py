"""Synthetic demo data for local payroll development.

employees/ has no CRUD UI yet (Person 1's work), so this command creates a
handful of synthetic Employee/Contract rows through the existing models —
same effect as creating them by hand in Django Admin. Idempotent
(get_or_create), safe to re-run. Delete/ignore once real employee data
exists; no payroll code depends on this command directly.

docs/security-and-data-policy.md: synthetic values only, never real data.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from employees.models import Contract, Department, Employee, Position
from payroll.models import TaxBracket


class Command(BaseCommand):
    help = "Seed synthetic employees/contracts and tax brackets for local payroll dev/demo."

    @transaction.atomic
    def handle(self, *args, **options):
        engineering, _ = Department.objects.get_or_create(
            name="Engineering", defaults={"description": "Product engineering."}
        )
        operations, _ = Department.objects.get_or_create(
            name="Operations", defaults={"description": "Operations and administration."}
        )

        engineer_role, _ = Position.objects.get_or_create(
            department=engineering, title="Software Engineer"
        )
        clerk_role, _ = Position.objects.get_or_create(
            department=operations, title="Operations Clerk"
        )

        employees = [
            {
                "employee_number": "EMP-1001",
                "first_name": "Grace",
                "last_name": "Hopper",
                "email": "grace.hopper@example.com",
                "hire_date": "2023-02-01",
                "department": engineering,
                "position": engineer_role,
                "contract": {
                    "contract_type": "full_time",
                    "start_date": "2023-02-01",
                    "basic_salary": Decimal("3000.00"),
                    "allowances_default": Decimal("150.00"),
                },
            },
            {
                "employee_number": "EMP-1002",
                "first_name": "Alan",
                "last_name": "Turing",
                "email": "alan.turing@example.com",
                "hire_date": "2022-06-15",
                "department": engineering,
                "position": engineer_role,
                "contract": {
                    "contract_type": "full_time",
                    "start_date": "2022-06-15",
                    "basic_salary": Decimal("4500.00"),
                    "allowances_default": Decimal("200.00"),
                },
            },
            {
                "employee_number": "EMP-1003",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada.lovelace@example.com",
                "hire_date": "2024-01-10",
                "department": operations,
                "position": clerk_role,
                "contract": {
                    "contract_type": "part_time",
                    "start_date": "2024-01-10",
                    "basic_salary": Decimal("1500.00"),
                    "working_hours_per_day": Decimal("4.00"),
                    "working_days_per_week": 3,
                },
            },
            {
                "employee_number": "EMP-1004",
                "first_name": "Margaret",
                "last_name": "Hamilton",
                "email": "margaret.hamilton@example.com",
                "hire_date": "2026-07-01",
                "department": operations,
                "position": clerk_role,
                "contract": {
                    "contract_type": "probation",
                    "start_date": "2026-07-01",
                    "basic_salary": Decimal("2200.00"),
                    "probation_end_date": "2026-10-01",
                },
            },
            {
                # Inactive employee: demonstrates payroll calculation correctly
                # excluding anyone without an active employee/contract pair.
                "employee_number": "EMP-1005",
                "first_name": "Katherine",
                "last_name": "Johnson",
                "email": "katherine.johnson@example.com",
                "hire_date": "2021-03-01",
                "department": engineering,
                "position": engineer_role,
                "is_active": False,
                "employment_status": "inactive",
                "contract": {
                    "contract_type": "full_time",
                    "start_date": "2021-03-01",
                    "end_date": "2026-06-30",
                    "basic_salary": Decimal("4000.00"),
                    "status": "inactive",
                },
            },
        ]

        for spec in employees:
            contract_spec = spec.pop("contract")
            employee, _ = Employee.objects.get_or_create(
                employee_number=spec.pop("employee_number"), defaults=spec
            )
            Contract.objects.get_or_create(
                employee=employee,
                status=contract_spec.pop("status", "active"),
                defaults=contract_spec,
            )

        tax_brackets = [
            {
                "name": "No tax",
                "min_amount": Decimal("0.00"),
                "max_amount": Decimal("999.99"),
                "percentage": Decimal("0.00"),
            },
            {
                "name": "Standard",
                "min_amount": Decimal("1000.00"),
                "max_amount": Decimal("4999.99"),
                "percentage": Decimal("10.00"),
            },
            {
                "name": "High",
                "min_amount": Decimal("5000.00"),
                "max_amount": None,
                "percentage": Decimal("15.00"),
                "fixed_amount": Decimal("50.00"),
            },
        ]
        for spec in tax_brackets:
            TaxBracket.objects.get_or_create(name=spec.pop("name"), defaults=spec)

        self.stdout.write(self.style.SUCCESS("Seeded demo employees, contracts, and tax brackets."))
