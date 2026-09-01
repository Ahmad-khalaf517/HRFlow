from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint
from django.utils import timezone


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

    def _calculate_worked_hours(self):
        if not self.employee:
            self.worked_hours = Decimal("0")
            self.overtime_hours = Decimal("0")
            return

        if not self.check_in or not self.check_out:
            self.worked_hours = Decimal("0")
            self.overtime_hours = Decimal("0")
            return

        delta = self._time_delta_seconds()
        if delta <= 0:
            raise ValidationError({"check_out": "Check-out must be after check-in."})

        hours = Decimal(str(delta)) / Decimal("3600")
        self.worked_hours = hours.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        contract = self.employee.contracts.filter(status="active").order_by("-start_date").first()
        contract_hours = (
            Decimal(str(contract.working_hours_per_day)) if contract else Decimal("0")
        )
        overtime = self.worked_hours - contract_hours
        self.overtime_hours = max(overtime, Decimal("0")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def _time_delta_seconds(self):
        from datetime import datetime

        today = self.date or datetime.today().date()
        check_in = datetime.combine(today, self.check_in)
        check_out = datetime.combine(today, self.check_out)
        return (check_out - check_in).total_seconds()

    def clean(self):
        super().clean()
        if self.check_in and self.check_out and self.check_out <= self.check_in:
            raise ValidationError({"check_out": "Check-out must be after check-in."})
        self._calculate_worked_hours()

    def save(self, *args, **kwargs):
        if self.check_in and self.check_out and self.check_out <= self.check_in:
            raise ValidationError({"check_out": "Check-out must be after check-in."})
        self._calculate_worked_hours()
        super().save(*args, **kwargs)

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

    def clean(self):
        super().clean()
        if not self.name or not self.name.strip():
            raise ValidationError({"name": "Leave type name is required."})
        self.name = self.name.strip()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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

    @staticmethod
    def _working_days_between(start_date, end_date):
        current = start_date
        count = 0
        while current <= end_date:
            if current.weekday() < 5:
                count += 1
            current += timedelta(days=1)
        return count

    def calculate_requested_days(self):
        if not self.start_date or not self.end_date:
            self.requested_days = Decimal("0")
            return self.requested_days
        if self.end_date < self.start_date:
            self.requested_days = Decimal("0")
            return self.requested_days
        working_days = self._working_days_between(self.start_date, self.end_date)
        self.requested_days = Decimal(working_days).quantize(Decimal("0.01"))
        return self.requested_days

    def can_transition_to(self, new_status):
        allowed = {
            "pending": {"approved", "rejected"},
        }
        return self.status in allowed and new_status in allowed[self.status]

    def approve(self, user):
        if self.status != "pending":
            raise ValidationError("Only pending leave requests can be approved.")
        self.status = "approved"
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

    def reject(self, user):
        if self.status != "pending":
            raise ValidationError("Only pending leave requests can be rejected.")
        self.status = "rejected"
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot precede start date."})

        if (
            self.employee
            and self.start_date
            and self.end_date
            and self.status in {"pending", "approved"}
        ):
            overlapping = LeaveRequest.objects.filter(
                employee=self.employee,
                status__in=["pending", "approved"],
                start_date__lte=self.end_date,
                end_date__gte=self.start_date,
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError(
                    "Pending or approved leave requests may not overlap for the same employee."
                )

        self.calculate_requested_days()

    def save(self, *args, **kwargs):
        self.full_clean()
        self.calculate_requested_days()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} — {self.leave_type} ({self.start_date} to {self.end_date})"
