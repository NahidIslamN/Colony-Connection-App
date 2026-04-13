from django.core.cache import cache
from django.test import TestCase
from django.test import override_settings
from rest_framework_simplejwt.tokens import AccessToken

from apps.chats.consumers import _extract_token
from apps.auths.models import CustomUser
from apps.chats.consumers import UpdateChatConsumerMessageGet, is_ws_message_rate_limited
from apps.chats.models import Chat
from core.exceptions import AuthenticationDomainError, PermissionDomainError
from core.jwt_utils import get_user_id_from_token


class WebsocketSecurityTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email="user@example.com", password="Pass1234")
        self.other_user = CustomUser.objects.create_user(email="other@example.com", password="Pass1234")
        self.chat = Chat.objects.create(chat_type="private", inviter=self.user, invitee=self.user)
        self.chat.participants.add(self.user)

    def test_token_validation_returns_user_id(self):
        token = str(AccessToken.for_user(self.user))
        user_id = get_user_id_from_token(token)
        self.assertEqual(user_id, self.user.id)

    def test_token_validation_rejects_invalid_token(self):
        with self.assertRaises(AuthenticationDomainError):
            get_user_id_from_token("invalid-token")

    def test_ws_message_save_rejects_non_participant(self):
        consumer = UpdateChatConsumerMessageGet()
        consumer.user = self.other_user

        with self.assertRaises(PermissionDomainError):
            UpdateChatConsumerMessageGet.save_message_to_database.__wrapped__(consumer, "hello", [], self.chat.id)

    def test_ws_token_extraction_rejects_query_string_token(self):
        token = str(AccessToken.for_user(self.user))
        scope = {"query_string": f"token={token}".encode()}
        extracted = _extract_token(scope, {})
        self.assertIsNone(extracted)

    def test_ws_token_extraction_accepts_authorization_header(self):
        token = str(AccessToken.for_user(self.user))
        headers = {"authorization": f"Bearer {token}"}
        extracted = _extract_token({}, headers)
        self.assertEqual(extracted, token)

    @override_settings(WS_MESSAGE_RATE_LIMIT=2, WS_MESSAGE_RATE_WINDOW_SECONDS=60)
    def test_ws_message_rate_limit_blocks_excess_messages(self):
        cache.clear()
        self.assertFalse(is_ws_message_rate_limited(self.user.id))
        self.assertFalse(is_ws_message_rate_limited(self.user.id))
        self.assertTrue(is_ws_message_rate_limited(self.user.id))
