from django.contrib import admin

from .models import Attendance, LeaveRequest, LeaveType


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["employee", "date", "status", "worked_hours", "overtime_hours"]
    list_filter = ["status", "date"]
    search_fields = ["employee__employee_number", "employee__first_name", "employee__last_name"]


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "annual_allowance", "is_paid", "requires_approval", "is_active"]


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ["employee", "leave_type", "start_date", "end_date", "requested_days", "status"]
    list_filter = ["status", "leave_type"]
    search_fields = ["employee__employee_number", "employee__first_name", "employee__last_name"]
