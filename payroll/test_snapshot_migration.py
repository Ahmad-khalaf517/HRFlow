from datetime import date
from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class SnapshotMigrationTests(TransactionTestCase):
    def test_legacy_item_keeps_amounts_without_invented_inputs(self):
        before = [("payroll", "0002_alter_bonus_bonus_amount_gte_0_and_more")]
        after = [("payroll", "0003_payslip_snapshot_inputs")]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        try:
            apps = executor.loader.project_state(before).apps
            user = apps.get_model("auth", "User").objects.create(username="migration_demo")
            employee = apps.get_model("employees", "Employee").objects.create(
                employee_number="EMP-LEGACY", first_name="Demo", last_name="Legacy",
                email="legacy@example.test", hire_date=date(2026, 1, 1),
            )
            run = apps.get_model("payroll", "Payroll").objects.create(
                month=9, year=2026, period_start=date(2026, 9, 1),
                period_end=date(2026, 9, 30), created_by=user, status="approved",
            )
            item = apps.get_model("payroll", "PayrollItem").objects.create(
                payroll=run, employee=employee, basic_salary=3000, net_salary=Decimal("2751.87"),
            )
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            updated = executor.loader.project_state(after).apps.get_model(
                "payroll", "PayrollItem"
            ).objects.get(pk=item.pk)
            self.assertEqual(updated.basic_salary, Decimal("3000.00"))
            self.assertEqual(updated.net_salary, Decimal("2751.87"))
            self.assertEqual(updated.calculation_inputs, {})
            self.assertEqual(updated.calculation_version, "")
            self.assertEqual(updated.employee_name_snapshot, "")
            self.assertEqual(updated.currency_code, "")
            self.assertIsNone(updated.contract_id)
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
