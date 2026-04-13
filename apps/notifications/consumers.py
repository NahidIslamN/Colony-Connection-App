import json
import logging
from urllib.parse import urlparse

from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from channels.db import database_sync_to_async as _database_sync_to_async
from channels.exceptions import StopConsumer
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.notifications.models import NoteModel
from core.exceptions import AuthenticationDomainError
from core.jwt_utils import extract_bearer_token, get_user_id_from_token

logger = logging.getLogger(__name__)


def _extract_token(scope, headers):
    return extract_bearer_token(headers)


def _origin_is_allowed(headers):
    origin = headers.get("origin")
    if not origin:
        return True

    try:
        host = urlparse(origin).hostname
    except ValueError:
        return False

    allowed = settings.ALLOWED_HOSTS or []
    if allowed == ["*"]:
        return True
    return bool(host and host in allowed)


class NotificationConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        user = self.scope.get("user")
        headers = {k.decode(): v.decode() for k, v in self.scope.get("headers", [])}

        if not _origin_is_allowed(headers):
            logger.warning("WebSocket notification rejected: origin not allowed")
            await self.close()
            return

        token = _extract_token(self.scope, headers)
        if token is None:
            logger.warning("WebSocket notification rejected: missing token")
            await self.send({"type": "websocket.close", "code": 4001})
            return

        try:
            token_user_id = get_user_id_from_token(token)
        except AuthenticationDomainError:
            logger.warning("WebSocket notification rejected: invalid token")
            await self.send({"type": "websocket.close", "code": 4001})
            return

        if getattr(user, "is_anonymous", True):
            try:
                user = await _database_sync_to_async(get_user_model().objects.get)(id=token_user_id)
            except get_user_model().DoesNotExist:
                logger.warning("WebSocket notification rejected: user not found")
                await self.send({"type": "websocket.close", "code": 4001})
                return
            self.scope["user"] = user

        if getattr(user, "id", None) != token_user_id:
            logger.warning("WebSocket notification rejected: token/user mismatch")
            await self.send({"type": "websocket.close", "code": 4001})
            return

        self.room_group_name = f"notification_{user.id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.send({"type": "websocket.accept"})

    async def websocket_receive(self, event):
        text_data = event.get("text", "")
        try:
            message = json.loads(text_data)
        except json.JSONDecodeError:
            message = {"text": text_data}

        await self.channel_layer.group_send(self.room_group_name, {"type": "sent.note", "message": message})

    async def sent_note(self, event):
        data = event["message"]
        user = self.scope.get("user")

        if not event.get("saved", False):
            await self.save_notification(user=user, data=data)

        await self.send({"type": "websocket.send", "text": json.dumps(event["message"])})

    async def success(self, event):
        await self.sent_note(event)

    async def warning(self, event):
        await self.sent_note(event)

    async def normal(self, event):
        await self.sent_note(event)

    @database_sync_to_async
    def save_notification(self, user, data):
        return NoteModel.objects.create(
            user=user,
            title=data.get("title"),
            content=data.get("content"),
            note_type=data.get("note_type"),
        )

    async def websocket_disconnect(self, event):
        if hasattr(self, "room_group_name") and getattr(self, "channel_layer", None):
            try:
                await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            except (AttributeError, RuntimeError, TypeError):
                logger.warning("Failed to discard notification group", exc_info=True)
        raise StopConsumer()
