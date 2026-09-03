"""Compatibility exports; payroll uses the public attendance services directly."""

from attendance.services import (
    get_absence_days,
    get_employee_overtime_hours,
    get_unpaid_leave_days,
)

__all__ = ["get_absence_days", "get_employee_overtime_hours", "get_unpaid_leave_days"]
