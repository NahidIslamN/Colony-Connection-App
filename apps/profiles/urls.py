from django.urls import path

from apps.profiles.views.api import MyAccountAPIView

urlpatterns = [
    path("me/", MyAccountAPIView.as_view(), name="profiles"),
]
