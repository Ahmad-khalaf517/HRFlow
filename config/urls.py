"""
URL configuration for the HRFlow project.

Per-app URLconfs (accounts, employees, attendance, payroll) are added here
with include() as each app's views land.
"""

from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", views.health, name="health"),
    path("accounts/", include("accounts.urls")),
    path("employees/", include("employees.urls")),
    path("attendance/", include("attendance.urls")),
    path("payroll/", include("payroll.urls")),
    path("", views.dashboard, name="home"),
]