from datetime import date, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from employees.models import Contract, Employee

from .models import Attendance, LeaveRequest, LeaveType

User = get_user_model()


class AttendanceConstraintTests(TestCase):
    """docs/business-rules.md §5: one attendance record per employee/date."""

    def setUp(self):
        self.user = User.objects.create_user(username="ada", password="secretpass123")
        self.employee = Employee.objects.create(
            user=self.user,
            employee_number="EMP-001",
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            hire_date=date(2024, 1, 1),
        )
        self.contract = Contract.objects.create(
            employee=self.employee,
            start_date=date(2024, 1, 1),
            basic_salary=Decimal("5000.00"),
            working_hours_per_day=Decimal("8.00"),
            status="active",
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

    def test_worked_hours_and_overtime_are_calculated(self):
        attendance = Attendance(
            employee=self.employee,
            date=date(2024, 6, 3),
            check_in=time(8, 0),
            check_out=time(17, 0),
            status="present",
        )
        attendance.save()

        self.assertEqual(attendance.worked_hours, Decimal("9.00"))
        self.assertEqual(attendance.overtime_hours, Decimal("1.00"))

    def test_overtime_is_zero_when_employee_works_standard_hours(self):
        attendance = Attendance(
            employee=self.employee,
            date=date(2024, 6, 4),
            check_in=time(8, 0),
            check_out=time(16, 0),
            status="present",
        )
        attendance.save()

        self.assertEqual(attendance.worked_hours, Decimal("8.00"))
        self.assertEqual(attendance.overtime_hours, Decimal("0.00"))

    def test_overtime_is_zero_when_employee_works_fewer_hours(self):
        attendance = Attendance(
            employee=self.employee,
            date=date(2024, 6, 5),
            check_in=time(8, 0),
            check_out=time(13, 30),
            status="present",
        )
        attendance.save()

        self.assertEqual(attendance.worked_hours, Decimal("5.50"))
        self.assertEqual(attendance.overtime_hours, Decimal("0.00"))

    def test_overtime_is_never_negative(self):
        attendance = Attendance(
            employee=self.employee,
            date=date(2024, 6, 6),
            check_in=time(9, 0),
            check_out=time(8, 30),
            status="present",
        )

        with self.assertRaises(ValidationError):
            attendance.full_clean()

    def test_missing_time_values_leave_hours_at_zero(self):
        attendance = Attendance(
            employee=self.employee,
            date=date(2024, 6, 7),
            status="present",
        )
        attendance.save()

        self.assertEqual(attendance.worked_hours, Decimal("0.00"))
        self.assertEqual(attendance.overtime_hours, Decimal("0.00"))

    def test_checkout_must_be_after_check_in(self):
        attendance = Attendance(
            employee=self.employee,
            date=date(2024, 6, 3),
            check_in=time(9, 0),
            check_out=time(8, 30),
            status="present",
        )

        with self.assertRaises(ValidationError):
            attendance.full_clean()


class AttendanceAuthorizationTests(TestCase):
    def setUp(self):
        self.employee_user = User.objects.create_user(username="employee", password="secretpass123")
        self.other_user = User.objects.create_user(username="other", password="secretpass123")
        self.hr_user = User.objects.create_user(username="hr", password="secretpass123")
        self.hr_group = Group.objects.get(name="HR Manager")
        self.hr_user.groups.add(self.hr_group)

        self.employee = Employee.objects.create(
            user=self.employee_user,
            employee_number="EMP-002",
            first_name="Grace",
            last_name="Hopper",
            email="grace@example.com",
            hire_date=date(2024, 1, 3),
        )
        self.other_employee = Employee.objects.create(
            user=self.other_user,
            employee_number="EMP-003",
            first_name="Linus",
            last_name="Torvalds",
            email="linus@example.com",
            hire_date=date(2024, 1, 4),
        )
        Contract.objects.create(
            employee=self.employee,
            start_date=date(2024, 1, 1),
            basic_salary=Decimal("4500.00"),
            working_hours_per_day=Decimal("8.00"),
            status="active",
        )
        Contract.objects.create(
            employee=self.other_employee,
            start_date=date(2024, 1, 1),
            basic_salary=Decimal("4600.00"),
            working_hours_per_day=Decimal("8.00"),
            status="active",
        )
        self.attendance = Attendance.objects.create(
            employee=self.other_employee,
            date=date(2024, 6, 5),
            check_in=time(8, 0),
            check_out=time(16, 0),
            status="present",
        )

    def test_employee_cannot_view_other_employee_attendance(self):
        self.client.force_login(self.employee_user)
        response = self.client.get(
            reverse("attendance:attendance_detail", args=[self.attendance.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_hr_manager_can_view_other_employee_attendance(self):
        self.client.force_login(self.hr_user)
        response = self.client.get(
            reverse("attendance:attendance_detail", args=[self.attendance.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_payroll_officer_cannot_manage_attendance(self):
        payroll_user = User.objects.create_user(username="payroll", password="secretpass123")
        payroll_group = Group.objects.get(name="Payroll Officer")
        payroll_user.groups.add(payroll_group)

        self.client.force_login(payroll_user)
        response = self.client.get(reverse("attendance:attendance_create"))
        self.assertEqual(response.status_code, 404)


class LeaveTypeManagementTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="adminleave", password="password123"
        )
        self.admin_group = Group.objects.get(name="Admin")
        self.admin_user.groups.add(self.admin_group)

        self.hr_user = User.objects.create_user(
            username="hrleave", password="password123"
        )
        self.hr_group = Group.objects.get(name="HR Manager")
        self.hr_user.groups.add(self.hr_group)

        self.employee_user = User.objects.create_user(
            username="employeeleave", password="password123"
        )
        self.employee = Employee.objects.create(
            user=self.employee_user,
            employee_number="EMP-004",
            first_name="Mary",
            last_name="Jane",
            email="mary@example.com",
            hire_date=date(2024, 1, 2),
        )
        self.leave_type = LeaveType.objects.create(name="Annual Leave", annual_allowance=20)

    def test_authorized_role_can_create_leave_type(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("attendance:leave_type_create"),
            {
                "name": "Sick Leave",
                "annual_allowance": 10,
                "is_paid": "on",
                "requires_approval": "on",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(LeaveType.objects.filter(name="Sick Leave").exists())

    def test_authorized_role_can_update_leave_type(self):
        self.client.force_login(self.hr_user)
        response = self.client.post(
            reverse("attendance:leave_type_update", args=[self.leave_type.pk]),
            {
                "name": "Annual Leave",
                "annual_allowance": 25,
                "is_paid": "on",
                "requires_approval": "on",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.leave_type.refresh_from_db()
        self.assertEqual(self.leave_type.annual_allowance, 25)

    def test_unauthorized_role_cannot_manage_leave_types(self):
        self.client.force_login(self.employee_user)
        response = self.client.get(reverse("attendance:leave_type_list"))
        self.assertEqual(response.status_code, 404)

    def test_leave_type_name_is_required(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("attendance:leave_type_create"),
            {"name": "   ", "annual_allowance": 5, "is_paid": "on", "requires_approval": "on"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Leave type name is required.")


class LeaveRequestTests(TestCase):
    def setUp(self):
        self.employee_user = User.objects.create_user(
            username="leaveemployee", password="password123"
        )
        self.other_user = User.objects.create_user(
            username="leaveother", password="password123"
        )
        self.employee = Employee.objects.create(
            user=self.employee_user,
            employee_number="EMP-005",
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            hire_date=date(2024, 1, 1),
        )
        self.other_employee = Employee.objects.create(
            user=self.other_user,
            employee_number="EMP-006",
            first_name="Bob",
            last_name="Jones",
            email="bob@example.com",
            hire_date=date(2024, 1, 2),
        )
        self.leave_type = LeaveType.objects.create(name="Annual Leave", annual_allowance=20)
        self.other_leave_request = LeaveRequest.objects.create(
            employee=self.other_employee,
            leave_type=self.leave_type,
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 5),
            reason="personal",
            status="pending",
        )

    def test_employee_can_submit_own_leave_request(self):
        self.client.force_login(self.employee_user)
        response = self.client.post(
            reverse("attendance:leave_request_create"),
            {
                "employee": str(self.employee.pk),
                "leave_type": str(self.leave_type.pk),
                "start_date": "2024-06-10",
                "end_date": "2024-06-12",
                "reason": "Family",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(LeaveRequest.objects.filter(employee=self.employee).exists())

    def test_employee_cannot_submit_for_another_employee(self):
        self.client.force_login(self.employee_user)
        self.client.post(
            reverse("attendance:leave_request_create"),
            {
                "employee": str(self.other_employee.pk),
                "leave_type": str(self.leave_type.pk),
                "start_date": "2024-06-10",
                "end_date": "2024-06-12",
                "reason": "Family",
            },
        )
        created = LeaveRequest.objects.filter(employee=self.employee).latest("created_at")
        self.assertEqual(created.employee, self.employee)

    def test_employee_can_view_only_their_own_leave_requests(self):
        self.client.force_login(self.employee_user)
        response = self.client.get(reverse("attendance:leave_request_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.other_employee.first_name)

    def test_another_employee_cannot_access_leave_request_detail(self):
        self.client.force_login(self.employee_user)
        response = self.client.get(
            reverse("attendance:leave_request_detail", args=[self.other_leave_request.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_end_date_before_start_date_is_rejected(self):
        self.client.force_login(self.employee_user)
        response = self.client.post(
            reverse("attendance:leave_request_create"),
            {
                "employee": str(self.employee.pk),
                "leave_type": str(self.leave_type.pk),
                "start_date": "2024-06-14",
                "end_date": "2024-06-12",
                "reason": "Family",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "End date cannot precede start date.")

    def test_requested_days_are_derived_from_weekdays(self):
        leave = LeaveRequest(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=date(2024, 6, 10),
            end_date=date(2024, 6, 12),
            reason="Vacation",
        )
        leave.calculate_requested_days()
        self.assertEqual(leave.requested_days, Decimal("3.00"))

    def test_weekends_are_excluded_from_requested_days(self):
        leave = LeaveRequest(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=date(2024, 6, 7),
            end_date=date(2024, 6, 10),
            reason="Vacation",
        )
        leave.calculate_requested_days()
        self.assertEqual(leave.requested_days, Decimal("2.00"))

    def test_overlapping_pending_requests_are_rejected(self):
        self.client.force_login(self.employee_user)
        first_response = self.client.post(
            reverse("attendance:leave_request_create"),
            {
                "employee": str(self.employee.pk),
                "leave_type": str(self.leave_type.pk),
                "start_date": "2024-07-02",
                "end_date": "2024-07-04",
                "reason": "Travel",
            },
        )
        self.assertEqual(first_response.status_code, 302)

        second_response = self.client.post(
            reverse("attendance:leave_request_create"),
            {
                "employee": str(self.employee.pk),
                "leave_type": str(self.leave_type.pk),
                "start_date": "2024-07-03",
                "end_date": "2024-07-05",
                "reason": "Travel again",
            },
        )
        self.assertEqual(second_response.status_code, 200)
        self.assertContains(second_response, "Pending or approved leave requests may not overlap")

    def test_status_starts_as_pending(self):
        request = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=date(2024, 6, 17),
            end_date=date(2024, 6, 17),
            reason="Test",
        )
        self.assertEqual(request.status, "pending")

    def test_employee_cannot_approve_or_reject_requests(self):
        self.client.force_login(self.employee_user)
        with self.assertRaises(NoReverseMatch):
            reverse("attendance:leave_request_approve")
        with self.assertRaises(NoReverseMatch):
            reverse("attendance:leave_request_reject")
