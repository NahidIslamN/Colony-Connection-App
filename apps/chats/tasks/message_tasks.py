from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.chats.models import Chat, Message


@shared_task
def sent_message_to_chat(chat_id: int, json_message: dict):
    channel_layer = get_channel_layer()
    try:
        users = Chat.objects.get(id=chat_id).participants.all()
    except Chat.DoesNotExist:
        return "chat does not exist"

    json_message["chat_id"] = chat_id
    for user in users:
        async_to_sync(channel_layer.group_send)(
            f"chats_{user.id}",
            {"type": "chat_message", "message": json_message},
        )
    return "success fully sent message to chat participants"


@shared_task
def update_messages_delivered(user_id):
    user_model = get_user_model()

    try:
        user = user_model.objects.get(id=user_id)
    except user_model.DoesNotExist:
        return

    recent_time = timezone.now() - timezone.timedelta(hours=24)
    chats = Chat.objects.filter(participants=user)

    Message.objects.filter(chat__in=chats, status="sent", created_at__gte=recent_time).exclude(sender=user).update(status="delivered")

    return "All messages received successfully and last_activity timestamp updated."
