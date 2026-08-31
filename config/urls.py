"""
URL configuration for the HRFlow project.

Per-app URLconfs (accounts, employees, attendance, payroll) are added here
with include() as each app's views land.
"""

from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
]
