from django import forms

from .models import Attendance, LeaveRequest, LeaveType


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
        check_in = cleaned_data.get("check_in")
        check_out = cleaned_data.get("check_out")

        if check_in and check_out and check_out <= check_in:
            raise forms.ValidationError("Check-out must be after check-in.")

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

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        employee = cleaned_data.get("employee")

        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date cannot precede start date.")

        if employee and start_date and end_date:
            queryset = LeaveRequest.objects.filter(
                employee=employee,
                status__in=["pending", "approved"],
                start_date__lte=end_date,
                end_date__gte=start_date,
            )
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError(
                    "Pending or approved leave requests may not overlap for the same employee."
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.full_clean()
        instance.calculate_requested_days()
        if commit:
            instance.save()
        return instance
