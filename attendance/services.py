"""Public attendance facts and guarded leave transitions; no monetary calculation."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import Attendance, LeaveRequest


def get_employee_overtime_hours(employee, start_date, end_date):
    total = Attendance.objects.filter(
        employee=employee, date__range=(start_date, end_date)
    ).aggregate(total=Sum("overtime_hours"))["total"]
    return total or Decimal("0.00")


def get_absence_days(employee, start_date, end_date):
    return Decimal(
        Attendance.objects.filter(
            employee=employee, date__range=(start_date, end_date), status="absent"
        ).count()
    )


def get_unpaid_leave_days(employee, start_date, end_date):
    requests = LeaveRequest.objects.filter(
        employee=employee,
        status="approved",
        leave_type__is_paid=False,
        start_date__lte=end_date,
        end_date__gte=start_date,
    )
    return Decimal(
        sum(
            LeaveRequest._working_days_between(
                max(leave.start_date, start_date), min(leave.end_date, end_date)
            )
            for leave in requests
        )
    )


@transaction.atomic
def transition_leave(leave_request, actor, target_status):
    if not actor.is_authenticated or not (
        actor.is_superuser or actor.groups.filter(name__in=["Admin", "HR Manager"]).exists()
    ):
        raise PermissionDenied("Only Admin or HR Manager may review leave requests.")
    locked = LeaveRequest.objects.select_for_update().get(pk=leave_request.pk)
    if locked.employee.user_id == actor.pk:
        raise ValidationError("You cannot approve or reject your own leave request.")
    if not locked.can_transition_to(target_status):
        raise ValidationError("Only pending leave requests can be approved or rejected.")
    locked.status = target_status
    locked.approved_by = actor
    locked.approved_at = timezone.now()
    locked.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    leave_request.refresh_from_db()
    return leave_request
