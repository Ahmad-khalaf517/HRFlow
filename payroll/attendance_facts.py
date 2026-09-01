"""Temporary stand-in for the attendance app's public service boundary.

TEAM_CONTEXT.md defines three required attendance functions that payroll
must consume — payroll must never query Attendance/LeaveRequest directly:

    get_employee_overtime_hours(employee, start_date, end_date)
    get_absence_days(employee, start_date, end_date)
    get_unpaid_leave_days(employee, start_date, end_date)

attendance/services.py doesn't exist yet (Person 2's app). These mocks match
the exact signatures with deterministic (not random) values so calculations
are stable across reruns. Once attendance/services.py ships, replace the
import in payroll/services.py with the real module — no other payroll code
should need to change, since call sites only depend on the signature.
"""

from decimal import Decimal


def get_employee_overtime_hours(employee, start_date, end_date) -> Decimal:
    return Decimal(employee.id % 6)


def get_absence_days(employee, start_date, end_date) -> Decimal:
    return Decimal(employee.id % 3)


def get_unpaid_leave_days(employee, start_date, end_date) -> Decimal:
    return Decimal(1) if employee.id % 4 == 0 else Decimal(0)
