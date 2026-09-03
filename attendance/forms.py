from django import forms
from django.db import transaction

from employees.models import Department

from .models import Attendance, LeaveRequest, LeaveType


class AttendanceFilterForm(forms.Form):
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    department = forms.ModelChoiceField(
        required=False, queryset=Department.objects.order_by("name"), empty_label="All departments"
    )
    status = forms.ChoiceField(
        required=False, choices=[("", "All statuses"), *Attendance.STATUS_CHOICES]
    )
    search = forms.CharField(
        required=False,
        max_length=150,
        label="Employee",
        widget=forms.TextInput(attrs={"placeholder": "Name or employee ID"}),
    )


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["employee", "date", "check_in", "check_out", "status", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "check_in": forms.TimeInput(attrs={"type": "time"}),
            "check_out": forms.TimeInput(attrs={"type": "time"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get("employee")
        work_date = cleaned_data.get("date")
        if employee and work_date:
            queryset = Attendance.objects.filter(employee=employee, date=work_date)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError(
                    "An attendance record already exists for this employee on that date."
                )

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.full_clean()
        instance._calculate_worked_hours()
        if commit:
            instance.save()
        return instance


class LeaveTypeForm(forms.ModelForm):
    class Meta:
        model = LeaveType
        fields = ["name", "annual_allowance", "is_paid", "requires_approval", "is_active"]
        widgets = {"name": forms.TextInput(attrs={"placeholder": "Annual Leave"})}

    def clean_name(self):
        return self.cleaned_data["name"].strip()


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["employee", "leave_type", "start_date", "end_date", "reason"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["leave_type"].queryset = LeaveType.objects.filter(is_active=True)

    @transaction.atomic
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.full_clean()
        instance.calculate_requested_days()
        if commit:
            instance.save()
        return instance
