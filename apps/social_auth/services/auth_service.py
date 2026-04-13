import logging

from django.conf import settings
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from apps.auths.models import CustomUser

logger = logging.getLogger(__name__)


class AuthServiceError(Exception):
    def __init__(self, code: str, details=None):
        super().__init__(code)
        self.code = code
        self.details = details or []

    def __str__(self) -> str:
        return self.code


def _configured_google_client_ids() -> list[str]:
    raw_multi = str(getattr(settings, "GOOGLE_OAUTH_CLIENT_IDS", "")).strip()
    if isinstance(getattr(settings, "GOOGLE_OAUTH_CLIENT_IDS", None), (list, tuple)):
        client_ids = [str(item).strip() for item in settings.GOOGLE_OAUTH_CLIENT_IDS if str(item).strip()]
    elif raw_multi:
        client_ids = [item.strip() for item in raw_multi.split(",") if item.strip()]
    else:
        client_ids = []

    single_client_id = str(getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "")).strip()
    if single_client_id and single_client_id not in client_ids:
        client_ids.append(single_client_id)

    return client_ids


def google_login(id_token_value: str) -> CustomUser:
    if not id_token_value:
        logger.warning("Google auth rejected: empty token")
        raise AuthServiceError("invalid_google_token")
    
    client_ids = _configured_google_client_ids()
    if not client_ids:
        logger.error("Google OAuth misconfigured: no client ID configured")
        raise AuthServiceError("google_oauth_misconfigured")

    audience = client_ids if len(client_ids) > 1 else client_ids[0]
    
    try:
        id_info = id_token.verify_oauth2_token(
            id_token_value,
            google_requests.Request(),
            audience=audience,
        )
    except (GoogleAuthError, ValueError, TypeError) as exc:
        logger.warning("Google auth rejected: token verification failed (%s)", str(exc))
        raise AuthServiceError("invalid_google_token") from exc
    

    issuer = id_info.get("iss")
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        logger.warning("Google auth rejected: invalid issuer")
        raise AuthServiceError("invalid_google_token")

    email = str(id_info.get("email") or "").strip().lower()
    full_name = str(id_info.get("name") or "").strip()
    email_verified = id_info.get("email_verified")
    if not email or email_verified is not True:
        logger.warning("Google auth rejected: missing or unverified email")
        raise AuthServiceError("invalid_google_token")

    user, _ = CustomUser.objects.get_or_create(email=email)
    user.full_name = full_name or user.full_name
    user.is_email_verified = True
    user.save(update_fields=["full_name", "is_email_verified"])
    return user
