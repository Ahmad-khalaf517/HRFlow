from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .forms import LoginForm
from .views import (
    ForcedPasswordChangeView,
    HRFlowPasswordResetConfirmView,
    StaffUserCreateView,
    StaffUserListView,
    StaffUserToggleActiveView,
    StaffUserUpdateView,
)

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "password/change/",
        ForcedPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html"
        ),
        name="password_change_done",
    ),
    path(
        "password/reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.txt",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url=reverse_lazy("password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password/reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password/reset/confirm/<uidb64>/<token>/",
        HRFlowPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password/reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("users/", StaffUserListView.as_view(), name="staff-user-list"),
    path("users/new/", StaffUserCreateView.as_view(), name="staff-user-create"),
    path("users/<int:pk>/edit/", StaffUserUpdateView.as_view(), name="staff-user-update"),
    path(
        "users/<int:pk>/toggle-active/",
        StaffUserToggleActiveView.as_view(),
        name="staff-user-toggle-active",
    ),
]
