"""Payroll business logic. Views stay thin and call into this module.

Formula source: docs/business-rules.md §6 (Q-002/Q-003/Q-004 confirmed
2026-09-01). Money handling: docs/business-rules.md §3 — Decimal only,
2 decimal places, ROUND_HALF_UP.
"""

from calendar import monthrange
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.utils import timezone

from accounts.constants import EMPLOYEE_GROUP
from attendance.services import (
    get_absence_days,
    get_employee_overtime_hours,
    get_unpaid_leave_days,
)
from employees.models import Employee

from .models import (
    LOCKED_PAYROLL_STATUSES,
    Bonus,
    ManualDeduction,
    Payroll,
    PayrollItem,
    TaxBracket,
)

TWO_PLACES = Decimal("0.01")
OVERTIME_MULTIPLIER = Decimal("1.5")
CALCULATION_VERSION = "mvp-2"

RECALCULATABLE_STATUSES = ("draft", "calculated")
PAYROLL_MANAGER_GROUPS = ["Admin", "Payroll Officer"]


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def user_in_groups(user, group_names) -> bool:
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=group_names).exists()


def published_payslip_items():
    """Saved, complete items available after approval; never backfill live inputs."""
    return (
        PayrollItem.objects.select_related("payroll")
        .filter(
            payroll__status__in=LOCKED_PAYROLL_STATUSES,
            contract__isnull=False,
            calculation_inputs__has_keys=[
                "contract",
                "period_start",
                "period_end",
                "daily_divisor",
                "daily_rate",
                "hourly_rate",
                "overtime_multiplier",
                "tax",
            ],
        )
        .exclude(calculation_version="")
        .exclude(currency_code="")
        .exclude(employee_number_snapshot="")
        .exclude(employee_name_snapshot="")
        .order_by("-payroll__year", "-payroll__month", "employee_name_snapshot", "pk")
    )


def payslip_items_for_user(user):
    """Authorization shared by history/detail; staff status alone grants no access."""
    if not user.is_authenticated or not user.is_active:
        raise PermissionDenied("Sign in with an active account to view payslips.")
    items = published_payslip_items()
    if user_in_groups(user, PAYROLL_MANAGER_GROUPS):
        return items
    if user_in_groups(user, [EMPLOYEE_GROUP]):
        return items.filter(employee__user=user)
    # HR-specific "Limited" access awaits the business owner's definition.
    raise PermissionDenied("Your role does not have access to payslips.")


def get_active_adjustments_for_period(model, employee, period_start: date, period_end: date):
    return model.objects.filter(
        employee=employee,
        status="active",
        effective_date__gte=period_start,
        effective_date__lte=period_end,
    )


def get_matching_tax_bracket(gross_salary: Decimal):
    return (
        TaxBracket.objects.filter(is_active=True, min_amount__lte=gross_salary)
        .filter(Q(max_amount__isnull=True) | Q(max_amount__gte=gross_salary))
        .order_by("min_amount")
        .first()
    )


def create_payroll_run(month: int, year: int, created_by) -> Payroll:
    if not user_in_groups(created_by, PAYROLL_MANAGER_GROUPS):
        raise PermissionDenied("Only Admin or Payroll Officer may create payroll.")
    if (
        not isinstance(month, int)
        or not isinstance(year, int)
        or not 1 <= month <= 12
        or not 2000 <= year <= 2100
    ):
        raise ValidationError("Choose a valid month and a year from 2000 to 2100.")
    period_start = date(year, month, 1)
    period_end = date(year, month, monthrange(year, month)[1])
    try:
        with transaction.atomic():
            return Payroll.objects.create(
                period_start=period_start,
                period_end=period_end,
                month=month,
                year=year,
                created_by=created_by,
            )
    except IntegrityError as exc:
        raise ValidationError(f"A payroll run already exists for {month:02d}/{year}.") from exc


@transaction.atomic
def calculate_payroll(payroll: Payroll, actor) -> Payroll:
    if not user_in_groups(actor, PAYROLL_MANAGER_GROUPS):
        raise PermissionDenied("Only Admin or Payroll Officer may calculate payroll.")
    # Lock and refresh before inspecting status; callers may hold stale model instances.
    Payroll.objects.select_for_update().get(pk=payroll.pk)
    payroll.refresh_from_db()
    if payroll.status not in RECALCULATABLE_STATUSES:
        raise ValidationError(
            f"Payroll in '{payroll.get_status_display()}' status cannot be (re)calculated."
        )

    employees = Employee.objects.filter(is_active=True, employment_status="active")
    included_ids = []

    for employee in employees:
        contract = employee.contracts.filter(status="active").first()
        if contract is None:
            continue
        included_ids.append(employee.pk)

        overtime_hours = get_employee_overtime_hours(
            employee, payroll.period_start, payroll.period_end
        )
        absence_days = get_absence_days(employee, payroll.period_start, payroll.period_end)
        unpaid_leave_days = get_unpaid_leave_days(
            employee, payroll.period_start, payroll.period_end
        )

        if any(
            value < 0
            for value in (
                contract.basic_salary,
                contract.allowances_default,
                overtime_hours,
                absence_days,
                unpaid_leave_days,
            )
        ):
            raise ValidationError("Payroll inputs cannot be negative.")
        if contract.working_hours_per_day <= 0:
            raise ValidationError("Contract working hours must be greater than zero.")

        daily_rate = contract.basic_salary / Decimal(30)
        hourly_rate = daily_rate / contract.working_hours_per_day

        overtime_amount = _money(overtime_hours * hourly_rate * OVERTIME_MULTIPLIER)
        absence_deduction = _money(absence_days * daily_rate)
        unpaid_leave_deduction = _money(unpaid_leave_days * daily_rate)

        bonus_amount = _money(
            get_active_adjustments_for_period(
                Bonus, employee, payroll.period_start, payroll.period_end
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal(0)
        )
        manual_deduction_amount = _money(
            get_active_adjustments_for_period(
                ManualDeduction, employee, payroll.period_start, payroll.period_end
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal(0)
        )

        gross_salary = _money(
            contract.basic_salary + contract.allowances_default + overtime_amount + bonus_amount
        )

        bracket = get_matching_tax_bracket(gross_salary)
        if bracket and (bracket.fixed_amount < 0 or bracket.percentage < 0):
            raise ValidationError("Tax inputs cannot be negative.")
        tax_amount = (
            _money(bracket.fixed_amount + gross_salary * bracket.percentage / Decimal(100))
            if bracket
            else Decimal("0.00")
        )

        total_deductions = _money(
            absence_deduction + unpaid_leave_deduction + manual_deduction_amount + tax_amount
        )
        net_salary = _money(gross_salary - total_deductions)
        if net_salary < 0:
            raise ValidationError("Deductions cannot exceed gross salary.")

        PayrollItem.objects.update_or_create(
            payroll=payroll,
            employee=employee,
            defaults={
                "contract": contract,
                "employee_number_snapshot": employee.employee_number,
                "employee_name_snapshot": f"{employee.first_name} {employee.last_name}".strip(),
                "currency_code": payroll.currency_code,
                "calculation_version": CALCULATION_VERSION,
                "calculation_inputs": {
                    "contract": {
                        "id": contract.pk,
                        "start_date": contract.start_date.isoformat(),
                        "end_date": contract.end_date.isoformat() if contract.end_date else None,
                        "type": contract.contract_type,
                        "basic_salary": str(contract.basic_salary),
                        "allowances": str(contract.allowances_default),
                        "working_hours_per_day": str(contract.working_hours_per_day),
                        "working_days_per_week": contract.working_days_per_week,
                    },
                    "period_start": payroll.period_start.isoformat(),
                    "period_end": payroll.period_end.isoformat(),
                    "daily_divisor": "30",
                    "daily_rate": str(daily_rate),
                    "hourly_rate": str(hourly_rate),
                    "overtime_multiplier": str(OVERTIME_MULTIPLIER),
                    "tax": {
                        "id": bracket.pk,
                        "min_amount": str(bracket.min_amount),
                        "max_amount": (
                            str(bracket.max_amount) if bracket.max_amount is not None else None
                        ),
                        "percentage": str(bracket.percentage),
                        "fixed_amount": str(bracket.fixed_amount),
                    }
                    if bracket
                    else None,
                    "attendance_source": "attendance-services-v1",
                },
                "basic_salary": contract.basic_salary,
                "allowances": contract.allowances_default,
                "overtime_hours": overtime_hours,
                "overtime_amount": overtime_amount,
                "bonus_amount": bonus_amount,
                "gross_salary": gross_salary,
                "absence_days": absence_days,
                "absence_deduction": absence_deduction,
                "unpaid_leave_days": unpaid_leave_days,
                "unpaid_leave_deduction": unpaid_leave_deduction,
                "manual_deduction_amount": manual_deduction_amount,
                "tax_amount": tax_amount,
                "total_deductions": total_deductions,
                "net_salary": net_salary,
            },
        )

    # Recalculation must not retain an employee who no longer qualifies for this run.
    payroll.items.exclude(employee_id__in=included_ids).delete()
    totals = payroll.items.aggregate(
        total_gross=Sum("gross_salary"),
        total_deductions=Sum("total_deductions"),
        total_net=Sum("net_salary"),
    )
    payroll.total_gross = totals["total_gross"] or Decimal("0.00")
    payroll.total_deductions = totals["total_deductions"] or Decimal("0.00")
    payroll.total_net = totals["total_net"] or Decimal("0.00")
    payroll.status = "calculated"
    payroll.save(update_fields=["total_gross", "total_deductions", "total_net", "status"])
    return payroll


@transaction.atomic
def mark_reviewed(payroll: Payroll, actor) -> Payroll:
    if not user_in_groups(actor, PAYROLL_MANAGER_GROUPS):
        raise PermissionDenied("Only Admin or Payroll Officer may review payroll.")
    Payroll.objects.select_for_update().get(pk=payroll.pk)
    payroll.refresh_from_db()
    if payroll.status != "calculated":
        raise ValidationError("Only calculated payroll can be moved to Reviewed.")
    payroll.status = "reviewed"
    payroll.reviewed_by = actor
    payroll.reviewed_at = timezone.now()
    payroll.save(update_fields=["status", "reviewed_by", "reviewed_at"])
    return payroll


@transaction.atomic
def approve_payroll(payroll: Payroll, actor) -> Payroll:
    Payroll.objects.select_for_update().get(pk=payroll.pk)
    payroll.refresh_from_db()
    if payroll.status != "reviewed":
        raise ValidationError("Only reviewed payroll can be approved.")
    if not user_in_groups(actor, PAYROLL_MANAGER_GROUPS):
        raise PermissionDenied("Only Admin or Payroll Officer may approve payroll.")
    payroll.status = "approved"
    payroll.approved_by = actor
    payroll.approved_at = timezone.now()
    payroll.save(update_fields=["status", "approved_by", "approved_at"])
    return payroll
