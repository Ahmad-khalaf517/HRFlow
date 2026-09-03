from datetime import date
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from . import services
from .forms import (
    BonusForm,
    BreakdownFilterForm,
    ManualDeductionForm,
    PayrollFilterForm,
    PayrollRunForm,
    PayslipFilterForm,
    TaxBracketForm,
)
from .models import Bonus, ManualDeduction, Payroll, TaxBracket


def require_payroll_manager(view_func):
    """business-rules.md §9: payroll inputs/runs are Manage-only for Admin/Payroll Officer.

    Renders a branded in-module response (rather than raising PermissionDenied and
    falling through to Django's unstyled default 403 page) so the denial still reads
    as part of the app. Still a real 403: status_code stays 403 either way.
    """

    @wraps(view_func)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not services.user_in_groups(request.user, services.PAYROLL_MANAGER_GROUPS):
            return render(
                request,
                "payroll/access_denied.html",
                {"reason": "Only Admin or Payroll Officer may access payroll."},
                status=403,
            )
        return view_func(request, *args, **kwargs)

    return wrapped


# --- Bonuses (HRF-21) -------------------------------------------------


@require_payroll_manager
def bonus_list(request):
    bonuses = Bonus.objects.select_related("employee").all()
    return render(request, "payroll/bonus_list.html", {"bonuses": bonuses, "today": date.today()})


@require_payroll_manager
def bonus_create(request):
    form = BonusForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        bonus = form.save(commit=False)
        bonus.created_by = request.user
        bonus.save()
        messages.success(request, "Bonus recorded.")
        return redirect("payroll:bonus-list")
    return render(request, "payroll/bonus_form.html", {"form": form})


@require_payroll_manager
def bonus_update(request, pk):
    bonus = get_object_or_404(Bonus, pk=pk)
    if bonus.effective_date < date.today():
        messages.error(
            request, "This bonus's effective date has passed and can no longer be edited."
        )
        return redirect("payroll:bonus-list")

    form = BonusForm(request.POST if request.method == "POST" else None, instance=bonus)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Bonus updated.")
        return redirect("payroll:bonus-list")
    return render(request, "payroll/bonus_form.html", {"form": form, "bonus": bonus})


@require_payroll_manager
def bonus_cancel(request, pk):
    if request.method == "POST":
        bonus = get_object_or_404(Bonus, pk=pk)
        if bonus.effective_date < date.today():
            messages.error(
                request, "This bonus's effective date has passed and can no longer be cancelled."
            )
        else:
            bonus.status = "cancelled"
            bonus.save(update_fields=["status"])
            messages.success(request, "Bonus cancelled.")
    return redirect("payroll:bonus-list")


# --- Manual deductions (HRF-22) ----------------------------------------


@require_payroll_manager
def deduction_list(request):
    deductions = ManualDeduction.objects.select_related("employee").all()
    return render(request, "payroll/deduction_list.html", {"deductions": deductions})


@require_payroll_manager
def deduction_create(request):
    form = ManualDeductionForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        deduction = form.save(commit=False)
        deduction.created_by = request.user
        deduction.save()
        messages.success(request, "Manual deduction recorded.")
        return redirect("payroll:deduction-list")
    return render(request, "payroll/deduction_form.html", {"form": form})


@require_payroll_manager
def deduction_cancel(request, pk):
    if request.method == "POST":
        deduction = get_object_or_404(ManualDeduction, pk=pk)
        deduction.status = "cancelled"
        deduction.save(update_fields=["status"])
        messages.success(request, "Manual deduction cancelled.")
    return redirect("payroll:deduction-list")


# --- Tax brackets (HRF-23) ----------------------------------------------


@require_payroll_manager
def tax_bracket_list(request):
    brackets = TaxBracket.objects.all()
    return render(request, "payroll/tax_bracket_list.html", {"brackets": brackets})


@require_payroll_manager
def tax_bracket_create(request):
    form = TaxBracketForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Tax bracket saved.")
        return redirect("payroll:tax-bracket-list")
    return render(request, "payroll/tax_bracket_form.html", {"form": form})


@require_payroll_manager
def tax_bracket_toggle(request, pk):
    if request.method == "POST":
        bracket = get_object_or_404(TaxBracket, pk=pk)
        bracket.is_active = not bracket.is_active
        bracket.save(update_fields=["is_active"])
        messages.success(
            request, f"Tax bracket {'activated' if bracket.is_active else 'deactivated'}."
        )
    return redirect("payroll:tax-bracket-list")


# --- Payroll runs (HRF-24, HRF-26) --------------------------------------


@require_payroll_manager
def run_list(request):
    runs = Payroll.objects.annotate(item_count=Count("items"), total_tax=Sum("items__tax_amount"))
    form = PayrollFilterForm(request.GET)
    if form.is_valid():
        for field in ("month", "year", "status"):
            if form.cleaned_data[field]:
                runs = runs.filter(**{field: form.cleaned_data[field]})
    else:
        runs = runs.none()
    page = Paginator(runs.order_by("-year", "-month", "-pk"), 20).get_page(request.GET.get("page"))
    return render(request, "payroll/run_list.html", {"runs": page, "page_obj": page, "form": form})


@require_payroll_manager
def run_create(request):
    form = PayrollRunForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            run = services.create_payroll_run(
                form.cleaned_data["month"], form.cleaned_data["year"], request.user
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "Payroll run created in Draft.")
            return redirect("payroll:run-detail", pk=run.pk)
    return render(request, "payroll/run_form.html", {"form": form})


@require_payroll_manager
def run_detail(request, pk):
    run = get_object_or_404(
        Payroll.objects.select_related("created_by", "reviewed_by", "approved_by"), pk=pk
    )
    items = run.items.select_related("employee").order_by("employee_name_snapshot", "pk")
    employee_count = items.count()
    total_tax = items.aggregate(total=Sum("tax_amount"))["total"]
    has_demo_facts = items.filter(
        calculation_inputs__attendance_source="mock-attendance-v1"
    ).exists()
    form = BreakdownFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data["search"]:
            term = form.cleaned_data["search"]
            items = items.filter(
                Q(employee_name_snapshot__icontains=term)
                | Q(employee_number_snapshot__icontains=term)
            )
        if form.cleaned_data["department"]:
            items = items.filter(employee__department=form.cleaned_data["department"])
    else:
        items = items.none()
    page = Paginator(items, 25).get_page(request.GET.get("page"))
    payslip_ids = set(
        services.published_payslip_items().filter(payroll=run).values_list("pk", flat=True)
    )
    for item in page:
        item.payslip_available = item.pk in payslip_ids
    return render(
        request,
        "payroll/run_detail.html",
        {
            "run": run,
            "items": page,
            "page_obj": page,
            "form": form,
            "employee_count": employee_count,
            "total_tax": total_tax,
            "has_demo_facts": has_demo_facts,
        },
    )


# --- Payroll status transitions (HRF-25, HRF-27, HRF-28) ----------------


@require_payroll_manager
def run_calculate(request, pk):
    run = get_object_or_404(Payroll, pk=pk)
    if request.method == "POST":
        try:
            services.calculate_payroll(run, request.user)
        except ValidationError as exc:
            detail = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
            messages.error(request, detail)
        else:
            messages.success(request, "Payroll calculated.")
    return redirect("payroll:run-detail", pk=pk)


@require_payroll_manager
def run_review(request, pk):
    run = get_object_or_404(Payroll, pk=pk)
    if request.method == "POST":
        try:
            services.mark_reviewed(run, request.user)
        except ValidationError as exc:
            messages.error(
                request, " ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc)
            )
        else:
            messages.success(request, "Payroll marked as reviewed.")
    return redirect("payroll:run-detail", pk=pk)


@require_payroll_manager
def run_approve(request, pk):
    run = get_object_or_404(Payroll, pk=pk)
    if request.method == "POST":
        try:
            services.approve_payroll(run, request.user)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(
                request, " ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc)
            )
        else:
            messages.success(request, "Payroll approved.")
    return redirect("payroll:run-detail", pk=pk)


# --- Payslips (HRF-008) ------------------------------------------------


@never_cache
@login_required
@require_safe
def payslip_list(request):
    try:
        items = services.payslip_items_for_user(request.user)
    except PermissionDenied as exc:
        return render(request, "payroll/access_denied.html", {"reason": str(exc)}, status=403)
    form = PayslipFilterForm(request.GET)
    if not services.user_in_groups(request.user, services.PAYROLL_MANAGER_GROUPS):
        del form.fields["department"]
        del form.fields["search"]
    if form.is_valid():
        data = form.cleaned_data
        for field in ("month", "year", "status"):
            if data[field]:
                items = items.filter(**{"payroll__" + field: data[field]})
        if data.get("department"):
            items = items.filter(employee__department=data["department"])
        if data.get("search"):
            items = items.filter(
                Q(employee_name_snapshot__icontains=data["search"])
                | Q(employee_number_snapshot__icontains=data["search"])
            )
    else:
        items = items.none()
    return render(
        request,
        "payroll/payslip_list.html",
        {
            "form": form,
            "page_obj": Paginator(items, 25).get_page(request.GET.get("page")),
            "is_payroll_manager": services.user_in_groups(
                request.user, services.PAYROLL_MANAGER_GROUPS
            ),
        },
    )


@never_cache
@login_required
@require_safe
def payslip_detail(request, pk):
    try:
        items = services.payslip_items_for_user(request.user)
    except PermissionDenied as exc:
        return render(request, "payroll/access_denied.html", {"reason": str(exc)}, status=403)
    item = items.filter(pk=pk).first()
    if item is None:
        return render(request, "payroll/payslip_unavailable.html", status=404)
    return render(
        request,
        "payroll/payslip_detail.html",
        {
            "item": item,
            "earnings": [
                ("Basic salary", item.basic_salary),
                ("Allowances", item.allowances),
                ("Overtime", item.overtime_amount),
                ("Bonuses", item.bonus_amount),
            ],
            "deductions": [
                ("Absence", item.absence_deduction),
                ("Unpaid leave", item.unpaid_leave_deduction),
                ("Manual deductions", item.manual_deduction_amount),
                ("Tax", item.tax_amount),
            ],
        },
    )
