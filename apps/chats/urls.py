from django.urls import path

from apps.chats.views.api import (
    ChatCreateListView,
    MessageListChatsView,
    SentMessageChatsView,
)

urlpatterns = [
    path("inboxes", ChatCreateListView.as_view(), name="chat-create-list"),
    path("messages/<int:inbox_id>", MessageListChatsView.as_view(), name="messages"),
    path("sent-message/<int:inbox_id>", SentMessageChatsView.as_view(), name="send-message"),
]
