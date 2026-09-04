from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .constants import STAFF_ACCOUNT_ROLES
from .services import create_staff_user, update_staff_user


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
        username_field = get_user_model()._meta.get_field("username")
        try:
            username_field.run_validators(username)
        except ValidationError as exc:
            raise forms.ValidationError(exc.messages) from exc
        if get_user_model().objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def clean_email(self):
        return self.cleaned_data["email"].strip()

    def save(self):
        if not self.is_valid():
            raise ValueError("Cannot save an invalid staff user form.")
        return create_staff_user(**self.cleaned_data)


class StaffUserUpdateForm(forms.Form):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "input"}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "input"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "input"}))
    role = forms.ChoiceField(
        choices=[(role, role) for role in STAFF_ACCOUNT_ROLES],
        widget=forms.Select(attrs={"class": "input"}),
    )

    def __init__(self, *args, user, **kwargs):
        self.user = user
        kwargs.setdefault(
            "initial",
            {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "role": user.groups.filter(name__in=STAFF_ACCOUNT_ROLES)
                .values_list("name", flat=True)
                .first(),
            },
        )
        super().__init__(*args, **kwargs)

    def clean_email(self):
        return self.cleaned_data["email"].strip()

    def save(self):
        if not self.is_valid():
            raise ValueError("Cannot save an invalid staff user form.")
        return update_staff_user(self.user, **self.cleaned_data)
