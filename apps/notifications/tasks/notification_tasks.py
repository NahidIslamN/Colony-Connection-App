from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model

from apps.notifications.models import NoteModel


@shared_task
def sent_note_to_user(user_id: int, title: str, content: str, note_type: str):
    user_model = get_user_model()
    try:
        user = user_model.objects.get(id=user_id)
        NoteModel.objects.create(user=user, title=title, content=content, note_type=note_type)
    except user_model.DoesNotExist:
        return "User not found"

    channel_layer = get_channel_layer()
    payload = {"title": title, "content": content, "note_type": note_type}
    group_name = f"notification_{user_id}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": note_type,
            "message": payload,
            "saved": True,
        },
    )

    return "success fully sent note to user"
