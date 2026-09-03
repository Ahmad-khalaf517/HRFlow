from datetime import date

from django import forms

from .models import Bonus, ManualDeduction, Payroll, TaxBracket

# Explicit ISO format: the "type": "date" widget requires yyyy-mm-dd in its
# value attribute regardless of locale, or a pre-filled initial won't show.
DATE_INPUT = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")

MONTH_CHOICES = [
    (1, "January"), (2, "February"), (3, "March"), (4, "April"),
    (5, "May"), (6, "June"), (7, "July"), (8, "August"),
    (9, "September"), (10, "October"), (11, "November"), (12, "December"),
]


class BonusForm(forms.ModelForm):
    class Meta:
        model = Bonus
        fields = ["employee", "bonus_type", "amount", "effective_date", "description"]
        widgets = {
            "effective_date": DATE_INPUT,
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["effective_date"].initial = date.today

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount < 0:
            raise forms.ValidationError("Amount cannot be negative.")
        return amount


class ManualDeductionForm(forms.ModelForm):
    class Meta:
        model = ManualDeduction
        fields = ["employee", "deduction_type", "amount", "effective_date", "description"]
        widgets = {
            "effective_date": DATE_INPUT,
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["effective_date"].initial = date.today

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount < 0:
            raise forms.ValidationError("Amount cannot be negative.")
        return amount


class TaxBracketForm(forms.ModelForm):
    class Meta:
        model = TaxBracket
        fields = ["name", "min_amount", "max_amount", "percentage", "fixed_amount", "is_active"]
        widgets = {
            "min_amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "max_amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "percentage": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "fixed_amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def clean_min_amount(self):
        min_amount = self.cleaned_data.get("min_amount")
        if min_amount is not None and min_amount < 0:
            raise forms.ValidationError("Min amount cannot be negative.")
        return min_amount

    def clean_percentage(self):
        percentage = self.cleaned_data.get("percentage")
        if percentage is not None and percentage < 0:
            raise forms.ValidationError("Percentage cannot be negative.")
        return percentage

    def clean(self):
        cleaned = super().clean()
        min_amount = cleaned.get("min_amount")
        max_amount = cleaned.get("max_amount")
        if min_amount is not None and max_amount is not None and max_amount < min_amount:
            self.add_error(
                "max_amount", "Max amount must be greater than or equal to min amount."
            )
        return cleaned


class PayrollRunForm(forms.Form):
    month = forms.TypedChoiceField(choices=MONTH_CHOICES, coerce=int)
    year = forms.IntegerField(min_value=2000, max_value=2100)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        self.fields["month"].initial = today.month
        self.fields["year"].initial = today.year

    def clean(self):
        cleaned = super().clean()
        month, year = cleaned.get("month"), cleaned.get("year")
        if month and year and Payroll.objects.filter(month=month, year=year).exists():
            raise forms.ValidationError(f"A payroll run already exists for {month:02d}/{year}.")
        return cleaned
