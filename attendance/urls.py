from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.attendance_list, name="attendance_list"),
    path("summary/", views.attendance_summary, name="attendance_summary"),
    path("mine/", views.my_attendance, name="my_attendance"),
    path("new/", views.attendance_form, name="attendance_create"),
    path("<int:pk>/", views.attendance_detail, name="attendance_detail"),
    path("<int:pk>/edit/", views.attendance_update, name="attendance_update"),
    path("leave-types/", views.leave_type_list, name="leave_type_list"),
    path("leave-types/new/", views.leave_type_form, name="leave_type_create"),
    path("leave-types/<int:pk>/edit/", views.leave_type_form, name="leave_type_update"),
    path("leave-requests/", views.leave_request_list, name="leave_request_list"),
    path("leave-requests/mine/", views.my_leave_requests, name="my_leave_requests"),
    path("leave-requests/new/", views.leave_request_create, name="leave_request_create"),
    path("leave-requests/approval/", views.leave_approval_list, name="leave_approval_list"),
    path(
        "leave-requests/<int:pk>/approve/",
        views.leave_request_approve,
        name="leave_request_approve",
    ),
    path(
        "leave-requests/<int:pk>/reject/",
        views.leave_request_reject,
        name="leave_request_reject",
    ),
    path("leave-requests/<int:pk>/", views.leave_request_detail, name="leave_request_detail"),
]
