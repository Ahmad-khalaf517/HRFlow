from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import CheckConstraint, Q, UniqueConstraint

# docs/erd.md records the migrated status values. business-rules.md §6 only
# says they're included when "their status is active/approved" — read here as a simple
# active/cancelled toggle, since no approval workflow is otherwise specified for either entity.
# Revisit if a real approval flow is added.
ADJUSTMENT_STATUS_CHOICES = [
    ("active", "Active"),
    ("cancelled", "Cancelled"),
]

LOCKED_PAYROLL_STATUSES = ("approved", "paid")


class Bonus(models.Model):
    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.PROTECT, related_name="bonuses"
    )
    bonus_type = models.CharField(max_length=50, blank=True, default="")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    effective_date = models.DateField()
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=ADJUSTMENT_STATUS_CHOICES, default="active")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bonuses_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-effective_date"]
        constraints = [
            CheckConstraint(
                condition=Q(amount__gte=0),
                name="bonus_amount_gte_0",
                violation_error_message="Amount cannot be negative.",
            )
        ]

    def __str__(self):
        return f"{self.employee} — {self.amount} ({self.effective_date})"


class ManualDeduction(models.Model):
    DEDUCTION_TYPE_CHOICES = [
        ("loan", "Loan"),
        ("insurance", "Insurance"),
        ("advance_repayment", "Advance Repayment"),
        ("disciplinary", "Disciplinary"),
        ("other", "Other"),
    ]

    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.PROTECT, related_name="manual_deductions"
    )
    deduction_type = models.CharField(
        max_length=30, choices=DEDUCTION_TYPE_CHOICES, default="other"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    effective_date = models.DateField()
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=ADJUSTMENT_STATUS_CHOICES, default="active")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="manual_deductions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-effective_date"]
        constraints = [
            CheckConstraint(
                condition=Q(amount__gte=0),
                name="manualdeduction_amount_gte_0",
                violation_error_message="Amount cannot be negative.",
            )
        ]

    # Do not use this model for absence/unpaid-leave deductions — those are derived
    # during payroll processing (docs/business-rules.md §6).
    def __str__(self):
        return f"{self.employee} — {self.get_deduction_type_display()} ({self.amount})"


class TaxBracket(models.Model):
    name = models.CharField(max_length=100)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    fixed_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["min_amount"]
        constraints = [
            CheckConstraint(
                condition=Q(min_amount__gte=0),
                name="taxbracket_min_amount_gte_0",
                violation_error_message="Min amount cannot be negative.",
            ),
            CheckConstraint(
                condition=Q(percentage__gte=0),
                name="taxbracket_percentage_gte_0",
                violation_error_message="Percentage cannot be negative.",
            ),
            CheckConstraint(
                condition=Q(max_amount__isnull=True) | Q(max_amount__gte=models.F("min_amount")),
                name="taxbracket_max_amount_gte_min_amount",
                violation_error_message="Max amount must be greater than or equal to min amount.",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"


class Payroll(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("calculated", "Calculated"),
        ("reviewed", "Reviewed"),
        ("approved", "Approved"),
        ("paid", "Paid"),
    ]

    period_start = models.DateField()
    period_end = models.DateField()
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    total_gross = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_net = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    # Q-002 confirmed in docs/business-rules.md on 2026-09-01.
    currency_code = models.CharField(max_length=3, default="USD")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payrolls_created"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payrolls_reviewed",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payrolls_approved",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-year", "-month"]
        constraints = [
            UniqueConstraint(fields=["month", "year"], name="payroll_unique_month_year"),
        ]

    def __str__(self):
        return f"Payroll {self.month:02d}/{self.year} ({self.get_status_display()})"

    @transaction.atomic
    def save(self, *args, **kwargs):
        previous = type(self).objects.select_for_update().filter(pk=self.pk).first()
        if previous and previous.status in LOCKED_PAYROLL_STATUSES:
            changed = any(
                getattr(previous, field.attname) != getattr(self, field.attname)
                for field in self._meta.concrete_fields
                if field.name != "status"
            )
            # The later payment service may advance approved -> paid without editing amounts.
            allowed_statuses = (previous.status, "paid")
            if changed or self.status not in allowed_statuses:
                raise ValidationError("Approved payroll cannot be edited.")
        return super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        current = type(self).objects.select_for_update().get(pk=self.pk)
        if current.status in LOCKED_PAYROLL_STATUSES:
            raise ValidationError("Approved payroll cannot be deleted.")
        return super().delete(*args, **kwargs)

    @property
    def lifecycle_step(self):
        """0-based index of `status` in STATUS_CHOICES order, for the lifecycle stepper UI."""
        return [choice[0] for choice in self.STATUS_CHOICES].index(self.status)


class PayrollItem(models.Model):
    """One employee's snapshot within one payroll run.

    Historical snapshot — never dynamically recalculated from current
    Employee/Contract values (docs/business-rules.md §7).
    """

    payroll = models.ForeignKey(Payroll, on_delete=models.PROTECT, related_name="items")
    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.PROTECT, related_name="payroll_items"
    )
    # Empty values identify legacy items; migrations must not invent historical inputs.
    contract = models.ForeignKey(
        "employees.Contract", on_delete=models.PROTECT, null=True, blank=True,
        related_name="payroll_items",
    )
    employee_number_snapshot = models.CharField(max_length=30, blank=True, default="")
    employee_name_snapshot = models.CharField(max_length=201, blank=True, default="")
    currency_code = models.CharField(max_length=3, blank=True, default="")
    calculation_version = models.CharField(max_length=50, blank=True, default="")
    # Decimal inputs/rates are strings to preserve precision without JSON floats.
    calculation_inputs = models.JSONField(default=dict, blank=True)
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overtime_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    absence_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    absence_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unpaid_leave_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    unpaid_leave_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    manual_deduction_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["payroll", "employee"]
        constraints = [
            UniqueConstraint(
                fields=["payroll", "employee"], name="payrollitem_unique_payroll_employee"
            ),
            CheckConstraint(
                condition=(
                    Q(basic_salary__gte=0) & Q(allowances__gte=0)
                    & Q(overtime_hours__gte=0) & Q(overtime_amount__gte=0)
                    & Q(bonus_amount__gte=0) & Q(gross_salary__gte=0)
                    & Q(absence_days__gte=0) & Q(absence_deduction__gte=0)
                    & Q(unpaid_leave_days__gte=0) & Q(unpaid_leave_deduction__gte=0)
                    & Q(manual_deduction_amount__gte=0) & Q(tax_amount__gte=0)
                    & Q(total_deductions__gte=0) & Q(net_salary__gte=0)
                ),
                name="payrollitem_nonnegative_values",
            ),
        ]

    def __str__(self):
        return f"{self.employee} — {self.payroll}"

    def _lock_mutable_parents(self):
        parent_ids = {self.payroll_id}
        if self.pk:
            old_parent = type(self).objects.filter(pk=self.pk).values_list(
                "payroll_id", flat=True
            ).first()
            if old_parent:
                parent_ids.add(old_parent)
        parents = Payroll.objects.select_for_update().filter(pk__in=parent_ids).order_by("pk")
        if any(parent.status in LOCKED_PAYROLL_STATUSES for parent in parents):
            raise ValidationError("Approved payroll items cannot be changed.")

    @transaction.atomic
    def save(self, *args, **kwargs):
        self._lock_mutable_parents()
        for field in self._meta.fields:
            if isinstance(field, models.DecimalField) and getattr(self, field.name) < 0:
                raise ValidationError({field.name: "Payroll values cannot be negative."})
        return super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        self._lock_mutable_parents()
        return super().delete(*args, **kwargs)


class Payslip(models.Model):
    payroll_item = models.OneToOneField(
        PayrollItem, on_delete=models.PROTECT, related_name="payslip"
    )
    file = models.FileField(upload_to="payslips/", null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payslip — {self.payroll_item}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    payroll_item = models.ForeignKey(PayrollItem, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=30, blank=True, default="")
    reference_number = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date"]
        constraints = [CheckConstraint(condition=Q(amount__gte=0), name="payment_amount_gte_0")]

    def __str__(self):
        return f"Payment — {self.payroll_item} ({self.amount})"
