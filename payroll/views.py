from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from . import services
from .forms import BonusForm, ManualDeductionForm, PayrollRunForm, TaxBracketForm
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
    return render(request, "payroll/bonus_list.html", {"bonuses": bonuses})


@require_payroll_manager
def bonus_create(request):
    form = BonusForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        bonus = form.save(commit=False)
        bonus.created_by = request.user
        bonus.save()
        messages.success(request, "Bonus recorded.")
        return redirect("payroll:bonus-list")
    return render(request, "payroll/bonus_form.html", {"form": form})


@require_payroll_manager
def bonus_cancel(request, pk):
    if request.method == "POST":
        bonus = get_object_or_404(Bonus, pk=pk)
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
    form = ManualDeductionForm(request.POST or None)
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
    form = TaxBracketForm(request.POST or None)
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
    runs = Payroll.objects.annotate(item_count=Count("items"))
    return render(request, "payroll/run_list.html", {"runs": runs})


@require_payroll_manager
def run_create(request):
    form = PayrollRunForm(request.POST or None)
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
    items = run.items.select_related("employee").order_by("employee__last_name")
    return render(request, "payroll/run_detail.html", {"run": run, "items": items})


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
            messages.error(request, str(exc))
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
            messages.error(request, str(exc))
        else:
            messages.success(request, "Payroll approved.")
    return redirect("payroll:run-detail", pk=pk)
