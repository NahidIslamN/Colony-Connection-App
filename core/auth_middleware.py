from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from core.exceptions import AuthenticationDomainError
from core.jwt_utils import extract_bearer_token, get_user_id_from_token

User = get_user_model()


class CustomAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        scope["user"] = await self.get_user(scope)
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, scope):
        try:
            header_map = {
                key.decode().lower(): value.decode()
                for key, value in scope.get("headers", [])
            }
            token = extract_bearer_token(header_map)
            if not token:
                return AnonymousUser()

            user_id = get_user_id_from_token(token)
            return User.objects.get(id=user_id)
        except (User.DoesNotExist, AuthenticationDomainError, TypeError, ValueError):
            return AnonymousUser()
