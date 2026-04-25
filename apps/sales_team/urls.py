from django.urls import path

from apps.sales_team.views.sales import VisitColonyReport_SpecificDay, CustomerListCreateAPIView

urlpatterns = [
    path("report/", VisitColonyReport_SpecificDay.as_view(), name="sales-team-visit-report"),
    path(
        "report/<int:pk>",
        VisitColonyReport_SpecificDay.as_view(),
        name="sales-team-visit-report-detail",
    ),
    path('add-customer/<int:colony_id>/', CustomerListCreateAPIView.as_view(), name='create-customer'),
]
