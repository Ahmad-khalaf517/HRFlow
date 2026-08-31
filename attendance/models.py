from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint


class Attendance(models.Model):
    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
        ("leave", "Leave"),
        ("holiday", "Holiday"),
        ("weekend", "Weekend"),
    ]

    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.PROTECT, related_name="attendance_records"
    )
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    # Hours only — attendance never stores monetary overtime values.
    worked_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="present")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
        constraints = [
            # docs/business-rules.md §5: one attendance record per employee/date.
            UniqueConstraint(
                fields=["employee", "date"], name="attendance_one_per_employee_per_date"
            ),
            CheckConstraint(
                condition=Q(check_in__isnull=True)
                | Q(check_out__isnull=True)
                | Q(check_out__gt=F("check_in")),
                name="attendance_check_out_after_check_in",
            ),
            CheckConstraint(condition=Q(worked_hours__gte=0), name="attendance_worked_hours_gte_0"),
            CheckConstraint(
                condition=Q(overtime_hours__gte=0), name="attendance_overtime_hours_gte_0"
            ),
        ]

    def __str__(self):
        return f"{self.employee} — {self.date}"


class LeaveType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    annual_allowance = models.PositiveIntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.PROTECT, related_name="leave_requests"
    )
    leave_type = models.ForeignKey(
        LeaveType, on_delete=models.PROTECT, related_name="leave_requests"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    # Derived by the system from the approved work calendar — not directly editable.
    requested_days = models.DecimalField(max_digits=5, decimal_places=2, default=0, editable=False)
    reason = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leave_requests_approved",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            CheckConstraint(
                condition=Q(end_date__gte=F("start_date")),
                name="leaverequest_end_date_not_before_start_date",
            ),
            CheckConstraint(
                condition=Q(requested_days__gte=0), name="leaverequest_requested_days_gte_0"
            ),
        ]

    def __str__(self):
        return f"{self.employee} — {self.leave_type} ({self.start_date} to {self.end_date})"
