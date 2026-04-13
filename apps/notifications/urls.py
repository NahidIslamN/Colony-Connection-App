from django.urls import path
from apps.notifications.views.api import NotificationsView, UnseenNotificationsCountView

urlpatterns = [
    path("", NotificationsView.as_view(), name="notifications"),
    path("unseen-count", UnseenNotificationsCountView.as_view(), name="unseen-notifications-count"),
]
