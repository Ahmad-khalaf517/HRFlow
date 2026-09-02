from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser, Group, User
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from employees.models import Contract, Employee

from .models import PayrollItem, Payslip, TaxBracket
from .services import (
    approve_payroll,
    calculate_payroll,
    create_payroll_run,
    mark_reviewed,
    payslip_items_for_user,
)


class PayslipTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.users = {}
        for role, group in (
            ("employee", "Employee"),
            ("other", "Employee"),
            ("officer", "Payroll Officer"),
            ("admin", "Admin"),
            ("hr", "HR Manager"),
            ("unlinked", "Employee"),
        ):
            user = User.objects.create_user(username=f"slip_{role}")
            user.groups.add(Group.objects.get(name=group))
            cls.users[role] = user
        cls.users["staff"] = User.objects.create_user(username="slip_staff", is_staff=True)
        cls.employees = {}
        for name in ("employee", "other", "hr"):
            employee = Employee.objects.create(
                user=cls.users[name],
                employee_number=f"SLIP-{name.upper()}",
                first_name="Demo",
                last_name=name.title(),
                email=f"{name}@example.test",
                hire_date=date(2026, 1, 1),
            )
            cls.employees[name] = employee
            Contract.objects.create(
                employee=employee,
                basic_salary=Decimal("3000.00"),
                allowances_default=Decimal("150.00"),
                working_hours_per_day=8,
                start_date=date(2026, 1, 1),
            )
        TaxBracket.objects.create(name="Demo tax", min_amount=0, percentage=10)
        cls.runs = {}
        for month, status in enumerate(("draft", "calculated", "reviewed", "approved", "paid"), 1):
            run = create_payroll_run(month, 2026, cls.users["officer"])
            with (
                patch("payroll.services.get_employee_overtime_hours", return_value=Decimal(1)),
                patch("payroll.services.get_absence_days", return_value=Decimal(1)),
                patch("payroll.services.get_unpaid_leave_days", return_value=Decimal(0)),
            ):
                calculate_payroll(run, cls.users["officer"])
            if status in ("reviewed", "approved", "paid"):
                mark_reviewed(run, cls.users["officer"])
            if status in ("approved", "paid"):
                approve_payroll(run, cls.users["officer"])
            run.status = status
            run.save(update_fields=["status"])
            cls.runs[status] = run

    def item(self, owner="employee", status="approved"):
        return self.runs[status].items.get(employee=self.employees[owner])

    def detail_url(self, owner="employee", status="approved"):
        return reverse("payroll:payslip-detail", args=[self.item(owner, status).pk])

    def test_anonymous_redirects_to_login(self):
        for url in (reverse("payroll:payslip-list"), self.detail_url()):
            response = self.client.get(url)
            self.assertRedirects(response, f"/accounts/login/?next={url}")

    def test_employee_history_is_own_approved_and_paid_only(self):
        self.client.force_login(self.users["employee"])
        response = self.client.get(reverse("payroll:payslip-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["page_obj"]),
            [
                self.item(status="paid"),
                self.item(status="approved"),
            ],
        )
        self.assertNotContains(response, "Demo Other")
        self.assertContains(response, "My payslips")

    def test_employee_cannot_guess_another_employee_url(self):
        self.client.force_login(self.users["employee"])
        response = self.client.get(self.detail_url(owner="other"))
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, "Demo Other", status_code=404)
        self.assertNotContains(response, "2751.87", status_code=404)

    def test_missing_item_returns_404(self):
        self.client.force_login(self.users["employee"])
        response = self.client.get(reverse("payroll:payslip-detail", args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_unpublished_items_are_not_accessible_even_to_managers(self):
        for role in ("employee", "officer", "admin"):
            self.client.force_login(self.users[role])
            for status in ("draft", "calculated", "reviewed"):
                with self.subTest(role=role, status=status):
                    self.assertEqual(
                        self.client.get(self.detail_url(status=status)).status_code, 404
                    )

    def test_admin_and_officer_can_view_all_published_items(self):
        for role in ("admin", "officer"):
            self.client.force_login(self.users[role])
            response = self.client.get(reverse("payroll:payslip-list"))
            with self.subTest(role=role):
                self.assertEqual(response.context["page_obj"].paginator.count, 6)
                self.assertEqual(self.client.get(self.detail_url(owner="other")).status_code, 200)

    def test_hr_specific_access_is_not_inferred_from_limited_rule(self):
        self.client.force_login(self.users["hr"])
        for url in (reverse("payroll:payslip-list"), self.detail_url(owner="hr")):
            self.assertEqual(self.client.get(url).status_code, 403)

    def test_staff_flag_alone_does_not_grant_access(self):
        self.client.force_login(self.users["staff"])
        self.assertEqual(self.client.get(self.detail_url()).status_code, 403)

    def test_employee_without_profile_gets_empty_history(self):
        self.client.force_login(self.users["unlinked"])
        response = self.client.get(reverse("payroll:payslip-list"))
        self.assertContains(response, "No payslips available yet.")
        self.assertEqual(self.client.get(self.detail_url()).status_code, 404)

    def test_service_rejects_anonymous_and_inactive_users(self):
        inactive = self.users["employee"]
        inactive.is_active = False
        for user in (AnonymousUser(), inactive):
            with self.assertRaises(PermissionDenied):
                payslip_items_for_user(user)

    def test_detail_uses_saved_components_and_has_no_write_side_effects(self):
        self.client.force_login(self.users["employee"])
        item = self.item()
        Contract.objects.filter(employee=self.employees["employee"]).update(basic_salary=9999)
        Employee.objects.filter(pk=self.employees["employee"].pk).update(first_name="Changed")
        TaxBracket.objects.update(percentage=99)
        with patch(
            "payroll.services.calculate_payroll", side_effect=AssertionError("recalculated")
        ):
            with CaptureQueriesContext(connection) as queries:
                response = self.client.get(self.detail_url())
            self.client.get(self.detail_url())
        self.assertContains(response, "Demo Employee")
        for value in ("3000.00", "150.00", "18.75", "100.00", "316.88", "416.88", "2751.87"):
            self.assertContains(response, value)
        self.assertContains(response, "USD")
        self.assertEqual(Payslip.objects.count(), 0)
        self.assertFalse(
            any(
                query["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
                for query in queries
            )
        )
        self.assertFalse(any('"employees_contract"' in query["sql"] for query in queries))
        updated = PayrollItem.objects.get(pk=item.pk)
        self.assertEqual(updated.updated_at, item.updated_at)
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertIn("private", response.headers["Cache-Control"])

    def test_post_is_rejected_on_read_only_pages(self):
        self.client.force_login(self.users["employee"])
        for url in (reverse("payroll:payslip-list"), self.detail_url()):
            self.assertEqual(self.client.post(url).status_code, 405)

    def test_legacy_incomplete_snapshot_is_not_published(self):
        # Emulate the historical rows preserved by migration 0003.
        item = self.item()
        PayrollItem.objects.filter(pk=item.pk).update(calculation_inputs={}, calculation_version="")
        self.client.force_login(self.users["employee"])
        self.assertEqual(self.client.get(self.detail_url()).status_code, 404)
        response = self.client.get(reverse("payroll:payslip-list"))
        self.assertEqual(list(response.context["page_obj"]), [self.item(status="paid")])

    def test_filters_cannot_widen_employee_scope(self):
        self.client.force_login(self.users["employee"])
        response = self.client.get(
            reverse("payroll:payslip-list"),
            {
                "employee": self.employees["other"].pk,
                "page": "invalid",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item.employee_id for item in response.context["page_obj"]},
            {self.employees["employee"].pk},
        )

    def test_dashboard_and_sidebar_links_match_access(self):
        for role in ("employee", "officer", "admin", "unlinked", "hr", "staff"):
            self.client.force_login(self.users[role])
            response = self.client.get(reverse("home"))
            with self.subTest(role=role):
                if role in ("hr", "staff"):
                    self.assertNotContains(response, reverse("payroll:payslip-list"))
                else:
                    self.assertContains(response, reverse("payroll:payslip-list"))
                    self.assertTrue(
                        any(
                            link["url"] == reverse("payroll:payslip-list")
                            for link in response.context["quick_links"]
                        )
                    )

    def test_manager_approval_makes_payslip_link_available(self):
        self.client.force_login(self.users["officer"])
        run = self.runs["calculated"]
        item = run.items.get(employee=self.employees["employee"])
        url = reverse("payroll:payslip-detail", args=[item.pk])
        response = self.client.get(reverse("payroll:run-detail", args=[run.pk]))
        self.assertNotContains(response, url)
        self.client.post(reverse("payroll:run-review", args=[run.pk]))
        response = self.client.post(reverse("payroll:run-approve", args=[run.pk]), follow=True)
        self.assertContains(response, url)
        self.assertContains(self.client.get(url), "Print payslip")
        self.client.force_login(self.users["employee"])
        self.assertContains(self.client.get(url), "2751.87")

    def test_legacy_run_explains_unavailable_payslip(self):
        item = self.item()
        PayrollItem.objects.filter(pk=item.pk).update(calculation_version="")
        self.client.force_login(self.users["officer"])
        response = self.client.get(reverse("payroll:run-detail", args=[item.payroll_id]))
        self.assertContains(response, "Payslip unavailable for this historical item.")
        self.assertNotContains(response, reverse("payroll:payslip-detail", args=[item.pk]))

    def test_inactive_employee_record_keeps_own_history_when_account_active(self):
        Employee.objects.filter(pk=self.employees["employee"].pk).update(is_active=False)
        self.client.force_login(self.users["employee"])
        self.assertContains(self.client.get(self.detail_url()), "2751.87")
