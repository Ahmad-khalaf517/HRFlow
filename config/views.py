"""
Dashboard landing view.

Lives here rather than in one of the domain apps because it reads across
employees/attendance/payroll and no single app owns "the page you land on
after login" — see TEAM_CONTEXT.md's dependency direction. Revisit if/when
the project settles on a dedicated home for cross-app views.
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from accounts.constants import ADMIN_GROUP, EMPLOYEE_GROUP, HR_MANAGER_GROUP, PAYROLL_OFFICER_GROUP
from attendance.models import Attendance, LeaveRequest
from employees.models import Employee
from payroll.models import Payroll


@require_GET
def health(request):
    """Unauthenticated liveness check for the deploy host (Render)."""
    return JsonResponse({"status": "ok"})


@login_required
def dashboard(request):
    today = timezone.localdate()
    group_names = set(request.user.groups.values_list("name", flat=True))
    is_admin = ADMIN_GROUP in group_names
    is_hr_manager = HR_MANAGER_GROUP in group_names
    is_payroll_officer = PAYROLL_OFFICER_GROUP in group_names

    if is_admin:
        current_payroll = (
            Payroll.objects.filter(month=today.month, year=today.year).order_by("-id").first()
        )
        dashboard_title = "Administration overview"
        dashboard_intro = "Company-wide HR, attendance, leave, and payroll activity."
        stats = [
            {"label": "Active Employees", "value": Employee.objects.filter(is_active=True).count()},
            {
                "label": "Present Today",
                "value": Attendance.objects.filter(date=today, status="present").count(),
            },
            {
                "label": "Pending Leave Requests",
                "value": LeaveRequest.objects.filter(status="pending").count(),
            },
            {
                "label": "This Month's Payroll",
                "value": current_payroll.get_status_display() if current_payroll else "Not started",
            },
        ]
        quick_links = [
            {
                "label": "Employees",
                "description": "Manage employee profiles and contracts.",
                "url": reverse("employees:employee-list"),
            },
            {
                "label": "User management",
                "description": "Create HR Manager and Payroll Officer accounts.",
                "url": reverse("staff-user-list"),
            },
            {
                "label": "Leave approvals",
                "description": "Review pending employee leave requests.",
                "url": reverse("attendance:leave_approval_list"),
            },
            {
                "label": "Payroll runs",
                "description": "Create and manage monthly payroll runs.",
                "url": reverse("payroll:run-list"),
            },
        ]
    elif is_hr_manager:
        dashboard_title = "HR overview"
        dashboard_intro = "Employee, attendance, and leave activity for your HR work."
        stats = [
            {"label": "Active Employees", "value": Employee.objects.filter(is_active=True).count()},
            {
                "label": "Present Today",
                "value": Attendance.objects.filter(date=today, status="present").count(),
            },
            {
                "label": "Pending Leave Requests",
                "value": LeaveRequest.objects.filter(status="pending").count(),
            },
        ]
        quick_links = [
            {
                "label": "Employees",
                "description": "Create and maintain employee profiles.",
                "url": reverse("employees:employee-list"),
            },
            {
                "label": "User management",
                "description": "Create HR Manager and Payroll Officer accounts.",
                "url": reverse("staff-user-list"),
            },
            {
                "label": "Attendance",
                "description": "Manage employee attendance records.",
                "url": reverse("attendance:attendance_list"),
            },
            {
                "label": "Leave approvals",
                "description": "Approve or reject leave requests.",
                "url": reverse("attendance:leave_approval_list"),
            },
        ]
    elif is_payroll_officer:
        current_payroll = (
            Payroll.objects.filter(month=today.month, year=today.year).order_by("-id").first()
        )
        dashboard_title = "Payroll overview"
        dashboard_intro = "Employee facts and payroll work available to Payroll Officers."
        stats = [
            {"label": "Active Employees", "value": Employee.objects.filter(is_active=True).count()},
            {
                "label": "Present Today",
                "value": Attendance.objects.filter(date=today, status="present").count(),
            },
            {
                "label": "This Month's Payroll",
                "value": current_payroll.get_status_display() if current_payroll else "Not started",
            },
        ]
        quick_links = [
            {
                "label": "Employee directory",
                "description": "View employee and contract information.",
                "url": reverse("employees:employee-list"),
            },
            {
                "label": "Attendance summary",
                "description": "Review attendance facts used by payroll.",
                "url": reverse("attendance:attendance_summary"),
            },
            {
                "label": "Payroll runs",
                "description": "Create, calculate, and progress payroll runs.",
                "url": reverse("payroll:run-list"),
            },
            {
                "label": "Payroll inputs",
                "description": "Manage bonuses and deductions.",
                "url": reverse("payroll:bonus-list"),
            },
        ]
    else:
        employee = Employee.objects.filter(user=request.user).first()
        dashboard_title = "My dashboard"
        dashboard_intro = "Your profile, attendance, and leave information."
        quick_links = []
        stats = [{"label": "Account Status", "value": "Active"}]
        if employee:
            attendance = Attendance.objects.filter(employee=employee, date=today).first()
            stats = [
                {"label": "Employment Status", "value": employee.get_employment_status_display()},
                {
                    "label": "Attendance Today",
                    "value": attendance.get_status_display() if attendance else "Not recorded",
                },
                {
                    "label": "Pending Leave Requests",
                    "value": LeaveRequest.objects.filter(
                        employee=employee, status="pending"
                    ).count(),
                },
            ]
            quick_links = [
                {
                    "label": "My profile",
                    "description": "View your employment profile.",
                    "url": reverse("employees:employee-detail", kwargs={"pk": employee.pk}),
                },
                {
                    "label": "My attendance",
                    "description": "Review your attendance records.",
                    "url": reverse("attendance:my_attendance"),
                },
                {
                    "label": "My leave requests",
                    "description": "Review or submit your leave requests.",
                    "url": reverse("attendance:my_leave_requests"),
                },
            ]

    if request.user.is_superuser or is_admin or is_payroll_officer:
        quick_links.append({
            "label": "Payslips",
            "description": "View and print payslips from approved payroll periods.",
            "url": reverse("payroll:payslip-list"),
        })
    elif EMPLOYEE_GROUP in group_names:
        quick_links.append({
            "label": "My payslips",
            "description": "View and print your payslips.",
            "url": reverse("payroll:payslip-list"),
        })

    return render(
        request,
        "home.html",
        {
            "dashboard_title": dashboard_title,
            "dashboard_intro": dashboard_intro,
            "stats": stats,
            "quick_links": quick_links,
        },
    )
