from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase

from employees.models import Contract, Employee

from .models import Bonus, ManualDeduction, Payroll, PayrollItem, TaxBracket
from .services import (
    approve_payroll,
    calculate_payroll,
    create_payroll_run,
    get_active_adjustments_for_period,
    get_matching_tax_bracket,
    mark_reviewed,
    user_in_groups,
)


def patch_attendance_facts(overtime=Decimal("0"), absence=Decimal("0"), unpaid_leave=Decimal("0")):
    """Patch the three mocked attendance-fact functions payroll.services imports.

    Each fact defaults to 0 so a test only needs to pass the ones it cares about.
    Returns a 3-tuple of unstarted patchers to use as `with p1, p2, p3:`.
    """
    return (
        patch("payroll.services.get_employee_overtime_hours", return_value=overtime),
        patch("payroll.services.get_absence_days", return_value=absence),
        patch("payroll.services.get_unpaid_leave_days", return_value=unpaid_leave),
    )


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


class PayrollCalculationTests(TestCase):
    """docs/business-rules.md §6 formula, hand-verified against HRF-25's brief example."""

    def setUp(self):
        self.officer = User.objects.create_user(username="calc_officer", password="testpass123")
        self.employee = Employee.objects.create(
            employee_number="EMP-CALC-1",
            first_name="Grace",
            last_name="Hopper",
            email="grace.calc@example.com",
            hire_date=date(2023, 2, 1),
        )
        Contract.objects.create(
            employee=self.employee,
            basic_salary=Decimal("3000.00"),
            allowances_default=Decimal("150.00"),
            working_hours_per_day=Decimal("8.00"),
            start_date=date(2023, 2, 1),
        )
        TaxBracket.objects.create(
            name="Standard",
            min_amount=Decimal("1000.00"),
            max_amount=Decimal("4999.99"),
            percentage=Decimal("10.00"),
        )
        self.payroll = create_payroll_run(9, 2026, self.officer)

    def test_formula_matches_documented_example(self):
        p1, p2, p3 = patch_attendance_facts(overtime=Decimal("1"), absence=Decimal("1"))
        with p1, p2, p3:
            calculate_payroll(self.payroll, self.officer)

        item = PayrollItem.objects.get(payroll=self.payroll, employee=self.employee)
        # daily_rate = 3000/30 = 100; hourly = 100/8 = 12.5; overtime = 1 * 12.5 * 1.5 = 18.75
        self.assertEqual(item.overtime_amount, Decimal("18.75"))
        self.assertEqual(item.absence_deduction, Decimal("100.00"))
        self.assertEqual(item.unpaid_leave_deduction, Decimal("0.00"))
        self.assertEqual(item.gross_salary, Decimal("3168.75"))
        # tax = 0 + 3168.75 * 10% = 316.875 -> ROUND_HALF_UP -> 316.88
        self.assertEqual(item.tax_amount, Decimal("316.88"))
        self.assertEqual(item.total_deductions, Decimal("416.88"))
        self.assertEqual(item.net_salary, Decimal("2751.87"))

        self.payroll.refresh_from_db()
        self.assertEqual(self.payroll.status, "calculated")
        self.assertEqual(self.payroll.total_gross, Decimal("3168.75"))
        self.assertEqual(self.payroll.total_net, Decimal("2751.87"))

    def test_bonus_and_manual_deduction_included(self):
        Bonus.objects.create(
            employee=self.employee,
            amount=Decimal("200.00"),
            effective_date=self.payroll.period_start,
            status="active",
        )
        ManualDeduction.objects.create(
            employee=self.employee,
            amount=Decimal("50.00"),
            effective_date=self.payroll.period_start,
            status="active",
        )
        p1, p2, p3 = patch_attendance_facts()
        with p1, p2, p3:
            calculate_payroll(self.payroll, self.officer)

        item = PayrollItem.objects.get(payroll=self.payroll, employee=self.employee)
        self.assertEqual(item.bonus_amount, Decimal("200.00"))
        self.assertEqual(item.manual_deduction_amount, Decimal("50.00"))
        # gross = 3000 + 150 + 0 + 200 = 3350.00; tax = 10% * 3350 = 335.00
        self.assertEqual(item.gross_salary, Decimal("3350.00"))
        self.assertEqual(item.tax_amount, Decimal("335.00"))
        # total_deductions = 0 + 0 + 50 + 335 = 385.00; net = 3350 - 385 = 2965.00
        self.assertEqual(item.net_salary, Decimal("2965.00"))

    def test_cancelled_bonus_excluded(self):
        Bonus.objects.create(
            employee=self.employee,
            amount=Decimal("999.00"),
            effective_date=self.payroll.period_start,
            status="cancelled",
        )
        p1, p2, p3 = patch_attendance_facts()
        with p1, p2, p3:
            calculate_payroll(self.payroll, self.officer)

        item = PayrollItem.objects.get(payroll=self.payroll, employee=self.employee)
        self.assertEqual(item.bonus_amount, Decimal("0.00"))

    def test_inactive_employee_excluded(self):
        inactive = Employee.objects.create(
            employee_number="EMP-CALC-2",
            first_name="Katherine",
            last_name="Johnson",
            email="katherine.calc@example.com",
            hire_date=date(2021, 3, 1),
            is_active=False,
            employment_status="inactive",
        )
        Contract.objects.create(
            employee=inactive,
            basic_salary=Decimal("4000.00"),
            start_date=date(2021, 3, 1),
            end_date=date(2026, 6, 30),
            status="inactive",
        )
        p1, p2, p3 = patch_attendance_facts()
        with p1, p2, p3:
            calculate_payroll(self.payroll, self.officer)

        self.assertFalse(PayrollItem.objects.filter(employee=inactive).exists())
        # Confirm the active employee was still processed alongside the excluded one.
        self.assertTrue(PayrollItem.objects.filter(employee=self.employee).exists())

    def test_employee_without_active_contract_excluded(self):
        no_contract = Employee.objects.create(
            employee_number="EMP-CALC-3",
            first_name="No",
            last_name="Contract",
            email="nocontract.calc@example.com",
            hire_date=date(2024, 1, 1),
        )
        p1, p2, p3 = patch_attendance_facts()
        with p1, p2, p3:
            calculate_payroll(self.payroll, self.officer)

        self.assertFalse(PayrollItem.objects.filter(employee=no_contract).exists())

    def test_recalculation_updates_existing_item_not_duplicate(self):
        p1, p2, p3 = patch_attendance_facts()
        with p1, p2, p3:
            calculate_payroll(self.payroll, self.officer)
        Bonus.objects.create(
            employee=self.employee,
            amount=Decimal("500.00"),
            effective_date=self.payroll.period_start,
            status="active",
        )
        p1, p2, p3 = patch_attendance_facts()
        with p1, p2, p3:
            calculate_payroll(self.payroll, self.officer)

        self.assertEqual(
            PayrollItem.objects.filter(payroll=self.payroll, employee=self.employee).count(), 1
        )
        item = PayrollItem.objects.get(payroll=self.payroll, employee=self.employee)
        self.assertEqual(item.bonus_amount, Decimal("500.00"))


class PayrollStatusTransitionTests(TestCase):
    """business-rules.md §7: Draft -> Calculated -> Reviewed -> Approved, explicit services only."""

    def setUp(self):
        self.officer = User.objects.create_user(username="trans_officer", password="testpass123")
        Group.objects.get_or_create(name="Payroll Officer")[0].user_set.add(self.officer)
        self.employee_user = User.objects.create_user(username="trans_emp", password="testpass123")
        Group.objects.get_or_create(name="Employee")[0].user_set.add(self.employee_user)
        self.payroll = create_payroll_run(10, 2026, self.officer)

    def test_create_payroll_run_derives_period_and_starts_draft(self):
        self.assertEqual(self.payroll.period_start, date(2026, 10, 1))
        self.assertEqual(self.payroll.period_end, date(2026, 10, 31))
        self.assertEqual(self.payroll.status, "draft")

    def test_create_payroll_run_rejects_duplicate_month_year(self):
        with self.assertRaises(ValidationError):
            create_payroll_run(10, 2026, self.officer)

    def test_mark_reviewed_requires_calculated_status(self):
        with self.assertRaises(ValidationError):
            mark_reviewed(self.payroll, self.officer)  # still draft

    def test_approve_requires_reviewed_status(self):
        with self.assertRaises(ValidationError):
            approve_payroll(self.payroll, self.officer)  # still draft

    def test_calculate_rejects_approved_or_paid_payroll(self):
        self.payroll.status = "approved"
        self.payroll.save(update_fields=["status"])
        with self.assertRaises(ValidationError):
            calculate_payroll(self.payroll, self.officer)

    def test_approve_rejects_actor_outside_manager_groups(self):
        self.payroll.status = "reviewed"
        self.payroll.save(update_fields=["status"])
        with self.assertRaises(PermissionDenied):
            approve_payroll(self.payroll, self.employee_user)

    def test_full_happy_path_transitions_record_actor_and_timestamp(self):
        p1, p2, p3 = patch_attendance_facts()
        with p1, p2, p3:
            calculate_payroll(self.payroll, self.officer)
        self.payroll.refresh_from_db()
        self.assertEqual(self.payroll.status, "calculated")

        mark_reviewed(self.payroll, self.officer)
        self.payroll.refresh_from_db()
        self.assertEqual(self.payroll.status, "reviewed")
        self.assertEqual(self.payroll.reviewed_by, self.officer)
        self.assertIsNotNone(self.payroll.reviewed_at)

        approve_payroll(self.payroll, self.officer)
        self.payroll.refresh_from_db()
        self.assertEqual(self.payroll.status, "approved")
        self.assertEqual(self.payroll.approved_by, self.officer)
        self.assertIsNotNone(self.payroll.approved_at)

        # business-rules.md §7: approved payroll cannot be recalculated or re-approved.
        with self.assertRaises(ValidationError):
            calculate_payroll(self.payroll, self.officer)
        with self.assertRaises(ValidationError):
            approve_payroll(self.payroll, self.officer)


class PayrollServiceHelperTests(TestCase):
    def setUp(self):
        self.officer = User.objects.create_user(username="helper_officer", password="testpass123")
        Group.objects.get_or_create(name="Payroll Officer")[0].user_set.add(self.officer)
        self.employee = Employee.objects.create(
            employee_number="EMP-HELP-1",
            first_name="Helper",
            last_name="One",
            email="helper1@example.com",
            hire_date=date(2024, 1, 1),
        )

    def test_get_active_adjustments_filters_status_and_date_range(self):
        Bonus.objects.create(
            employee=self.employee, amount=Decimal("100"), effective_date=date(2026, 9, 15),
            status="active",
        )
        Bonus.objects.create(
            employee=self.employee, amount=Decimal("100"), effective_date=date(2026, 9, 15),
            status="cancelled",
        )
        Bonus.objects.create(
            employee=self.employee, amount=Decimal("100"), effective_date=date(2026, 8, 1),
            status="active",
        )
        result = get_active_adjustments_for_period(
            Bonus, self.employee, date(2026, 9, 1), date(2026, 9, 30)
        )
        self.assertEqual(result.count(), 1)

    def test_get_matching_tax_bracket_selects_correct_range(self):
        TaxBracket.objects.create(
            name="No tax", min_amount=Decimal("0"), max_amount=Decimal("999.99"),
            percentage=Decimal("0"),
        )
        TaxBracket.objects.create(
            name="Standard", min_amount=Decimal("1000"), max_amount=Decimal("4999.99"),
            percentage=Decimal("10"),
        )
        TaxBracket.objects.create(
            name="High", min_amount=Decimal("5000"), max_amount=None, percentage=Decimal("15"),
            fixed_amount=Decimal("50"),
        )

        self.assertEqual(get_matching_tax_bracket(Decimal("500")).name, "No tax")
        self.assertEqual(get_matching_tax_bracket(Decimal("3000")).name, "Standard")
        self.assertEqual(get_matching_tax_bracket(Decimal("10000")).name, "High")

    def test_get_matching_tax_bracket_ignores_inactive_bracket(self):
        TaxBracket.objects.create(
            name="Inactive", min_amount=Decimal("0"), max_amount=None, percentage=Decimal("5"),
            is_active=False,
        )
        self.assertIsNone(get_matching_tax_bracket(Decimal("100")))

    def test_user_in_groups(self):
        self.assertTrue(user_in_groups(self.officer, ["Payroll Officer"]))

        plain_user = User.objects.create_user(username="plainuser", password="testpass123")
        self.assertFalse(user_in_groups(plain_user, ["Payroll Officer"]))

        superuser = User.objects.create_superuser(
            username="super1", password="testpass123", email="s@example.com"
        )
        self.assertTrue(user_in_groups(superuser, ["Payroll Officer"]))


class PayrollViewPermissionTests(TestCase):
    """business-rules.md §9: navigation visibility is not authorization — verified server-side."""

    PAYROLL_URLS = [
        "/payroll/runs/",
        "/payroll/bonuses/",
        "/payroll/deductions/",
        "/payroll/tax-brackets/",
    ]

    def setUp(self):
        self.client = Client()
        self.officer = User.objects.create_user(username="perm_officer", password="testpass123")
        Group.objects.get_or_create(name="Payroll Officer")[0].user_set.add(self.officer)
        self.employee_user = User.objects.create_user(username="perm_emp", password="testpass123")
        Group.objects.get_or_create(name="Employee")[0].user_set.add(self.employee_user)

    def test_anonymous_user_redirected_to_login(self):
        resp = self.client.get("/payroll/runs/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.url)

    def test_employee_role_gets_branded_403_on_every_payroll_view(self):
        self.client.login(username="perm_emp", password="testpass123")
        for url in self.PAYROLL_URLS:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 403, url)
            self.assertContains(resp, "Access denied", status_code=403)

    def test_payroll_officer_gets_200_on_every_payroll_view(self):
        self.client.login(username="perm_officer", password="testpass123")
        for url in self.PAYROLL_URLS:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, url)


class PayrollViewFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.officer = User.objects.create_user(username="flow_officer", password="testpass123")
        Group.objects.get_or_create(name="Payroll Officer")[0].user_set.add(self.officer)
        self.client.login(username="flow_officer", password="testpass123")
        self.employee = Employee.objects.create(
            employee_number="EMP-FLOW-1",
            first_name="Flow",
            last_name="One",
            email="flow1@example.com",
            hire_date=date(2024, 1, 1),
        )

    def test_bonus_create_and_cancel(self):
        resp = self.client.post(
            "/payroll/bonuses/new/",
            {
                "employee": self.employee.pk,
                "bonus_type": "Performance",
                "amount": "100.00",
                "effective_date": "2026-09-15",
                "description": "",
            },
        )
        self.assertRedirects(resp, "/payroll/bonuses/")
        bonus = Bonus.objects.get(employee=self.employee)
        self.assertEqual(bonus.status, "active")
        self.assertEqual(bonus.created_by, self.officer)

        resp = self.client.post(f"/payroll/bonuses/{bonus.pk}/cancel/")
        self.assertRedirects(resp, "/payroll/bonuses/")
        bonus.refresh_from_db()
        self.assertEqual(bonus.status, "cancelled")

    def test_bonus_negative_amount_rejected_by_form(self):
        resp = self.client.post(
            "/payroll/bonuses/new/",
            {
                "employee": self.employee.pk,
                "bonus_type": "Performance",
                "amount": "-10.00",
                "effective_date": "2026-09-15",
                "description": "",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Bonus.objects.filter(employee=self.employee).exists())

    def test_deduction_create_and_cancel(self):
        resp = self.client.post(
            "/payroll/deductions/new/",
            {
                "employee": self.employee.pk,
                "deduction_type": "loan",
                "amount": "50.00",
                "effective_date": "2026-09-15",
                "description": "",
            },
        )
        self.assertRedirects(resp, "/payroll/deductions/")
        deduction = ManualDeduction.objects.get(employee=self.employee)
        self.assertEqual(deduction.status, "active")

        resp = self.client.post(f"/payroll/deductions/{deduction.pk}/cancel/")
        deduction.refresh_from_db()
        self.assertEqual(deduction.status, "cancelled")

    def test_deduction_negative_amount_rejected_by_form(self):
        resp = self.client.post(
            "/payroll/deductions/new/",
            {
                "employee": self.employee.pk,
                "deduction_type": "loan",
                "amount": "-5.00",
                "effective_date": "2026-09-15",
                "description": "",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(ManualDeduction.objects.filter(employee=self.employee).exists())

    def test_tax_bracket_create_and_toggle(self):
        resp = self.client.post(
            "/payroll/tax-brackets/new/",
            {
                "name": "Test bracket",
                "min_amount": "0.00",
                "max_amount": "999.99",
                "percentage": "5.00",
                "fixed_amount": "0.00",
                "is_active": "on",
            },
        )
        self.assertRedirects(resp, "/payroll/tax-brackets/")
        bracket = TaxBracket.objects.get(name="Test bracket")
        self.assertTrue(bracket.is_active)

        resp = self.client.post(f"/payroll/tax-brackets/{bracket.pk}/toggle/")
        self.assertRedirects(resp, "/payroll/tax-brackets/")
        bracket.refresh_from_db()
        self.assertFalse(bracket.is_active)

    def test_run_create_via_view(self):
        resp = self.client.post("/payroll/runs/new/", {"month": "11", "year": "2026"})
        payroll = Payroll.objects.get(month=11, year=2026)
        self.assertRedirects(resp, f"/payroll/runs/{payroll.pk}/")
        self.assertEqual(payroll.status, "draft")

    def test_run_create_duplicate_shows_friendly_error_not_500(self):
        create_payroll_run(12, 2026, self.officer)
        resp = self.client.post("/payroll/runs/new/", {"month": "12", "year": "2026"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "A payroll run already exists for 12/2026.")

    def test_run_detail_status_actions_follow_lifecycle(self):
        run = create_payroll_run(1, 2027, self.officer)

        # Draft: only Calculate is offered.
        resp = self.client.get(f"/payroll/runs/{run.pk}/")
        self.assertContains(resp, "Calculate")
        self.assertNotContains(resp, "Mark reviewed")

        self.client.post(f"/payroll/runs/{run.pk}/calculate/")
        run.refresh_from_db()
        self.assertEqual(run.status, "calculated")

        self.client.post(f"/payroll/runs/{run.pk}/review/")
        run.refresh_from_db()
        self.assertEqual(run.status, "reviewed")

        self.client.post(f"/payroll/runs/{run.pk}/approve/")
        run.refresh_from_db()
        self.assertEqual(run.status, "approved")

        resp = self.client.get(f"/payroll/runs/{run.pk}/")
        self.assertContains(resp, "Payroll is locked")
