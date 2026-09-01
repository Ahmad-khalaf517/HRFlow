"""
Dashboard landing view.

Lives here rather than in one of the domain apps because it reads across
employees/attendance/payroll and no single app owns "the page you land on
after login" — see TEAM_CONTEXT.md's dependency direction. Revisit if/when
the project settles on a dedicated home for cross-app views.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from attendance.models import Attendance, LeaveRequest
from employees.models import Employee
from payroll.models import Payroll


@login_required
def dashboard(request):
    today = timezone.localdate()

    current_payroll = (
        Payroll.objects.filter(month=today.month, year=today.year).order_by("-id").first()
    )

    stats = [
        {
            "label": "Active Employees",
            "value": Employee.objects.filter(is_active=True).count(),
        },
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

    setup_steps = [
        {"label": "Database connected (Neon)", "done": True},
        {"label": "Design system applied", "done": True},
        {"label": "Authentication", "done": True},
        {"label": "Employee management", "done": False},
        {"label": "Attendance & leave", "done": False},
        {"label": "Payroll processing", "done": False},
    ]

    return render(
        request,
        "home.html",
        {"stats": stats, "setup_steps": setup_steps},
    )
