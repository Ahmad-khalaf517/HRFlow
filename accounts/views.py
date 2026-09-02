
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView

from .constants import ACCOUNT_MANAGER_GROUPS, STAFF_ACCOUNT_ROLES
from .forms import StaffUserCreationForm


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
        user = form.save()
        messages.success(self.request, f"User account created for {user.get_full_name()}.")
        return super().form_valid(form)
