from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint

# docs/erd.md records the migrated status values. business-rules.md §6 only
# says they're included when "their status is active/approved" — read here as a simple
# active/cancelled toggle, since no approval workflow is otherwise specified for either entity.
# Revisit if a real approval flow is added.
ADJUSTMENT_STATUS_CHOICES = [
    ("active", "Active"),
    ("cancelled", "Cancelled"),
]


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
        constraints = [CheckConstraint(condition=Q(amount__gte=0), name="bonus_amount_gte_0")]

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
            CheckConstraint(condition=Q(amount__gte=0), name="manualdeduction_amount_gte_0")
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
            CheckConstraint(condition=Q(min_amount__gte=0), name="taxbracket_min_amount_gte_0"),
            CheckConstraint(condition=Q(percentage__gte=0), name="taxbracket_percentage_gte_0"),
            CheckConstraint(
                condition=Q(max_amount__isnull=True) | Q(max_amount__gte=models.F("min_amount")),
                name="taxbracket_max_amount_gte_min_amount",
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
    # Q-002 (docs/business-rules.md §1) is still unresolved; USD is the doc's own recommended
    # default, used here only as the field default, not a confirmed policy decision.
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


class PayrollItem(models.Model):
    """One employee's snapshot within one payroll run.

    Historical snapshot — never dynamically recalculated from current
    Employee/Contract values (docs/business-rules.md §7).
    """

    payroll = models.ForeignKey(Payroll, on_delete=models.PROTECT, related_name="items")
    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.PROTECT, related_name="payroll_items"
    )
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
        ]

    def __str__(self):
        return f"{self.employee} — {self.payroll}"


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
