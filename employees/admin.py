from django.contrib import admin

from .models import Contract, Department, Employee, Position


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "manager", "created_at"]
    search_fields = ["name"]


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ["title", "department", "is_active"]
    list_filter = ["department", "is_active"]
    search_fields = ["title"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        "employee_number",
        "first_name",
        "last_name",
        "department",
        "position",
        "employment_status",
        "is_active",
    ]
    list_filter = ["department", "position", "employment_status", "is_active"]
    search_fields = ["employee_number", "first_name", "last_name", "email"]


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ["employee", "contract_type", "status", "start_date", "end_date", "basic_salary"]
    list_filter = ["contract_type", "status"]
    search_fields = ["employee__employee_number", "employee__first_name", "employee__last_name"]
