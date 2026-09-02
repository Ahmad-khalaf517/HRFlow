from django.contrib import admin

from .models import Bonus, ManualDeduction, Payment, Payroll, PayrollItem, Payslip, TaxBracket


@admin.register(Bonus)
class BonusAdmin(admin.ModelAdmin):
    list_display = ["employee", "bonus_type", "amount", "effective_date", "status"]
    list_filter = ["status"]
    search_fields = ["employee__employee_number", "employee__first_name", "employee__last_name"]


@admin.register(ManualDeduction)
class ManualDeductionAdmin(admin.ModelAdmin):
    list_display = ["employee", "deduction_type", "amount", "effective_date", "status"]
    list_filter = ["deduction_type", "status"]
    search_fields = ["employee__employee_number", "employee__first_name", "employee__last_name"]


@admin.register(TaxBracket)
class TaxBracketAdmin(admin.ModelAdmin):
    list_display = ["name", "min_amount", "max_amount", "percentage", "fixed_amount", "is_active"]


class PayrollRecordAdmin(admin.ModelAdmin):
    """Payroll records are maintained by their guarded workflow services."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Payroll)
class PayrollAdmin(PayrollRecordAdmin):
    list_display = ["month", "year", "status", "total_gross", "total_deductions", "total_net"]
    list_filter = ["status", "year"]


@admin.register(PayrollItem)
class PayrollItemAdmin(PayrollRecordAdmin):
    list_display = ["payroll", "employee", "gross_salary", "total_deductions", "net_salary"]
    search_fields = ["employee__employee_number", "employee__first_name", "employee__last_name"]


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ["payroll_item", "generated_at"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["payroll_item", "amount", "payment_date", "status"]
    list_filter = ["status"]
