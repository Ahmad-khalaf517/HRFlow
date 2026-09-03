from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse

from attendance.models import Attendance, LeaveRequest, LeaveType
from employees.models import Contract, Employee

from .forms import TaxBracketForm
from .models import Bonus, ManualDeduction, Payroll, TaxBracket
from .services import approve_payroll, calculate_payroll, create_payroll_run, mark_reviewed


class PayrollFlowAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.officer = User.objects.create_user("demo-payroll-audit")
        cls.officer.groups.add(Group.objects.get(name="Payroll Officer"))
        cls.hr = User.objects.create_user("demo-hr-payroll-audit")
        cls.hr.groups.add(Group.objects.get(name="HR Manager"))
        cls.worker = User.objects.create_user("demo-payslip-audit")
        cls.worker.groups.add(Group.objects.get(name="Employee"))
        cls.employee = Employee.objects.create(
            user=cls.worker,
            employee_number="DEMO-E2E",
            first_name="Demo",
            last_name="Flow",
            email="flow@example.test",
            hire_date=date(2026, 1, 1),
        )
        cls.contract = Contract.objects.create(
            employee=cls.employee,
            start_date=date(2026, 1, 1),
            basic_salary=3000,
            allowances_default=150,
            working_hours_per_day=8,
        )

    def test_real_attendance_to_approved_immutable_payslip(self):
        Attendance.objects.create(
            employee=self.employee, date=date(2026, 10, 1), check_in=time(8), check_out=time(18)
        )
        Attendance.objects.create(employee=self.employee, date=date(2026, 10, 2), status="absent")
        leave_type = LeaveType.objects.create(name="Demo Unpaid", is_paid=False)
        leave = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=leave_type,
            start_date=date(2026, 10, 5),
            end_date=date(2026, 10, 6),
        )
        leave.approve(self.hr)
        Bonus.objects.create(employee=self.employee, amount=100, effective_date=date(2026, 10, 1))
        ManualDeduction.objects.create(
            employee=self.employee, amount=25, effective_date=date(2026, 10, 1)
        )
        TaxBracket.objects.create(name="Demo tax", min_amount=0, percentage=10)
        run = create_payroll_run(10, 2026, self.officer)
        calculate_payroll(run, self.officer)
        item = run.items.get()
        self.assertEqual(item.overtime_hours, Decimal("2.00"))
        self.assertEqual(item.absence_days, Decimal("1.00"))
        self.assertEqual(item.unpaid_leave_days, Decimal("2.00"))
        self.assertEqual(item.gross_salary, Decimal("3287.50"))
        self.assertEqual(item.total_deductions, Decimal("653.75"))
        self.assertEqual(item.net_salary, Decimal("2633.75"))
        self.assertEqual(item.calculation_inputs["attendance_source"], "attendance-services-v1")
        mark_reviewed(run, self.officer)
        approve_payroll(run, self.officer)
        Contract.objects.filter(pk=self.contract.pk).update(basic_salary=4000)
        self.client.force_login(self.worker)
        response = self.client.get(reverse("payroll:payslip-detail", args=[item.pk]))
        self.assertContains(response, "2633.75")
        self.assertNotContains(response, "4000")
        with self.assertRaises(ValidationError):
            calculate_payroll(run, self.officer)
        item.refresh_from_db()
        self.assertEqual(item.net_salary, Decimal("2633.75"))

    def test_empty_posts_and_invalid_money_return_bound_errors(self):
        self.client.force_login(self.officer)
        for route in ["bonus-create", "deduction-create", "tax-bracket-create", "run-create"]:
            with self.subTest(route=route):
                response = self.client.post(reverse("payroll:" + route), {})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].is_bound)
                self.assertTrue(response.context["form"].errors)
        for value in ["-0.01", "NaN", "Infinity", "100000000000000000", "1.001"]:
            with self.subTest(value=value):
                response = self.client.post(
                    reverse("payroll:bonus-create"),
                    {"employee": self.employee.pk, "amount": value, "effective_date": "2026-10-01"},
                )
                self.assertIn("amount", response.context["form"].errors)
        self.assertFalse(Bonus.objects.exists())

    def test_negative_fixed_tax_is_rejected(self):
        form = TaxBracketForm(
            {
                "name": "Demo",
                "min_amount": 0,
                "percentage": 10,
                "fixed_amount": "-1",
                "is_active": True,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("fixed_amount", form.errors)

    def test_invalid_filters_are_safe_and_do_not_widen_own_history(self):
        run = create_payroll_run(10, 2026, self.officer)
        calculate_payroll(run, self.officer)
        mark_reviewed(run, self.officer)
        approve_payroll(run, self.officer)
        for user in [self.officer, self.worker]:
            self.client.force_login(user)
            for query in [{"month": "13"}, {"year": "99999999999999"}, {"status": "sent"}]:
                with self.subTest(user=user.username, query=query):
                    response = self.client.get(reverse("payroll:payslip-list"), query)
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.context["form"].errors)
                    self.assertEqual(response.context["page_obj"].paginator.count, 0)

    def test_main_bonus_editing_rule_is_preserved(self):
        self.client.force_login(self.officer)
        bonus = Bonus.objects.create(
            employee=self.employee, amount=100, effective_date=date.today() + timedelta(days=1)
        )
        url = reverse("payroll:bonus-update", args=[bonus.pk])
        response = self.client.post(
            url,
            {
                "employee": self.employee.pk,
                "amount": "125.00",
                "effective_date": bonus.effective_date.isoformat(),
            },
        )
        self.assertEqual(response.status_code, 302)
        bonus.refresh_from_db()
        self.assertEqual(bonus.amount, Decimal("125.00"))
        bonus.effective_date = date.today() - timedelta(days=1)
        bonus.save()
        response = self.client.post(reverse("payroll:bonus-cancel", args=[bonus.pk]), follow=True)
        self.assertContains(response, "can no longer be cancelled")
        bonus.refresh_from_db()
        self.assertEqual(bonus.status, "active")

    def test_service_authorization_and_invalid_periods(self):
        with self.assertRaises(PermissionDenied):
            create_payroll_run(10, 2026, self.worker)
        run = create_payroll_run(10, 2026, self.officer)
        for operation in [calculate_payroll, mark_reviewed]:
            with self.subTest(operation=operation.__name__), self.assertRaises(PermissionDenied):
                operation(run, self.worker)
        for month, year in [(13, 2026), (1, 99999), ("one", 2026)]:
            with self.subTest(month=month, year=year), self.assertRaises(ValidationError):
                create_payroll_run(month, year, self.officer)
        self.assertEqual(Payroll.objects.count(), 1)

    def test_invalid_transition_message_has_no_python_list_formatting(self):
        run = create_payroll_run(10, 2026, self.officer)
        self.client.force_login(self.officer)
        response = self.client.post(reverse("payroll:run-review", args=[run.pk]), follow=True)
        self.assertContains(response, "Only calculated payroll can be moved to Reviewed.")
        self.assertNotContains(response, "[&#x27;Only calculated")
