from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint


class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, default="")

    manager = models.ForeignKey(
        "Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="departments_managed",
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    
class Position(models.Model):

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="positions",
    )

    title = models.CharField(
        max_length=150,
    )

    code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    min_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )

    max_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "department",
                    "title",
                ],
                name="unique_position_title_per_department",
            )
        ]

    def __str__(self):
        return (
            f"{self.title} "
            f"({self.department.name})"
        )

class Employee(models.Model):
    EMPLOYMENT_STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("terminated", "Terminated"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employee_profile",
    )
    employee_number = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True, default="")
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, default="")
    hire_date = models.DateField()
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="employees"
    )
    position = models.ForeignKey(
        Position, null=True, blank=True, on_delete=models.SET_NULL, related_name="employees"
    )
    employment_status = models.CharField(
        max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default="active"
    )
    # MVP uses synthetic bank values only — see docs/security-and-data-policy.md.
    bank_name = models.CharField(max_length=150, blank=True, default="")
    bank_account_number = models.CharField(max_length=50, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.employee_number} — {self.first_name} {self.last_name}"


class Contract(models.Model):
    CONTRACT_TYPE_CHOICES = [
        ("full_time", "Full-time"),
        ("part_time", "Part-time"),
        ("contract", "Contract"),
        ("probation", "Probation"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("terminated", "Terminated"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="contracts")
    contract_type = models.CharField(
        max_length=30, choices=CONTRACT_TYPE_CHOICES, default="full_time"
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances_default = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    working_hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=8)
    working_days_per_week = models.PositiveSmallIntegerField(default=5)
    probation_end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            # docs/business-rules.md §4: only one contract may be marked active per employee.
            UniqueConstraint(
                fields=["employee"],
                condition=Q(status="active"),
                name="contract_one_active_per_employee",
            ),
            CheckConstraint(
                condition=Q(end_date__isnull=True) | Q(end_date__gte=F("start_date")),
                name="contract_end_date_not_before_start_date",
            ),
            CheckConstraint(condition=Q(basic_salary__gte=0), name="contract_basic_salary_gte_0"),
        ]

    def __str__(self):
        return f"{self.employee} — {self.get_status_display()} ({self.start_date})"
