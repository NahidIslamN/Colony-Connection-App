from django.urls import path

from .views.company_functions import ColonyDetailAPIView, ColonyListCreateAPIView

urlpatterns = [
    path("company/colonies/", ColonyListCreateAPIView.as_view(), name="colony-list-create"),
    path("company/colonies/<int:pk>/", ColonyDetailAPIView.as_view(), name="colony-detail"),
]
