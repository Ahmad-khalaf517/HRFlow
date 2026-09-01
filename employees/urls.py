from django.urls import path

from .views import (

    # Departments
    DepartmentCreateView,
    DepartmentDeactivateView,
    DepartmentDetailView,
    DepartmentListView,
    DepartmentUpdateView,

    # Employees
    EmployeeCreateView,
    EmployeeDeactivateView,
    EmployeeDetailView,
    EmployeeListView,
    EmployeeReactivateView,
    EmployeeTerminateView,
    EmployeeUpdateView,

    # Positions
    PositionCreateView,
    PositionDeactivateView,
    PositionDetailView,
    PositionListView,
    PositionUpdateView,

    # Contracts
    ContractCreateView,
    ContractDeactivateView,
    ContractDetailView,
    ContractListView,
    ContractReactivateView,
    ContractTerminateView,
    ContractUpdateView,
)


app_name = "employees"


urlpatterns = [

    # ==========================================
    # DEPARTMENTS
    # ==========================================

    path(
        "departments/",
        DepartmentListView.as_view(),
        name="department-list",
    ),

    path(
        "departments/create/",
        DepartmentCreateView.as_view(),
        name="department-create",
    ),

    path(
        "departments/<int:pk>/",
        DepartmentDetailView.as_view(),
        name="department-detail",
    ),

    path(
        "departments/<int:pk>/edit/",
        DepartmentUpdateView.as_view(),
        name="department-update",
    ),

    path(
        "departments/<int:pk>/deactivate/",
        DepartmentDeactivateView.as_view(),
        name="department-deactivate",
    ),


    # ==========================================
    # POSITIONS
    # ==========================================

    path(
        "positions/",
        PositionListView.as_view(),
        name="position-list",
    ),

    path(
        "positions/create/",
        PositionCreateView.as_view(),
        name="position-create",
    ),

    path(
        "positions/<int:pk>/",
        PositionDetailView.as_view(),
        name="position-detail",
    ),

    path(
        "positions/<int:pk>/edit/",
        PositionUpdateView.as_view(),
        name="position-update",
    ),

    path(
        "positions/<int:pk>/deactivate/",
        PositionDeactivateView.as_view(),
        name="position-deactivate",
    ),


    # ==========================================
    # CONTRACTS
    # ==========================================

    path(
        "contracts/",
        ContractListView.as_view(),
        name="contract-list",
    ),

    path(
        "contracts/create/",
        ContractCreateView.as_view(),
        name="contract-create",
    ),

    path(
        "contracts/<int:pk>/",
        ContractDetailView.as_view(),
        name="contract-detail",
    ),

    path(
        "contracts/<int:pk>/edit/",
        ContractUpdateView.as_view(),
        name="contract-update",
    ),

    path(
        "contracts/<int:pk>/deactivate/",
        ContractDeactivateView.as_view(),
        name="contract-deactivate",
    ),

    path(
        "contracts/<int:pk>/reactivate/",
        ContractReactivateView.as_view(),
        name="contract-reactivate",
    ),

    path(
        "contracts/<int:pk>/terminate/",
        ContractTerminateView.as_view(),
        name="contract-terminate",
    ),


    # ==========================================
    # EMPLOYEES
    # ==========================================

    path(
        "",
        EmployeeListView.as_view(),
        name="employee-list",
    ),

    path(
        "create/",
        EmployeeCreateView.as_view(),
        name="employee-create",
    ),

    path(
        "<int:pk>/",
        EmployeeDetailView.as_view(),
        name="employee-detail",
    ),

    path(
        "<int:pk>/edit/",
        EmployeeUpdateView.as_view(),
        name="employee-update",
    ),

    path(
        "<int:pk>/deactivate/",
        EmployeeDeactivateView.as_view(),
        name="employee-deactivate",
    ),

    path(
        "<int:pk>/reactivate/",
        EmployeeReactivateView.as_view(),
        name="employee-reactivate",
    ),

    path(
        "<int:pk>/terminate/",
        EmployeeTerminateView.as_view(),
        name="employee-terminate",
    ),
]