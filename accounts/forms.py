from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

from .constants import STAFF_ACCOUNT_ROLES
from .services import create_staff_user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"})
    )


class StaffUserCreationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "input", "autocomplete": "off", "placeholder": "hr.manager"}
        ),
    )
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "input"}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "input"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "input"}))
    role = forms.ChoiceField(
        choices=[(role, role) for role in STAFF_ACCOUNT_ROLES],
        widget=forms.Select(attrs={"class": "input"}),
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if get_user_model().objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def save(self):
        if not self.is_valid():
            raise ValueError("Cannot save an invalid staff user form.")
        return create_staff_user(**self.cleaned_data)
