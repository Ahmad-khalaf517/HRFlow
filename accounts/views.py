
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, ListView

from .constants import ACCOUNT_MANAGER_GROUPS, STAFF_ACCOUNT_ROLES
from .forms import StaffUserCreationForm, StaffUserUpdateForm
from .services import clear_must_change_password, set_staff_user_active


def _apply_form_validation_error(form, exc):
    """Map a service-raised ValidationError onto form fields (shared by create/update)."""
    if hasattr(exc, "message_dict"):
        for field, errors in exc.message_dict.items():
            target = None if field == NON_FIELD_ERRORS or field not in form.fields else field
            for error in errors:
                form.add_error(target, error)
    else:
        form.add_error(None, exc)


class AccountManagementRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not request.user.groups.filter(name__in=ACCOUNT_MANAGER_GROUPS).exists():
            return render(
                request,
                "accounts/access_denied.html",
                {"reason": "Only Admin or HR Manager may manage user accounts."},
                status=403,
            )
        return super().dispatch(request, *args, **kwargs)


class StaffUserListView(AccountManagementRequiredMixin, ListView):
    model = get_user_model()
    template_name = "accounts/user_list.html"
    context_object_name = "staff_users"
    paginate_by = 25

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(groups__name__in=STAFF_ACCOUNT_ROLES)
            .prefetch_related("groups")
            .distinct()
            .order_by("first_name", "last_name", "username")
        )


class StaffUserCreateView(AccountManagementRequiredMixin, FormView):
    form_class = StaffUserCreationForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("staff-user-list")

    def form_valid(self, form):
        try:
            user = form.save()
        except ValidationError as exc:
            _apply_form_validation_error(form, exc)
            return self.form_invalid(form)
        messages.success(self.request, f"User account created for {user.get_full_name()}.")
        return super().form_valid(form)


class StaffUserUpdateView(AccountManagementRequiredMixin, View):
    template_name = "accounts/user_form.html"

    def _get_object(self):
        return get_object_or_404(
            get_user_model().objects.filter(groups__name__in=STAFF_ACCOUNT_ROLES).distinct(),
            pk=self.kwargs["pk"],
        )

    def get(self, request, pk):
        user = self._get_object()
        form = StaffUserUpdateForm(user=user)
        return render(request, self.template_name, {"form": form, "staff_user": user})

    def post(self, request, pk):
        user = self._get_object()
        form = StaffUserUpdateForm(request.POST, user=user)
        if form.is_valid():
            try:
                form.save()
            except ValidationError as exc:
                _apply_form_validation_error(form, exc)
            else:
                messages.success(request, f"Updated {user.get_full_name()}.")
                return redirect("staff-user-list")
        return render(request, self.template_name, {"form": form, "staff_user": user})


class StaffUserToggleActiveView(AccountManagementRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(
            get_user_model().objects.filter(groups__name__in=STAFF_ACCOUNT_ROLES).distinct(),
            pk=pk,
        )
        if user == request.user:
            messages.error(request, "You cannot deactivate your own account.")
        else:
            set_staff_user_active(user, is_active=not user.is_active)
            messages.success(
                request,
                f"{user.get_full_name() or user.username} is now "
                f"{'active' if user.is_active else 'inactive'}.",
            )
        return redirect("staff-user-list")


class ForcedPasswordChangeView(auth_views.PasswordChangeView):
    template_name = "accounts/password_change_form.html"
    success_url = reverse_lazy("password_change_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        clear_must_change_password(self.request.user)
        return response


class HRFlowPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")

    def form_valid(self, form):
        response = super().form_valid(form)
        clear_must_change_password(form.user)
        return response
