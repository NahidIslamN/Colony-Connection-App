from django.urls import path

from apps.sales_team.views.sales import VisitColonyReport_SpecificDay

urlpatterns = [
    path("report/", VisitColonyReport_SpecificDay.as_view(), name="sales-team-visit-report"),
]
