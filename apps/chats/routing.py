from django.urls import path

from apps.chats.consumers import UpdateChatConsumerMessageGet

websocket_urlpatterns = [
    path("ws/asc/chats/", UpdateChatConsumerMessageGet.as_asgi()),
]
