from typing import Mapping

from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from core.exceptions import AuthenticationDomainError


def validate_access_token(token: str) -> AccessToken:
    try:
        return AccessToken(token)
    except (InvalidToken, TokenError) as exc:
        raise AuthenticationDomainError(code="invalid_token", message="Invalid token") from exc


def get_user_id_from_token(token: str) -> int:
    validated = validate_access_token(token)
    user_id = validated.get("user_id")
    if user_id is None:
        raise AuthenticationDomainError(code="invalid_token", message="Invalid token payload")

    try:
        return int(user_id)
    except (TypeError, ValueError) as exc:
        raise AuthenticationDomainError(code="invalid_token", message="Invalid token payload") from exc


def extract_bearer_token(headers: Mapping[str, str]) -> str | None:
    auth_header = headers.get("authorization")
    if not auth_header:
        return None

    auth_header = auth_header.strip()
    if not auth_header.lower().startswith("bearer "):
        return None

    parts = auth_header.split(None, 1)
    if len(parts) != 2 or not parts[1].strip():
        return None
    return parts[1].strip()
