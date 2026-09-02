from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from employees.models import Employee

from .forms import AttendanceForm, LeaveRequestForm, LeaveTypeForm
from .models import Attendance, LeaveRequest, LeaveType


def _has_attendance_management_access(user):
    return user.is_authenticated and (
        user.is_staff or user.groups.filter(name__in=["Admin", "HR Manager"]).exists()
    )


def _has_attendance_view_access(user):
    return user.is_authenticated and (
        _has_attendance_management_access(user)
        or user.groups.filter(name="Payroll Officer").exists()
    )


def _can_access_employee_records(user, employee):
    if _has_attendance_view_access(user):
        return True
    return user.is_authenticated and employee.user_id == user.pk


def _has_leave_management_access(user):
    return user.is_authenticated and (
        user.is_staff or user.groups.filter(name__in=["Admin", "HR Manager"]).exists()
    )


def _has_leave_approval_access(user):
    return _has_leave_management_access(user)


def _has_leave_view_access(user):
    return user.is_authenticated and (
        _has_leave_management_access(user)
        or user.groups.filter(name="Payroll Officer").exists()
    )


def _can_access_leave_request(user, leave_request):
    if _has_leave_view_access(user):
        return True
    return user.is_authenticated and leave_request.employee.user_id == user.pk


def _status_counts(queryset, statuses):
    counts = dict(
        queryset.values("status").annotate(total=Count("id")).values_list("status", "total")
    )
    return {status: counts.get(status, 0) for status in statuses}


@login_required
def attendance_summary(request):
    if not _has_attendance_view_access(request.user):
        employee = get_object_or_404(Employee, user=request.user)
        queryset = Attendance.objects.filter(employee=employee).order_by("-date")
    else:
        queryset = Attendance.objects.select_related("employee").order_by("-date")

    present_days = queryset.filter(status="present").count()
    absent_days = queryset.filter(status="absent").count()
    total_worked_hours = (
        queryset.aggregate(total=Sum("worked_hours"))["total"] or Decimal("0.00")
    )
    total_overtime_hours = (
        queryset.aggregate(total=Sum("overtime_hours"))["total"] or Decimal("0.00")
    )

    return render(
        request,
        "attendance/attendance_summary.html",
        {
            "attendance_records": queryset,
            "total_records": queryset.count(),
            "present_days": present_days,
            "absent_days": absent_days,
            "total_worked_hours": total_worked_hours,
            "total_overtime_hours": total_overtime_hours,
        },
    )


@login_required
def attendance_list(request):
    base_queryset = Attendance.objects.select_related("employee").order_by("-date")

    if not _has_attendance_view_access(request.user):
        base_queryset = base_queryset.filter(employee__user=request.user)

    status = request.GET.get("status", "").strip()
    date_filter = request.GET.get("date", "").strip()

    queryset = base_queryset
    if status:
        queryset = queryset.filter(status=status)
    if date_filter:
        queryset = queryset.filter(date=date_filter)

    return render(
        request,
        "attendance/attendance_list.html",
        {
            "attendance_records": queryset,
            "status_counts": _status_counts(
                base_queryset, ["present", "late", "absent", "leave"]
            ),
            "status_choices": Attendance.STATUS_CHOICES,
            "selected_status": status,
            "selected_date": date_filter,
        },
    )


@login_required
def my_attendance(request):
    employee = get_object_or_404(Employee, user=request.user)
    base_queryset = Attendance.objects.filter(employee=employee).order_by("-date")

    status = request.GET.get("status", "").strip()
    date_filter = request.GET.get("date", "").strip()

    queryset = base_queryset
    if status:
        queryset = queryset.filter(status=status)
    if date_filter:
        queryset = queryset.filter(date=date_filter)

    return render(
        request,
        "attendance/attendance_list.html",
        {
            "attendance_records": queryset,
            "status_counts": _status_counts(
                base_queryset, ["present", "late", "absent", "leave"]
            ),
            "status_choices": Attendance.STATUS_CHOICES,
            "selected_status": status,
            "selected_date": date_filter,
            "title": "My Attendance",
        },
    )


@login_required
def attendance_detail(request, pk):
    attendance = get_object_or_404(Attendance.objects.select_related("employee"), pk=pk)
    if not _can_access_employee_records(request.user, attendance.employee):
        raise Http404
    return render(request, "attendance/attendance_detail.html", {"attendance": attendance})


@login_required
def attendance_form(request):
    employee_profile = getattr(request.user, "employee_profile", None)
    employee_profile_id = employee_profile.pk if employee_profile else None

    if request.method == "POST":
        form = AttendanceForm(request.POST)
        if _has_attendance_management_access(request.user):
            employee = form.data.get("employee")
            if not employee and employee_profile_id:
                form.fields["employee"].initial = employee_profile_id
        elif employee_profile_id:
            form = AttendanceForm(
                request.POST,
                initial={"employee": employee_profile_id},
            )
            form.fields["employee"].queryset = Employee.objects.filter(pk=employee_profile_id)
        else:
            raise Http404

        if form.is_valid():
            attendance = form.save()
            messages.success(request, "Attendance saved successfully.")
            return redirect("attendance:attendance_detail", pk=attendance.pk)
    else:
        if _has_attendance_management_access(request.user):
            form = AttendanceForm()
        elif employee_profile_id:
            form = AttendanceForm(initial={"employee": employee_profile_id})
            form.fields["employee"].queryset = Employee.objects.filter(pk=employee_profile_id)
        else:
            raise Http404

    return render(request, "attendance/attendance_form.html", {"form": form})


@login_required
def attendance_update(request, pk):
    attendance = get_object_or_404(Attendance.objects.select_related("employee"), pk=pk)
    if not _can_access_employee_records(request.user, attendance.employee):
        raise Http404
    if (
        not _has_attendance_management_access(request.user)
        and attendance.employee.user_id != request.user.pk
    ):
        raise Http404

    if request.method == "POST":
        form = AttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            updated = form.save()
            messages.success(request, "Attendance updated successfully.")
            return redirect("attendance:attendance_detail", pk=updated.pk)
    else:
        form = AttendanceForm(instance=attendance)

    return render(
        request,
        "attendance/attendance_form.html",
        {"form": form, "attendance": attendance},
    )


@login_required
def leave_type_list(request):
    if not _has_leave_management_access(request.user):
        raise Http404
    leave_types = LeaveType.objects.order_by("name")
    return render(request, "attendance/leave_type_list.html", {"leave_types": leave_types})


@login_required
def leave_type_form(request, pk=None):
    if not _has_leave_management_access(request.user):
        raise Http404
    leave_type = get_object_or_404(LeaveType, pk=pk) if pk else None

    if request.method == "POST":
        form = LeaveTypeForm(request.POST, instance=leave_type)
        if form.is_valid():
            leave_type_obj = form.save()
            messages.success(
                request,
                "Leave type updated successfully."
                if leave_type_obj.pk == pk
                else "Leave type created successfully.",
            )
            return redirect("attendance:leave_type_list")
    else:
        form = LeaveTypeForm(instance=leave_type)

    return render(
        request,
        "attendance/leave_type_form.html",
        {"form": form, "leave_type": leave_type},
    )


@login_required
def leave_request_list(request):
    queryset = LeaveRequest.objects.select_related("employee", "leave_type").order_by("-start_date")
    if not _has_leave_view_access(request.user):
        queryset = queryset.filter(employee__user=request.user)
    return render(
        request,
        "attendance/leave_request_list.html",
        {
            "leave_requests": queryset,
            "status_counts": _status_counts(queryset, ["pending", "approved", "rejected"]),
        },
    )


@login_required
def leave_approval_list(request):
    if not _has_leave_approval_access(request.user):
        raise Http404
    queryset = (
        LeaveRequest.objects.select_related("employee", "leave_type")
        .filter(status="pending")
        .order_by("-start_date")
    )
    return render(request, "attendance/leave_approval_list.html", {"leave_requests": queryset})


@login_required
def my_leave_requests(request):
    employee = get_object_or_404(Employee, user=request.user)
    queryset = LeaveRequest.objects.filter(employee=employee).order_by("-start_date")
    return render(
        request,
        "attendance/leave_request_list.html",
        {
            "leave_requests": queryset,
            "status_counts": _status_counts(queryset, ["pending", "approved", "rejected"]),
            "title": "My Leave Requests",
        },
    )


@login_required
def leave_request_create(request):
    employee_profile = getattr(request.user, "employee_profile", None)
    is_manager = request.user.groups.filter(name__in=["Admin", "HR Manager"]).exists()
    if is_manager or request.user.is_staff:
        if request.method == "POST":
            form = LeaveRequestForm(request.POST)
        else:
            form = LeaveRequestForm()
    else:
        if not employee_profile:
            raise Http404
        if request.method == "POST":
            data = request.POST.copy()
            data["employee"] = str(employee_profile.pk)
            form = LeaveRequestForm(data)
        else:
            form = LeaveRequestForm(initial={"employee": employee_profile.pk})
        form.fields["employee"].queryset = Employee.objects.filter(pk=employee_profile.pk)

    if request.method == "POST":
        if form.is_valid():
            leave_request = form.save()
            messages.success(request, "Leave request submitted successfully.")
            return redirect("attendance:leave_request_detail", pk=leave_request.pk)

    return render(request, "attendance/leave_request_form.html", {"form": form})


@login_required
def leave_request_approve(request, pk):
    if not _has_leave_approval_access(request.user):
        raise Http404
    leave_request = get_object_or_404(
        LeaveRequest.objects.select_related("employee", "leave_type"), pk=pk
    )

    if leave_request.status != "pending":
        messages.error(request, "Only pending leave requests can be approved.")
        return redirect("attendance:leave_approval_list")

    leave_request.approve(request.user)
    messages.success(request, "Leave request approved successfully.")
    return redirect("attendance:leave_approval_list")


@login_required
def leave_request_reject(request, pk):
    if not _has_leave_approval_access(request.user):
        raise Http404
    leave_request = get_object_or_404(
        LeaveRequest.objects.select_related("employee", "leave_type"), pk=pk
    )

    if leave_request.status != "pending":
        messages.error(request, "Only pending leave requests can be rejected.")
        return redirect("attendance:leave_approval_list")

    leave_request.reject(request.user)
    messages.success(request, "Leave request rejected successfully.")
    return redirect("attendance:leave_approval_list")


@login_required
def leave_request_detail(request, pk):
    leave_request = get_object_or_404(
        LeaveRequest.objects.select_related("employee", "leave_type"),
        pk=pk,
    )
    if not _can_access_leave_request(request.user, leave_request):
        raise Http404
    return render(
        request,
        "attendance/leave_request_detail.html",
        {"leave_request": leave_request},
    )
