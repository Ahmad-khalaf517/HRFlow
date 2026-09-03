from django.urls import path

from . import views

app_name = "payroll"

urlpatterns = [
    path("bonuses/", views.bonus_list, name="bonus-list"),
    path("bonuses/new/", views.bonus_create, name="bonus-create"),
    path("bonuses/<int:pk>/edit/", views.bonus_update, name="bonus-update"),
    path("bonuses/<int:pk>/cancel/", views.bonus_cancel, name="bonus-cancel"),
    path("deductions/", views.deduction_list, name="deduction-list"),
    path("deductions/new/", views.deduction_create, name="deduction-create"),
    path("deductions/<int:pk>/cancel/", views.deduction_cancel, name="deduction-cancel"),
    path("tax-brackets/", views.tax_bracket_list, name="tax-bracket-list"),
    path("tax-brackets/new/", views.tax_bracket_create, name="tax-bracket-create"),
    path("tax-brackets/<int:pk>/toggle/", views.tax_bracket_toggle, name="tax-bracket-toggle"),
    path("runs/", views.run_list, name="run-list"),
    path("runs/new/", views.run_create, name="run-create"),
    path("runs/<int:pk>/", views.run_detail, name="run-detail"),
    path("runs/<int:pk>/calculate/", views.run_calculate, name="run-calculate"),
    path("runs/<int:pk>/review/", views.run_review, name="run-review"),
    path("runs/<int:pk>/approve/", views.run_approve, name="run-approve"),
]
