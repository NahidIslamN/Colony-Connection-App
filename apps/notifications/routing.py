from django.urls import path

from apps.notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    path("ws/asc/notifications/", NotificationConsumer.as_asgi()),
]
