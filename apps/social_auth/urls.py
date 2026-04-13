from django.urls import path
from apps.social_auth.views.api import GoogleLoginView

urlpatterns = [
    path("google", GoogleLoginView.as_view(), name="google-auth"),
]
