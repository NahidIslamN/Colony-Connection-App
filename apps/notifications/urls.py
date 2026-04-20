from django.urls import path

from apps.notifications.views.api import NotificationsView, UnseenNotificationsCountView
from apps.notifications.views.device_api import (
    DeactivateDeviceAPIView,
    RegisterDeviceAPIView,
)

urlpatterns = [
    path("", NotificationsView.as_view(), name="notifications"),
    path("unseen-count", UnseenNotificationsCountView.as_view(), name="unseen-notifications-count"),
    path("device/register", RegisterDeviceAPIView.as_view(), name="register-device"),
    path("device/deactivate", DeactivateDeviceAPIView.as_view(), name="deactivate-device"),
]
