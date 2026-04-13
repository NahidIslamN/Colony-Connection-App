from datetime import timedelta
from typing import Dict, Tuple

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
import logging

from apps.auths.models import CustomUser
from apps.auths.selectors.user_selectors import (
    get_or_create_user_otp,
    get_user_by_email,
    get_user_otp,
)
from apps.auths.services.email_service import send_verification_email
from apps.notifications.tasks.notification_tasks import sent_note_to_user
from common.otp import generate_otp


class AuthServiceError(Exception):
    def __init__(self, code: str, details=None):
        super().__init__(code)
        self.code = code
        self.details = details or []

    def __str__(self) -> str:
        return self.code

logger = logging.getLogger(__name__)


def _validate_password_or_raise(password: str, user: CustomUser | None = None) -> None:
    try:
        validate_password(password=password, user=user)
    except DjangoValidationError as exc:
        raise AuthServiceError("weak_password", details=list(exc.messages)) from exc


def create_or_update_unverified_signup_user(full_name: str, email: str, password: str) -> Tuple[CustomUser, bool]:
    _validate_password_or_raise(password=password)

    with transaction.atomic():
        existing_user = get_user_by_email(email)
        if existing_user and not existing_user.is_email_verified:
            existing_user.full_name = full_name
            existing_user.email = email
            existing_user.set_password(password)
            existing_user.save(update_fields=["full_name", "email", "password"])
            return existing_user, True

        if existing_user:
            raise AuthServiceError("duplicate_user")

        user = CustomUser.objects.create(full_name=full_name, email=email)
        user.set_password(password)
        user.save()
        return user, False


def issue_and_send_otp(user: CustomUser) -> str:
    with transaction.atomic():
        otp = generate_otp()
        otp_object = get_or_create_user_otp(user)
        otp_object.otp = otp
        otp_object.save(update_fields=["otp", "updated_at"])
    send_verification_email(user.email, user.full_name, otp)
    return otp


def verify_signup_otp(email: str, otp: str) -> Dict:
    with transaction.atomic():
        user = get_user_by_email(email)
        if not user:
            raise AuthServiceError("user_not_found")
        otp_object = get_user_otp(user)

        if otp_object.otp != otp:
            raise AuthServiceError("invalid_otp")

        if timezone.now() - otp_object.updated_at > timedelta(minutes=5):
            raise AuthServiceError("expired_otp")

        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])

        otp_object.otp = generate_otp()
        otp_object.save(update_fields=["otp", "updated_at"])

    sent_note_to_user.delay(
        user_id=user.id,
        title="Congratulations!",
        content="Your email has been successfully verified. Welcome to Mealz",
        note_type="success",
    )

    return {"user": user}


def authenticate_with_password(email: str, password: str):
    return authenticate(email=email, password=password)


def build_jwt_payload(user: CustomUser) -> Dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def refresh_access_from_refresh_token(refresh_token: str) -> Dict[str, str]:
    if not refresh_token:
        raise AuthServiceError("missing_refresh_token")

    try:
        refresh = RefreshToken(refresh_token)
    except (InvalidToken, TokenError, TypeError, ValueError) as exc:
        raise AuthServiceError("invalid_refresh_token") from exc

    user_id = refresh.get("user_id")
    if not user_id:
        raise AuthServiceError("invalid_refresh_token")

    user = CustomUser.objects.filter(id=user_id, is_active=True).first()
    if not user:
        raise AuthServiceError("user_not_found")

    payload: Dict[str, str] = {"access": str(refresh.access_token)}

    rotate_refresh = bool(settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS", False))
    if rotate_refresh:
        new_refresh = RefreshToken.for_user(user)
        payload["refresh"] = str(new_refresh)

        if settings.SIMPLE_JWT.get("BLACKLIST_AFTER_ROTATION", False):
            try:
                refresh.blacklist()
            except AttributeError:
                pass

    return payload


def request_forgot_password_otp(email: str) -> None:
    user = get_user_by_email(email)
    if not user:
        raise AuthServiceError("user_not_found")
    issue_and_send_otp(user)


def verify_forgot_password_otp(email: str, otp: str) -> Dict:
    with transaction.atomic():
        user = get_user_by_email(email)
        if not user:
            raise AuthServiceError("user_not_found")
        otp_object = get_user_otp(user)

        if otp_object.otp != otp:
            raise AuthServiceError("invalid_otp")

        if timezone.now() - otp_object.updated_at > timedelta(minutes=5):
            raise AuthServiceError("expired_otp")

        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])

        otp_object.otp = generate_otp()
        otp_object.save(update_fields=["otp", "updated_at"])
        return {"user": user}


def change_user_password(user: CustomUser, old_password: str, new_password: str) -> bool:
    if not check_password(old_password, user.password):
        return False

    _validate_password_or_raise(password=new_password, user=user)
    user.set_password(new_password)
    user.save(update_fields=["password"])
    return True


def reset_user_password(user: CustomUser, new_password: str) -> None:
    _validate_password_or_raise(password=new_password, user=user)
    user.set_password(new_password)
    user.save(update_fields=["password"])
