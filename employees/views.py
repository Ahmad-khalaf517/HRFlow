from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import (
    ContractForm,
    DepartmentForm,
    EmployeeForm,
    PositionForm,
)
from .models import (
    Contract,
    Department,
    Employee,
    Position,
)

# ==========================================
# PERMISSIONS
# ==========================================

class HRManagementRequiredMixin(LoginRequiredMixin):
    """
    Allow only Admin and HR Manager users
    to access management actions.
    """

    allowed_groups = ["Admin", "HR Manager"]

    def dispatch(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if not request.user.groups.filter(
            name__in=self.allowed_groups
        ).exists():

            return render(
                request,
                "employees/access_denied.html",
                {"reason": "Only Admin or HR Manager may perform this action."},
                status=403,
            )

        return super().dispatch(request, *args, **kwargs)


# ==========================================
# DEPARTMENTS
# ==========================================

class DepartmentListView(LoginRequiredMixin, ListView):

    model = Department
    template_name = "employees/department_list.html"
    context_object_name = "departments"
    paginate_by = 10

    def get_queryset(self):

        queryset = Department.objects.select_related(
            "manager"
        ).all()

        search = self.request.GET.get(
            "search",
            ""
        ).strip()

        status = self.request.GET.get(
            "status",
            ""
        ).strip()

        if search:

            queryset = queryset.filter(
                name__icontains=search
            )

        if status == "active":

            queryset = queryset.filter(
                is_active=True
            )

        elif status == "inactive":

            queryset = queryset.filter(
                is_active=False
            )

        return queryset


class DepartmentDetailView(LoginRequiredMixin, DetailView):

    model = Department
    template_name = "employees/department_detail.html"
    context_object_name = "department"

    def get_queryset(self):

        return Department.objects.select_related(
            "manager"
        )


class DepartmentCreateView(
    HRManagementRequiredMixin,
    SuccessMessageMixin,
    CreateView,
):

    model = Department
    form_class = DepartmentForm
    template_name = "employees/department_form.html"
    success_message = "Department created."

    success_url = reverse_lazy(
        "employees:department-list"
    )


class DepartmentUpdateView(
    HRManagementRequiredMixin,
    SuccessMessageMixin,
    UpdateView,
):

    model = Department
    form_class = DepartmentForm
    template_name = "employees/department_form.html"
    success_message = "Department updated."

    success_url = reverse_lazy(
        "employees:department-list"
    )


class DepartmentDeactivateView(
    HRManagementRequiredMixin,
    View,
):

    """
    Deactivate a department using POST only.
    """

    def post(self, request, pk, *args, **kwargs):

        department = get_object_or_404(
            Department,
            pk=pk,
        )

        department.is_active = False

        department.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        messages.success(request, "Department deactivated.")

        return redirect(
            "employees:department-list"
        )

    def get(self, request, *args, **kwargs):

        return HttpResponseNotAllowed(
            ["POST"]
        )


# ==========================================
# EMPLOYEES
# ==========================================

class EmployeeListView(LoginRequiredMixin, ListView):

    model = Employee
    template_name = "employees/employee_list.html"
    context_object_name = "employees"
    paginate_by = 10

    def get_queryset(self):

        queryset = Employee.objects.select_related(
            "department",
            "position",
        ).all()

        search = self.request.GET.get(
            "search",
            ""
        ).strip()

        department_id = self.request.GET.get(
            "department",
            ""
        ).strip()

        status = self.request.GET.get(
            "status",
            ""
        ).strip()

        # Search employee number, name, or email.
        if search:

            queryset = queryset.filter(

                Q(employee_number__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)

            )

        # Filter by department.
        if department_id.isdigit():

            queryset = queryset.filter(
                department_id=department_id
            )

        # Filter by employment status.
        if status:

            queryset = queryset.filter(
                employment_status=status
            )

        return queryset

    def get_context_data(self, **kwargs):

        context = super().get_context_data(
            **kwargs
        )

        context["departments"] = Department.objects.filter(
            is_active=True
        ).order_by(
            "name"
        )

        context["status_choices"] = (
            Employee.EMPLOYMENT_STATUS_CHOICES
        )

        return context


class EmployeeCreateView(
    HRManagementRequiredMixin,
    SuccessMessageMixin,
    CreateView,
):

    model = Employee
    form_class = EmployeeForm
    template_name = "employees/employee_form.html"
    success_message = "Employee created."

    success_url = reverse_lazy(
        "employees:employee-list"
    )


class EmployeeDetailView(
    LoginRequiredMixin,
    DetailView,
):

    model = Employee
    template_name = "employees/employee_detail.html"
    context_object_name = "employee"

    def get_queryset(self):

        return Employee.objects.select_related(
            "department",
            "position",
            "user",
        )


class EmployeeUpdateView(
    HRManagementRequiredMixin,
    SuccessMessageMixin,
    UpdateView,
):

    model = Employee
    form_class = EmployeeForm
    template_name = "employees/employee_form.html"
    success_message = "Employee updated."

    def get_success_url(self):

        return reverse_lazy(

            "employees:employee-detail",

            kwargs={
                "pk": self.object.pk,
            },

        )


class EmployeeDeactivateView(
    HRManagementRequiredMixin,
    View,
):

    """
    Deactivate an employee using POST only.
    """

    def post(self, request, pk, *args, **kwargs):

        employee = get_object_or_404(
            Employee,
            pk=pk,
        )

        employee.employment_status = "inactive"
        employee.is_active = False

        employee.save(
            update_fields=[
                "employment_status",
                "is_active",
                "updated_at",
            ]
        )

        messages.success(request, "Employee deactivated.")

        return redirect(

            "employees:employee-detail",

            pk=employee.pk,

        )

    def get(self, request, *args, **kwargs):

        return HttpResponseNotAllowed(
            ["POST"]
        )


class EmployeeReactivateView(
    HRManagementRequiredMixin,
    View,
):

    """
    Reactivate an employee using POST only.
    """

    def post(self, request, pk, *args, **kwargs):

        employee = get_object_or_404(
            Employee,
            pk=pk,
        )

        employee.employment_status = "active"
        employee.is_active = True

        employee.save(
            update_fields=[
                "employment_status",
                "is_active",
                "updated_at",
            ]
        )

        messages.success(request, "Employee reactivated.")

        return redirect(

            "employees:employee-detail",

            pk=employee.pk,

        )

    def get(self, request, *args, **kwargs):

        return HttpResponseNotAllowed(
            ["POST"]
        )


class EmployeeTerminateView(
    HRManagementRequiredMixin,
    View,
):

    """
    Terminate an employee using POST only.
    """

    def post(self, request, pk, *args, **kwargs):

        employee = get_object_or_404(
            Employee,
            pk=pk,
        )

        employee.employment_status = "terminated"
        employee.is_active = False

        employee.save(
            update_fields=[
                "employment_status",
                "is_active",
                "updated_at",
            ]
        )

        messages.success(request, "Employee terminated.")

        return redirect(

            "employees:employee-detail",

            pk=employee.pk,

        )

    def get(self, request, *args, **kwargs):

        return HttpResponseNotAllowed(
            ["POST"]
        )


# ==========================================
# POSITIONS
# ==========================================

class PositionListView(LoginRequiredMixin, ListView):

    model = Position
    template_name = "employees/position_list.html"
    context_object_name = "positions"
    paginate_by = 10

    def get_queryset(self):

        queryset = Position.objects.select_related(
            "department"
        ).all()

        search = self.request.GET.get(
            "search",
            ""
        ).strip()

        department_id = self.request.GET.get(
            "department",
            ""
        ).strip()

        status = self.request.GET.get(
            "status",
            ""
        ).strip()

        # Search position title or code.
        if search:

            queryset = queryset.filter(

                Q(title__icontains=search)
                | Q(code__icontains=search)

            )

        # Filter by department.
        if department_id.isdigit():

            queryset = queryset.filter(
                department_id=department_id
            )

        # Filter by status.
        if status == "active":

            queryset = queryset.filter(
                is_active=True
            )

        elif status == "inactive":

            queryset = queryset.filter(
                is_active=False
            )

        return queryset.order_by(
            "department__name",
            "title",
        )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(
            **kwargs
        )

        context["departments"] = Department.objects.filter(
            is_active=True
        ).order_by(
            "name"
        )

        return context


class PositionDetailView(
    LoginRequiredMixin,
    DetailView,
):

    model = Position
    template_name = "employees/position_detail.html"
    context_object_name = "position"

    def get_queryset(self):

        return Position.objects.select_related(
            "department"
        )


class PositionCreateView(
    HRManagementRequiredMixin,
    SuccessMessageMixin,
    CreateView,
):

    model = Position
    form_class = PositionForm
    template_name = "employees/position_form.html"
    success_message = "Position created."

    success_url = reverse_lazy(
        "employees:position-list"
    )


class PositionUpdateView(
    HRManagementRequiredMixin,
    SuccessMessageMixin,
    UpdateView,
):

    model = Position
    form_class = PositionForm
    template_name = "employees/position_form.html"
    success_message = "Position updated."

    success_url = reverse_lazy(
        "employees:position-list"
    )


class PositionDeactivateView(
    HRManagementRequiredMixin,
    View,
):

    """
    Deactivate a position using POST only.
    """

    def post(self, request, pk, *args, **kwargs):

        position = get_object_or_404(
            Position,
            pk=pk,
        )

        position.is_active = False

        position.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        messages.success(request, "Position deactivated.")

        return redirect(
            "employees:position-list"
        )

    def get(self, request, *args, **kwargs):

        return HttpResponseNotAllowed(
            ["POST"]
        )

# ==========================================
# CONTRACTS
# ==========================================


class ContractListView(LoginRequiredMixin, ListView):
    model = Contract
    template_name = "employees/contract_list.html"
    context_object_name = "contracts"
    paginate_by = 10

    def get_queryset(self):

        queryset = Contract.objects.select_related(
            "employee"
        ).all()

        search = self.request.GET.get(
            "search",
            ""
        ).strip()

        status = self.request.GET.get(
            "status",
            ""
        ).strip()

        contract_type = self.request.GET.get(
            "contract_type",
            ""
        ).strip()

        # Search by employee name or employee number.
        if search:

            queryset = queryset.filter(
                Q(employee__employee_number__icontains=search)
                | Q(employee__first_name__icontains=search)
                | Q(employee__last_name__icontains=search)
            )

        # Filter by contract status.
        if status:

            queryset = queryset.filter(
                status=status
            )

        # Filter by contract type.
        if contract_type:

            queryset = queryset.filter(
                contract_type=contract_type
            )

        return queryset.order_by(
            "-start_date"
        )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(
            **kwargs
        )

        context["status_choices"] = (
            Contract.STATUS_CHOICES
        )

        context["contract_type_choices"] = (
            Contract.CONTRACT_TYPE_CHOICES
        )

        return context


class ContractDetailView(LoginRequiredMixin, DetailView):
    model = Contract
    template_name = "employees/contract_detail.html"
    context_object_name = "contract"

    def get_queryset(self):

        return Contract.objects.select_related(
            "employee",
            "employee__department",
            "employee__position",
        )


class ContractCreateView(
    HRManagementRequiredMixin,
    SuccessMessageMixin,
    CreateView,
):
    model = Contract
    form_class = ContractForm
    template_name = "employees/contract_form.html"
    success_message = "Contract created."
    success_url = reverse_lazy(
        "employees:contract-list"
    )


class ContractUpdateView(
    HRManagementRequiredMixin,
    SuccessMessageMixin,
    UpdateView,
):
    model = Contract
    form_class = ContractForm
    template_name = "employees/contract_form.html"
    success_message = "Contract updated."

    def get_success_url(self):

        return reverse_lazy(
            "employees:contract-detail",
            kwargs={
                "pk": self.object.pk,
            },
        )


class ContractDeactivateView(
    HRManagementRequiredMixin,
    View,
):
    """
    Deactivate a contract using POST only.
    """

    def post(self, request, pk, *args, **kwargs):

        contract = get_object_or_404(
            Contract,
            pk=pk,
        )

        contract.status = "inactive"

        contract.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        messages.success(request, "Contract deactivated.")

        return redirect(
            "employees:contract-detail",
            pk=contract.pk,
        )

    def get(self, request, *args, **kwargs):

        return HttpResponseNotAllowed(
            ["POST"]
        )


class ContractReactivateView(
    HRManagementRequiredMixin,
    View,
):
    """
    Reactivate a contract using POST only.
    """

    def post(self, request, pk, *args, **kwargs):

        contract = get_object_or_404(
            Contract,
            pk=pk,
        )

        # Only one active contract may exist per employee.
        other_active_exists = Contract.objects.filter(
            employee=contract.employee,
            status="active",
        ).exclude(pk=contract.pk).exists()

        if other_active_exists:
            messages.error(
                request,
                "This employee already has an active contract. "
                "Deactivate or terminate it before reactivating this one.",
            )
            return redirect(
                "employees:contract-detail",
                pk=contract.pk,
            )

        contract.status = "active"

        contract.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        messages.success(request, "Contract reactivated.")

        return redirect(
            "employees:contract-detail",
            pk=contract.pk,
        )

    def get(self, request, *args, **kwargs):

        return HttpResponseNotAllowed(
            ["POST"]
        )


class ContractTerminateView(
    HRManagementRequiredMixin,
    View,
):
    """
    Terminate a contract using POST only.
    """

    def post(self, request, pk, *args, **kwargs):

        contract = get_object_or_404(
            Contract,
            pk=pk,
        )

        contract.status = "terminated"

        contract.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        messages.success(request, "Contract terminated.")

        return redirect(
            "employees:contract-detail",
            pk=contract.pk,
        )

    def get(self, request, *args, **kwargs):

        return HttpResponseNotAllowed(
            ["POST"]
        )