from django.urls import path

from .views.company_functions import (
    CustomerDetailAPIView,
    CustomerListCreateAPIView,
    ColonyDetailAPIView, 
    ColonyListCreateAPIView, 
    ColonyAnalyticsService,
    ColoniesForAssignmentAPIView,
    SalesRepsForAssignmentAPIView,
    SalseRepList,
    SalesRepresentativeDetailAPIView,
    SalesRepresentativeListCreateAPIView,
    AssignSalesRepToColoniesAPIView,
    GetSalesRepColoniesAPIView,
)

urlpatterns = [
    path("company/colonies/", ColonyListCreateAPIView.as_view(), name="colony-list-create"),
    path("company/colonies/<int:pk>/", ColonyDetailAPIView.as_view(), name="colony-detail"),
    path("company/colonies/analytics/", ColonyAnalyticsService.as_view(), name='analytics'),
    path("company/salse-reps/", SalseRepList.as_view(), name='salse-reps'),

    path("company/colonies-for-assignment/", ColoniesForAssignmentAPIView.as_view(), name="colonies-for-assignment"),
    path("company/sales-reps-for-assignment/", SalesRepsForAssignmentAPIView.as_view(), name="sales-reps-for-assignment"),

    path("company/customers/", CustomerListCreateAPIView.as_view(), name="customer-list-create"),
    path("company/customers/<int:pk>/", CustomerDetailAPIView.as_view(), name="customer-detail"),

    path("company/sales-representatives/", SalesRepresentativeListCreateAPIView.as_view(), name="sales-representative-list-create"),
    path("company/sales-representatives/<int:pk>/", SalesRepresentativeDetailAPIView.as_view(), name="sales-representative-detail"),

    path("company/sales-representatives/<int:sales_rep_id>/assign-colonies/", AssignSalesRepToColoniesAPIView.as_view(), name="assign-sales-rep-colonies"),
    path("company/sales-representatives/<int:sales_rep_id>/colonies/", GetSalesRepColoniesAPIView.as_view(), name="sales-rep-colonies"),
]
