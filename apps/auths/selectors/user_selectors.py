from typing import Optional

from apps.auths.models import CustomUser, OtpTable


def get_user_by_email(email: str) -> Optional[CustomUser]:
    return CustomUser.objects.filter(email=email).first()


def get_or_create_user_otp(user: CustomUser) -> OtpTable:
    otp_object, _ = OtpTable.objects.get_or_create(user=user)
    return otp_object


def get_user_otp(user: CustomUser) -> OtpTable:
    return OtpTable.objects.get(user=user)
