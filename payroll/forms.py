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
        widgets = {"effective_date": DATE_INPUT}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["effective_date"].initial = date.today


class ManualDeductionForm(forms.ModelForm):
    class Meta:
        model = ManualDeduction
        fields = ["employee", "deduction_type", "amount", "effective_date", "description"]
        widgets = {"effective_date": DATE_INPUT}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["effective_date"].initial = date.today


class TaxBracketForm(forms.ModelForm):
    class Meta:
        model = TaxBracket
        fields = ["name", "min_amount", "max_amount", "percentage", "fixed_amount", "is_active"]


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
