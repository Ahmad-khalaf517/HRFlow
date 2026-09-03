"""HRF-007 prerequisites for historically stable payslips; synthetic data only."""

from copy import deepcopy
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import RequestFactory, TestCase

from employees.models import Contract, Employee

from .admin import PayrollAdmin, PayrollItemAdmin
from .models import ManualDeduction, Payroll, PayrollItem, TaxBracket
from .services import approve_payroll, calculate_payroll, create_payroll_run, mark_reviewed


class SnapshotTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.officer = User.objects.create_user(username="snapshot_officer")
        cls.officer.groups.add(Group.objects.get(name="Payroll Officer"))
        cls.employee = Employee.objects.create(
            employee_number="EMP-SNAPSHOT", first_name="Demo", last_name="Employee",
            email="snapshot@example.test", hire_date=date(2026, 1, 1),
        )
        cls.contract = Contract.objects.create(
            employee=cls.employee, start_date=date(2026, 1, 1),
            basic_salary=Decimal("3000.00"), allowances_default=Decimal("150.00"),
            working_hours_per_day=Decimal("8.00"),
        )
        cls.tax = TaxBracket.objects.create(
            name="Demo tax", min_amount=0, percentage=Decimal("10.00"),
        )

    def setUp(self):
        self.run = create_payroll_run(9, 2026, self.officer)
        for name, value in (
            ("get_employee_overtime_hours", "1"), ("get_absence_days", "1"),
            ("get_unpaid_leave_days", "0"),
        ):
            patcher = patch(f"payroll.services.{name}", return_value=Decimal(value))
            patcher.start()
            self.addCleanup(patcher.stop)

    def calculate(self):
        calculate_payroll(self.run, self.officer)
        return self.run.items.get()

    def approve(self):
        item = self.calculate()
        mark_reviewed(self.run, self.officer)
        approve_payroll(self.run, self.officer)
        return item

    def test_snapshot_preserves_inputs_and_documented_amounts(self):
        item = self.calculate()
        self.assertEqual(item.employee_name_snapshot, "Demo Employee")
        self.assertEqual(item.employee_number_snapshot, "EMP-SNAPSHOT")
        self.assertEqual(item.currency_code, "USD")
        self.assertEqual(item.calculation_version, "mvp-2")
        self.assertEqual(item.contract_id, self.contract.pk)
        self.assertEqual(item.calculation_inputs["contract"]["working_hours_per_day"], "8.00")
        self.assertEqual(Decimal(item.calculation_inputs["hourly_rate"]), Decimal("12.5"))
        self.assertEqual(item.calculation_inputs["tax"]["percentage"], "10.00")
        self.assertEqual(item.gross_salary, Decimal("3168.75"))
        self.assertEqual(item.total_deductions, Decimal("416.88"))
        self.assertEqual(item.net_salary, Decimal("2751.87"))

    def test_changes_to_live_sources_do_not_change_approved_snapshot(self):
        item = self.approve()
        original = deepcopy(item.calculation_inputs)
        Contract.objects.filter(pk=self.contract.pk).update(basic_salary=9000)
        Employee.objects.filter(pk=self.employee.pk).update(first_name="Changed")
        TaxBracket.objects.filter(pk=self.tax.pk).update(percentage=25)
        item.refresh_from_db()
        self.assertEqual(item.calculation_inputs, original)
        self.assertEqual(item.employee_name_snapshot, "Demo Employee")
        self.assertEqual(item.net_salary, Decimal("2751.87"))

    def test_referenced_contract_cannot_be_deleted(self):
        self.calculate()
        with self.assertRaises(ProtectedError):
            self.contract.delete()

    def test_negative_net_rolls_back_existing_snapshot_and_status(self):
        item = self.calculate()
        ManualDeduction.objects.create(
            employee=self.employee, amount=4000, effective_date=date(2026, 9, 1),
        )
        with self.assertRaisesMessage(ValidationError, "Deductions cannot exceed"):
            calculate_payroll(self.run, self.officer)
        item.refresh_from_db()
        self.run.refresh_from_db()
        self.assertEqual(item.net_salary, Decimal("2751.87"))
        self.assertEqual(self.run.total_net, item.net_salary)
        self.assertEqual(self.run.status, "calculated")

    def test_invalid_contract_inputs_rejected(self):
        for changes in ({"allowances_default": -1}, {"working_hours_per_day": 0}):
            with self.subTest(changes=changes):
                Contract.objects.filter(pk=self.contract.pk).update(**changes)
                with self.assertRaises(ValidationError):
                    self.calculate()
                self.assertFalse(self.run.items.exists())
                Contract.objects.filter(pk=self.contract.pk).update(
                    allowances_default=150, working_hours_per_day=8,
                )

    def test_database_rejects_negative_item_even_through_bulk_update(self):
        item = self.calculate()
        with self.assertRaises(IntegrityError), transaction.atomic():
            PayrollItem.objects.filter(pk=item.pk).update(net_salary=-1)

    def test_approved_item_cannot_be_saved_deleted_or_moved(self):
        item = self.approve()
        with self.assertRaises(ValidationError):
            item.delete()
        item.net_salary = Decimal("1.00")
        with self.assertRaises(ValidationError):
            item.save()
        item.payroll = create_payroll_run(10, 2026, self.officer)
        with self.assertRaises(ValidationError):
            item.save()

    def test_cannot_add_items_to_approved_run(self):
        self.approve()
        with self.assertRaises(ValidationError):
            PayrollItem.objects.create(payroll=self.run, employee=self.employee, basic_salary=1)

    def test_stale_calculation_and_review_cannot_overwrite_approval(self):
        self.calculate()
        stale = Payroll.objects.get(pk=self.run.pk)
        mark_reviewed(self.run, self.officer)
        approve_payroll(self.run, self.officer)
        for action in (calculate_payroll, mark_reviewed, approve_payroll):
            with self.subTest(action=action.__name__), self.assertRaises(ValidationError):
                action(stale, self.officer)
        self.run.refresh_from_db()
        self.assertEqual(self.run.status, "approved")

    def test_approved_run_fields_and_status_cannot_be_rewritten(self):
        self.approve()
        for field, value in (("total_net", 0), ("currency_code", "EUR"), ("status", "draft")):
            run = Payroll.objects.get(pk=self.run.pk)
            setattr(run, field, value)
            with self.subTest(field=field), self.assertRaises(ValidationError):
                run.save()
        with self.assertRaises(ValidationError):
            self.run.delete()

    def test_recalculation_removes_no_longer_eligible_employee(self):
        self.calculate()
        Employee.objects.filter(pk=self.employee.pk).update(is_active=False)
        calculate_payroll(self.run, self.officer)
        self.assertFalse(self.run.items.exists())
        self.assertEqual(self.run.total_net, Decimal("0.00"))

    def test_admin_cannot_bypass_workflow_even_as_superuser(self):
        item = self.approve()
        request = RequestFactory().get("/admin/")
        request.user = User(is_superuser=True, is_staff=True, is_active=True)
        for model, admin_type, obj in (
            (Payroll, PayrollAdmin, self.run), (PayrollItem, PayrollItemAdmin, item),
        ):
            admin = admin_type(model, AdminSite())
            with self.subTest(model=model.__name__):
                self.assertFalse(admin.has_add_permission(request))
                self.assertFalse(admin.has_change_permission(request, obj))
                self.assertFalse(admin.has_delete_permission(request, obj))
                self.assertTrue(admin.has_view_permission(request, obj))
