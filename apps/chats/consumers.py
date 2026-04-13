import json
import logging
from urllib.parse import urlparse

from channels.db import database_sync_to_async
from channels.db import database_sync_to_async as _database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache

from apps.chats.services.chat_service import create_chat_message, list_chat_participant_ids
from core.exceptions import AuthenticationDomainError, NotFoundDomainError, PermissionDomainError, ValidationDomainError
from core.jwt_utils import extract_bearer_token, get_user_id_from_token

logger = logging.getLogger(__name__)


def _extract_token(scope, headers):
    return extract_bearer_token(headers)


def is_ws_message_rate_limited(user_id: int) -> bool:
    limit = int(getattr(settings, "WS_MESSAGE_RATE_LIMIT", 60))
    window_seconds = int(getattr(settings, "WS_MESSAGE_RATE_WINDOW_SECONDS", 60))
    cache_key = f"ws-message-rate:{user_id}"

    if cache.add(cache_key, 1, timeout=window_seconds):
        return False

    try:
        current = cache.incr(cache_key)
    except ValueError:
        cache.set(cache_key, 1, timeout=window_seconds)
        return False
    return current > limit


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


class UpdateChatConsumerMessageGet(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        headers = {k.decode(): v.decode() for k, v in self.scope.get("headers", [])}

        if not _origin_is_allowed(headers):
            logger.warning("WebSocket chat rejected: origin not allowed")
            await self.close(code=4002)
            return

        token = _extract_token(self.scope, headers)
        if token is None:
            logger.warning("WebSocket chat rejected: missing token")
            await self.close(code=4001)
            return

        try:
            token_user_id = get_user_id_from_token(token)
        except AuthenticationDomainError:
            logger.warning("WebSocket chat rejected: invalid token")
            await self.close(code=4001)
            return

        if getattr(self.user, "is_anonymous", True):
            try:
                user_obj = await _database_sync_to_async(get_user_model().objects.get)(id=token_user_id)
            except get_user_model().DoesNotExist:
                logger.warning("WebSocket chat rejected: user not found")
                await self.close(code=4001)
                return
            self.scope["user"] = user_obj
            self.user = user_obj

        if getattr(self.user, "id", None) != token_user_id:
            logger.warning("WebSocket chat rejected: token/user mismatch")
            await self.close(code=4001)
            return

        self.user_group = f"chats_{self.user.id}"
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "user_group") and getattr(self, "channel_layer", None):
            try:
                await self.channel_layer.group_discard(self.user_group, self.channel_name)
            except (AttributeError, RuntimeError, TypeError):
                logger.warning("Failed to discard chat group", exc_info=True)

    async def receive(self, text_data):
        if await self.is_message_rate_limited():
            logger.warning(
                "WebSocket chat rejected: rate limit exceeded",
                extra={"user_id": getattr(self.user, "id", None)},
            )
            await self.close(code=4008)
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        message_text = data.get("message", "")
        chat_id = data.get("chat_id")
        files_data = data.get("files", [])

        if not chat_id or (not message_text and not files_data):
            return

        try:
            message_obj = await self.save_message_to_database(message_text, files_data, chat_id)
        except (ValidationDomainError, PermissionDomainError, NotFoundDomainError):
            logger.warning(
                "WebSocket chat message rejected",
                extra={"chat_id": chat_id, "user_id": getattr(self.user, "id", None)},
            )
            return

        files_urls = await self.get_message_files(message_obj)

        username = getattr(self.user, "username", None) or getattr(self.user, "email", "Anonymous")
        profile_image = None
        user_image = getattr(self.user, "image", None)
        if user_image:
            profile_image = user_image.url

        payload = {
            "id": message_obj.id,
            "text": message_obj.text,
            "status": getattr(message_obj, "status", None),
            "chat_id": chat_id,
            "sender": {"id": self.user.id, "username": username, "profile_image": profile_image},
            "last_activity": str(getattr(self.user, "last_activity", None)),
            "files": files_urls,
            "created_at": message_obj.created_at.isoformat() if message_obj.created_at else None,
        }

        try:
            participant_ids = await self.get_chat_participants(chat_id)
        except NotFoundDomainError:
            logger.warning(
                "WebSocket chat message dropped: chat participants not found",
                extra={"chat_id": chat_id, "user_id": getattr(self.user, "id", None)},
            )
            return

        for participant_id in participant_ids:
            await self.channel_layer.group_send(
                f"chats_{participant_id}",
                {"type": "chat_message", "message": payload},
            )

    async def chat_message(self, event):
        msg = event.get("message", {})
        await self.send(
            text_data=json.dumps(
                {
                    "success": True,
                    "message": msg,
                    "chat_id": msg.get("chat_id"),
                    "username": (msg.get("sender") or {}).get("username"),
                    "image": (msg.get("sender") or {}).get("profile_image"),
                    "last_activity": msg.get("last_activity"),
                    "files": msg.get("files", []),
                }
            )
        )

    @database_sync_to_async
    def get_message_files(self, message_obj):
        return [file_item.file.url for file_item in message_obj.files.all()]

    @database_sync_to_async
    def save_message_to_database(self, message_text, files, chat_id):
        return create_chat_message(
            user=self.user,
            chat_id=chat_id,
            message_text=message_text,
            files=files,
        )

    @database_sync_to_async
    def is_message_rate_limited(self):
        return is_ws_message_rate_limited(getattr(self.user, "id", 0))

    @database_sync_to_async
    def get_chat_participants(self, chat_id):
        participant_ids = list_chat_participant_ids(chat_id)
        if not participant_ids:
            raise NotFoundDomainError(code="chat_not_found", message="Chat not found")
        return participant_ids
