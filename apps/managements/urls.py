from django.urls import path

from .views.company_functions import (
    ColonyDetailAPIView, 
    ColonyListCreateAPIView, 
    ColonyAnalyticsService,
    SalseRepList
)

urlpatterns = [
    path("company/colonies/", ColonyListCreateAPIView.as_view(), name="colony-list-create"),
    path("company/colonies/<int:pk>/", ColonyDetailAPIView.as_view(), name="colony-detail"),
    path("company/colonies/analytics/", ColonyAnalyticsService.as_view(), name='analytics'),
    path("company/salse-reps/", SalseRepList.as_view(), name='salse-reps'),
 
]
