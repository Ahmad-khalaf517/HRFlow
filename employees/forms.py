from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import Contract, Department, Employee, Position


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = [
            "name",
            "description",
            "manager",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter department name",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Enter department description",
                    "rows": 4,
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "manager": forms.Select(
                attrs={
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()

        if not name:
            return name

        departments = Department.objects.filter(name__iexact=name)

        if self.instance.pk:
            departments = departments.exclude(pk=self.instance.pk)

        if departments.exists():
            raise ValidationError(
                "A department with this name already exists."
            )

        return name


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position

        fields = [
            "department",
            "title",
            "code",
            "description",
            "min_salary",
            "max_salary",
        ]

        widgets = {
            "department": forms.Select(
                attrs={
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Enter position title",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "code": forms.TextInput(
                attrs={
                    "placeholder": "Optional position code",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Enter position description",
                    "rows": 4,
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "min_salary": forms.NumberInput(
                attrs={
                    "placeholder": "Minimum salary",
                    "step": "0.01",
                    "min": "0",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "max_salary": forms.NumberInput(
                attrs={
                    "placeholder": "Maximum salary",
                    "step": "0.01",
                    "min": "0",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        department = cleaned_data.get("department")
        title = cleaned_data.get("title", "").strip()
        min_salary = cleaned_data.get("min_salary")
        max_salary = cleaned_data.get("max_salary")

        for field, value in (("min_salary", min_salary), ("max_salary", max_salary)):
            if value is not None and value < 0:
                self.add_error(field, "Salary cannot be negative.")

        if department and title:
            positions = Position.objects.filter(
                department=department,
                title__iexact=title,
            )

            if self.instance.pk:
                positions = positions.exclude(pk=self.instance.pk)

            if positions.exists():
                self.add_error(
                    "title",
                    "A position with this title already exists in this department.",
                )

        if (
            min_salary is not None
            and max_salary is not None
            and min_salary > max_salary
        ):
            self.add_error(
                "max_salary",
                "Maximum salary must be greater than or equal to minimum salary.",
            )

        return cleaned_data

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee

        fields = [
            "employee_number",
            "first_name",
            "last_name",
            "email",
            "phone",
            "date_of_birth",
            "address",
            "hire_date",
            "department",
            "position",
            "employment_status",
            "bank_name",
            "bank_account_number",
        ]

        widgets = {
            "employee_number": forms.TextInput(
                attrs={
                    "placeholder": "EMP-001",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "placeholder": "First name",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "placeholder": "Last name",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "employee@example.com",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "placeholder": "Phone number",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "placeholder": "Address",
                    "rows": 3,
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "hire_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "department": forms.Select(
                attrs={
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "position": forms.Select(
                attrs={
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "employment_status": forms.Select(
                attrs={
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "bank_name": forms.TextInput(
                attrs={
                    "placeholder": "Bank name",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "bank_account_number": forms.TextInput(
                attrs={
                    "placeholder": "Bank account number",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
        }

    def clean_employee_number(self):
        employee_number = self.cleaned_data.get(
            "employee_number",
            ""
        ).strip()

        if not employee_number:
            return employee_number

        for validator in get_user_model()._meta.get_field("username").validators:
            validator(employee_number)

        employees = Employee.objects.filter(
            employee_number__iexact=employee_number
        )

        if self.instance.pk:
            employees = employees.exclude(pk=self.instance.pk)

        if employees.exists():
            raise ValidationError(
                "An employee with this employee number already exists."
            )

        users = get_user_model().objects.filter(username__iexact=employee_number)
        if self.instance.user_id:
            users = users.exclude(pk=self.instance.user_id)
        if users.exists():
            raise ValidationError(
                "A user with this employee number already exists."
            )

        return employee_number

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if Employee.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("An employee with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()

        department = cleaned_data.get("department")
        position = cleaned_data.get("position")

        if position:
            if not department or position.department_id != department.id:
                self.add_error(
                    "position",
                    "The selected position does not belong to the selected department.",
                )

        return cleaned_data

    def save(self, commit=True):
        employee = super().save(commit=False)
        employee.is_active = employee.employment_status == "active"
        if commit:
            employee.save()
            self.save_m2m()
        return employee


class EmployeeFilterForm(forms.Form):
    search = forms.CharField(required=False, max_length=150, label="Search",
                             widget=forms.TextInput(attrs={"placeholder": "Name, ID, or email"}))
    department = forms.ModelChoiceField(
        required=False, queryset=Department.objects.order_by("name"), empty_label="All departments"
    )
    status = forms.ChoiceField(
        required=False, choices=[("", "All statuses"), *Employee.EMPLOYMENT_STATUS_CHOICES]
    )
    contract_type = forms.ChoiceField(
        required=False, choices=[("", "All contract types"), *Contract.CONTRACT_TYPE_CHOICES]
    )

class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract

        fields = [
            "employee",
            "contract_type",
            "start_date",
            "end_date",
            "basic_salary",
            "allowances_default",
            "working_hours_per_day",
            "working_days_per_week",
            "probation_end_date",
            "status",
        ]

        widgets = {
            "employee": forms.Select(
                attrs={
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "contract_type": forms.Select(
                attrs={
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "start_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "basic_salary": forms.NumberInput(
                attrs={
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "allowances_default": forms.NumberInput(
                attrs={
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "working_hours_per_day": forms.NumberInput(
                attrs={
                    "placeholder": "8",
                    "step": "0.01",
                    "min": "0",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "working_days_per_week": forms.NumberInput(
                attrs={
                    "min": "1",
                    "max": "7",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "probation_end_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "w-full rounded border border-outline-variant px-3 py-2",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        employee = cleaned_data.get("employee")
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        basic_salary = cleaned_data.get("basic_salary")
        allowances_default = cleaned_data.get("allowances_default")
        working_hours_per_day = cleaned_data.get("working_hours_per_day")
        working_days_per_week = cleaned_data.get("working_days_per_week")
        status = cleaned_data.get("status")

        # Validate contract dates.
        if start_date and end_date and end_date < start_date:
            self.add_error(
                "end_date",
                "End date cannot be before the start date.",
            )

        # Validate salary.
        if basic_salary is not None and basic_salary < 0:
            self.add_error(
                "basic_salary",
                "Basic salary cannot be negative.",
            )

        # Validate allowances.
        if allowances_default is not None and allowances_default < 0:
            self.add_error(
                "allowances_default",
                "Allowances cannot be negative.",
            )

        # Validate working hours.
        if (
            working_hours_per_day is not None
            and working_hours_per_day <= 0
        ):
            self.add_error(
                "working_hours_per_day",
                "Working hours per day must be greater than zero.",
            )

        # Validate working days.
        if (
            working_days_per_week is not None
            and not 1 <= working_days_per_week <= 7
        ):
            self.add_error(
                "working_days_per_week",
                "Working days per week must be between 1 and 7.",
            )

        # Only one active contract per employee.
        if employee and status == "active":
            active_contracts = Contract.objects.filter(
                employee=employee,
                status="active",
            )

            if self.instance.pk:
                active_contracts = active_contracts.exclude(
                    pk=self.instance.pk
                )

            if active_contracts.exists():
                self.add_error(
                    "employee",
                    "This employee already has an active contract.",
                )

        return cleaned_data
