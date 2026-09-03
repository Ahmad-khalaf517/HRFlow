from datetime import date, time
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from employees.models import Contract, Employee

from .forms import AttendanceForm, LeaveRequestForm
from .models import Attendance, LeaveRequest, LeaveType
from .services import get_absence_days, get_employee_overtime_hours, get_unpaid_leave_days


class AttendanceFlowAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = User.objects.create_user("demo-hr-audit")
        cls.manager.groups.add(Group.objects.get(name="HR Manager"))
        cls.user = User.objects.create_user("demo-worker-audit")
        cls.user.groups.add(Group.objects.get(name="Employee"))
        cls.officer = User.objects.create_user("demo-officer-audit")
        cls.officer.groups.add(Group.objects.get(name="Payroll Officer"))
        cls.employee = cls.make_employee(cls.user, "WORKER")
        cls.other = cls.make_employee(cls.manager, "HR")
        cls.leave_type = LeaveType.objects.create(name="Demo unpaid", is_paid=False)
        Contract.objects.create(
            employee=cls.employee,
            start_date=date(2026, 1, 1),
            basic_salary=3000,
            working_hours_per_day=8,
        )

    @staticmethod
    def make_employee(user, number):
        return Employee.objects.create(
            user=user,
            employee_number=number,
            first_name="Demo",
            last_name=number,
            email=number + "@example.test",
            hire_date=date(2026, 1, 1),
        )

    def leave(self, employee=None, **overrides):
        return LeaveRequest.objects.create(
            employee=employee or self.employee,
            leave_type=self.leave_type,
            start_date=date(2026, 9, 7),
            end_date=date(2026, 9, 8),
            **overrides,
        )

    def test_empty_and_forged_forms_report_errors(self):
        self.client.force_login(self.manager)
        for route in ["attendance_create", "leave_request_create"]:
            for data in [{}, {"employee": "9999999999999999999999999"}]:
                with self.subTest(route=route, data=data):
                    response = self.client.post(reverse("attendance:" + route), data)
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, "Please correct the following errors.")

    def test_invalid_attendance_filters_do_not_crash(self):
        self.client.force_login(self.user)
        for route in ["attendance_list", "my_attendance"]:
            for data in [
                {"date": "not-a-date"},
                {"date": "2026-02-30"},
                {"status": "bogus"},
                {"department": "²"},
            ]:
                with self.subTest(route=route, data=data):
                    response = self.client.get(reverse("attendance:" + route), data)
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.context["form"].errors)

    def test_employee_cannot_reassign_attendance_on_edit(self):
        record = Attendance.objects.create(employee=self.employee, date=date(2026, 9, 1))
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("attendance:attendance_update", args=[record.pk]),
            {
                "employee": self.other.pk,
                "date": "2026-09-01",
                "status": "present",
                "check_in": "08:00",
                "check_out": "17:00",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("employee", response.context["form"].errors)
        record.refresh_from_db()
        self.assertEqual(record.employee_id, self.employee.pk)

    def test_valid_attendance_then_duplicate_and_invalid_times(self):
        self.client.force_login(self.user)
        data = {
            "employee": self.employee.pk,
            "date": "2026-09-01",
            "status": "present",
            "check_in": "08:00",
            "check_out": "17:30",
        }
        url = reverse("attendance:attendance_create")
        self.assertEqual(self.client.post(url, data).status_code, 302)
        record = Attendance.objects.get()
        self.assertEqual(record.overtime_hours, Decimal("1.50"))
        self.assertEqual(self.client.post(url, data).status_code, 200)
        for value in ["07:00", "08:00", "invalid"]:
            form = AttendanceForm({**data, "date": "2026-09-02", "check_out": value})
            self.assertFalse(form.is_valid())
        self.assertEqual(Attendance.objects.count(), 1)

    def test_leave_decisions_require_post_and_csrf(self):
        leave = self.leave()
        self.client.force_login(self.manager)
        for action in ["approve", "reject"]:
            url = reverse("attendance:leave_request_" + action, args=[leave.pk])
            self.assertEqual(self.client.get(url).status_code, 405)
            csrf_client = Client(enforce_csrf_checks=True)
            csrf_client.force_login(self.manager)
            self.assertEqual(csrf_client.post(url).status_code, 403)
        leave.refresh_from_db()
        self.assertEqual(leave.status, "pending")

    def test_self_approval_is_rejected_in_service_and_view(self):
        leave = self.leave(self.other)
        with self.assertRaises(ValidationError):
            leave.approve(self.manager)
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("attendance:leave_request_approve", args=[leave.pk]), follow=True
        )
        self.assertContains(response, "You cannot approve or reject your own leave request.")
        leave.refresh_from_db()
        self.assertEqual(leave.status, "pending")
        self.assertIsNone(leave.approved_by)

    def test_officer_is_read_only_even_for_direct_service_calls(self):
        leave = self.leave()
        with self.assertRaises(PermissionDenied):
            leave.approve(self.officer)
        self.client.force_login(self.officer)
        url = reverse("attendance:leave_request_approve", args=[leave.pk])
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertEqual(
            self.client.get(reverse("attendance:leave_approval_list")).status_code, 200
        )

    def test_successful_approval_records_actor_and_repeated_transition_fails(self):
        leave = self.leave()
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("attendance:leave_request_approve", args=[leave.pk]), follow=True
        )
        self.assertContains(response, "Leave request approved successfully.")
        leave.refresh_from_db()
        self.assertEqual(leave.approved_by, self.manager)
        self.assertIsNotNone(leave.approved_at)
        with self.assertRaises(ValidationError):
            leave.reject(self.manager)

    def test_rejection_does_not_contribute_to_unpaid_days(self):
        leave = self.leave()
        leave.reject(self.manager)
        self.assertEqual(
            get_unpaid_leave_days(self.employee, date(2026, 9, 1), date(2026, 9, 30)), Decimal(0)
        )

    def test_inactive_leave_type_and_extreme_dates_are_rejected(self):
        self.leave_type.is_active = False
        self.leave_type.save()
        data = {
            "employee": self.employee.pk,
            "leave_type": self.leave_type.pk,
            "start_date": "2026-01-01",
            "end_date": "9999-12-31",
        }
        form = LeaveRequestForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("leave_type", form.errors)
        self.assertIn("supported maximum", str(form.non_field_errors()))
        self.assertEqual(LeaveRequest._working_days_between(date.max, date.max), 1)

    def test_facts_respect_employee_period_and_approved_unpaid_only(self):
        Attendance.objects.create(
            employee=self.employee, date=date(2026, 9, 1), check_in=time(8), check_out=time(18)
        )
        Attendance.objects.create(employee=self.employee, date=date(2026, 9, 2), status="absent")
        Attendance.objects.create(employee=self.other, date=date(2026, 9, 2), status="absent")
        Attendance.objects.create(employee=self.employee, date=date(2026, 8, 31), status="absent")
        leave = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=date(2026, 8, 28),
            end_date=date(2026, 9, 4),
        )
        leave.approve(self.manager)
        self.leave()  # Pending does not count.
        start, end = date(2026, 9, 1), date(2026, 9, 30)
        self.assertEqual(get_employee_overtime_hours(self.employee, start, end), Decimal(2))
        self.assertEqual(get_absence_days(self.employee, start, end), Decimal(1))
        self.assertEqual(get_unpaid_leave_days(self.employee, start, end), Decimal(4))

    def test_staff_flag_alone_cannot_manage_other_records(self):
        self.user.is_staff = True
        self.user.save()
        record = Attendance.objects.create(employee=self.other, date=date(2026, 9, 1))
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.get(reverse("attendance:attendance_detail", args=[record.pk])).status_code,
            404,
        )
