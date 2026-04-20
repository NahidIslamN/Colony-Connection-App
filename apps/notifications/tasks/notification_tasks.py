import logging
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from apps.notifications.models import NoteModel
from apps.notifications.services.push_notification_service import (
    send_push_notification_to_user,
)


logger = logging.getLogger(__name__)


@shared_task
def sent_note_to_user(user_id: int, title: str, content: str, note_type: str, data: dict = None):
    """
    Send notification to user with multiple delivery methods:
    1. WebSocket (real-time)
    2. Database (persistent storage)
    3. Push Notification (mobile/web via OneSignal)
    
    Args:
        user_id: User ID to send notification to
        title: Notification title
        content: Notification body
        note_type: Notification type (success/warning/normal)
        data: Optional additional data payload for push notification
    """
    user_model = get_user_model()

    try:
        user = user_model.objects.get(id=user_id)
    except user_model.DoesNotExist:
        logger.error(f"User {user_id} not found for notification")
        return "User not found"

    # 1. Store in database for persistent history
    try:
        NoteModel.objects.create(
            user=user,
            title=title,
            content=content,
            note_type=note_type,
        )
        logger.info(f"Notification stored in DB for user {user_id}")
    except Exception as exc:
        logger.error(f"Error storing notification in DB: {exc}", exc_info=True)

    # 2. Send WebSocket message for real-time delivery
    try:
        channel_layer = get_channel_layer()
        payload = {
            "title": title,
            "content": content,
            "note_type": note_type,
            "data": data or {},
        }
        group_name = f"notification_{user_id}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": note_type,
                "message": payload,
                "saved": True,
            },
        )
        logger.info(f"WebSocket notification sent to user {user_id}")
    except Exception as exc:
        logger.error(f"Error sending WebSocket notification: {exc}", exc_info=True)

    # 3. Send push notification to device (OneSignal)
    try:
        push_data = data or {}
        push_success = send_push_notification_to_user(
            user=user,
            title=title,
            content=content,
            data=push_data,
        )
        if push_success:
            logger.info(f"Push notification sent to user {user_id}")
        else:
            logger.warning(f"No active device found for push notification to user {user_id}")
    except Exception as exc:
        logger.error(f"Error sending push notification: {exc}", exc_info=True)

    return "Notification sent successfully"
