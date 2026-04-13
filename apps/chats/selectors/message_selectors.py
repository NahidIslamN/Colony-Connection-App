from django.utils import timezone

from apps.chats.models import Chat, Message


def get_chat_messages(chat):
    return Message.objects.filter(chat=chat).select_related("sender").prefetch_related("files").order_by("-created_at")


def mark_non_sender_messages_as_seen(chat, user):
    return Message.objects.filter(chat=chat, status__in=["delivered", "sent"]).exclude(sender=user).update(status="seen")


def mark_recent_messages_as_delivered_for_user(user):
    chats = Chat.objects.filter(participants=user)
    recent_time = timezone.now() - timezone.timedelta(hours=24)
    Message.objects.filter(chat__in=chats, status="sent", created_at__gte=recent_time).exclude(sender=user).update(status="delivered")
