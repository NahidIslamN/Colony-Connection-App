from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.managements.models import Company, SupportModel

logger = logging.getLogger(__name__)
User = get_user_model()


COMPANY_ASSIGNMENT_CACHE_KEY = "admin_dashboard:company_assignment_list:v1"
COMPANY_ASSIGNMENT_CACHE_TIMEOUT = 300


@dataclass
class CompanyServiceError(Exception):
    code: str
    details: object | None = None

    def __str__(self) -> str:
        return self.code


def _resolve_company_queryset() -> QuerySet[Company]:
    return Company.objects.select_related("user", "subscription_package").all().order_by("-id")


def _invalidate_company_assignment_cache() -> None:
    cache.delete(COMPANY_ASSIGNMENT_CACHE_KEY)


def get_companies_for_assignment(force_refresh: bool = False) -> list[dict]:
    """Return a compact company list for assignment dropdowns (cached)."""
    if not force_refresh:
        cached = cache.get(COMPANY_ASSIGNMENT_CACHE_KEY)
        if cached is not None:
            return cached

    companies = _resolve_company_queryset().select_related("user")
    payload = [
        {
            "id": company.id,
            "company_name": company.company_name,
            "email": company.email,
            "phone": company.phone,
            "user": {
                "id": company.user_id,
                "email": company.user.email if company.user else None,
                "full_name": company.user.full_name if company.user else None,
            },
        }
        for company in companies
    ]

    cache.set(COMPANY_ASSIGNMENT_CACHE_KEY, payload, COMPANY_ASSIGNMENT_CACHE_TIMEOUT)
    return payload


def list_companies(query_params=None) -> QuerySet[Company]:
    queryset = _resolve_company_queryset()
    query_params = query_params or {}

    search = query_params.get("search")
    if search:
        queryset = queryset.filter(
            Q(company_name__icontains=search)
            | Q(ceo_name__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
            | Q(user__email__icontains=search)
            | Q(user__full_name__icontains=search)
        )

    subscription_package = query_params.get("subscription_package")
    if subscription_package:
        queryset = queryset.filter(subscription_package_id=subscription_package)

    is_subscribe = query_params.get("is_subscribe")
    if is_subscribe is not None and str(is_subscribe).lower() in {"true", "false"}:
        queryset = queryset.filter(is_subscribe=str(is_subscribe).lower() == "true")

    return queryset




def _resolve_support_queryset() -> QuerySet[SupportModel]:
    return SupportModel.objects.prefetch_related("files").all().order_by("-id")


def list_support_messages(keyword: str | None = None) -> QuerySet[SupportModel]:
    queryset = _resolve_support_queryset()

    if keyword:
        queryset = queryset.filter(
            Q(full_name__icontains=keyword)
            | Q(message__icontains=keyword)
            | Q(email__icontains=keyword)
        )

    return queryset


# Backward-compatible alias
def list_messages(keyword: str | None = None) -> QuerySet[SupportModel]:
    return list_support_messages(keyword=keyword)
        



def get_company_by_id(company_id: int) -> Company | None:
    return _resolve_company_queryset().filter(id=company_id).first()


def _default_expire_date(subscription_package=None):
    if subscription_package:
        return timezone.localdate() + timedelta(days=30)
    return timezone.localdate()


def _user_payload_from_data(data: dict) -> dict:
    return {
        "full_name": data.get("user_full_name") or data.get("ceo_name") or "",
        "email": data.get("user_email") or data.get("email"),
        "phone": data.get("user_phone") or data.get("phone") or None,
        "role": data.get("user_role", "company"),
        "status": data.get("user_status", True),
        "is_active": data.get("user_is_active", True),
    }


@transaction.atomic
def create_company(validate_data: dict) -> Company:
    try:
        payload = dict(validate_data)
        user_payload = _user_payload_from_data(payload)
        password = payload.pop("password")

        user = User.objects.create_user(
            email=user_payload["email"],
            password=password,
            full_name=user_payload["full_name"],
            phone=user_payload["phone"],
            role=user_payload["role"],
            status=user_payload["status"],
            is_active=user_payload["is_active"],
            is_email_verified=True,
            is_phone_verified=True,
        )

        company = Company.objects.create(
            user=user,
            company_name=payload["company_name"],
            ceo_name=payload.get("ceo_name") or user_payload["full_name"],
            email=payload.get("email") or user_payload["email"],
            phone=payload.get("phone") or user_payload["phone"],
            subscription_package=payload.get("subscription_package"),
            is_subscribe=bool(payload.get("is_subscribe", False)),
            expire_date=payload.get("expire_date") or _default_expire_date(payload.get("subscription_package")),
        )

        _invalidate_company_assignment_cache()

        return company
    except IntegrityError as exc:
        logger.exception("Integrity error while creating company")
        raise CompanyServiceError("integrity_error", details="Company or user already exists.") from exc
    except Exception as exc:
        logger.exception("Unexpected error while creating company")
        raise CompanyServiceError("company_create_failed", details=str(exc)) from exc


@transaction.atomic
def update_company(company_id: int, validate_data: dict) -> Company:
    try:
        company = Company.objects.select_for_update().select_related("user", "subscription_package").filter(id=company_id).first()
        if not company:
            raise CompanyServiceError("company_not_found", details="Company not found.")

        user = company.user
        company_changed = False
        user_changed = False

        # Update Company fields
        if "company_name" in validate_data:
            company.company_name = validate_data["company_name"]
            company_changed = True
        if "ceo_name" in validate_data:
            company.ceo_name = validate_data["ceo_name"]
            company_changed = True
        if "email" in validate_data and validate_data["email"] != company.email:
            # Check uniqueness excluding self
            if Company.objects.filter(email=validate_data["email"]).exclude(id=company.id).exists():
                raise CompanyServiceError("integrity_error", details="A company with this email already exists.")
            company.email = validate_data["email"]
            company_changed = True
        if "phone" in validate_data and validate_data["phone"] != company.phone:
            # Check uniqueness excluding self
            if Company.objects.filter(phone=validate_data["phone"]).exclude(id=company.id).exists():
                raise CompanyServiceError("integrity_error", details="A company with this phone already exists.")
            company.phone = validate_data["phone"]
            company_changed = True
        if "subscription_package" in validate_data:
            company.subscription_package = validate_data["subscription_package"]
            company_changed = True
        if "is_subscribe" in validate_data:
            company.is_subscribe = validate_data["is_subscribe"]
            company_changed = True
        if "expire_date" in validate_data:
            company.expire_date = validate_data["expire_date"]
            company_changed = True

        # Update User fields
        if user:
            if "user_full_name" in validate_data or "ceo_name" in validate_data:
                new_full_name = validate_data.get("user_full_name") or validate_data.get("ceo_name") or user.full_name
                if new_full_name != user.full_name:
                    user.full_name = new_full_name
                    user_changed = True
            if "user_email" in validate_data or "email" in validate_data:
                new_email = validate_data.get("user_email") or validate_data.get("email") or user.email
                if new_email != user.email:
                    # Check uniqueness excluding self
                    if User.objects.filter(email=new_email).exclude(id=user.id).exists():
                        raise CompanyServiceError("integrity_error", details="A user with this email already exists.")
                    user.email = new_email
                    user_changed = True
            if "user_phone" in validate_data or "phone" in validate_data:
                new_phone = validate_data.get("user_phone") or validate_data.get("phone") or user.phone
                if new_phone != user.phone:
                    # Check uniqueness excluding self
                    if User.objects.filter(phone=new_phone).exclude(id=user.id).exists():
                        raise CompanyServiceError("integrity_error", details="A user with this phone already exists.")
                    user.phone = new_phone
                    user_changed = True
            if "user_status" in validate_data and validate_data["user_status"] != user.status:
                user.status = validate_data["user_status"]
                user_changed = True
            if "user_is_active" in validate_data and validate_data["user_is_active"] != user.is_active:
                user.is_active = validate_data["user_is_active"]
                user_changed = True
            if validate_data.get("password"):
                user.set_password(validate_data["password"])
                user_changed = True

            if user.email:
                user.is_email_verified = True
            if user.phone:
                user.is_phone_verified = True

            if user_changed:
                user.save()

        if company_changed:
            company.save()

        _invalidate_company_assignment_cache()

        return company
    except CompanyServiceError:
        raise
    except IntegrityError as exc:
        logger.exception("Integrity error while updating company")
        raise CompanyServiceError("integrity_error", details="Unable to update company due to duplicate data.") from exc
    except Exception as exc:
        logger.exception("Unexpected error while updating company")
        raise CompanyServiceError("company_update_failed", details=str(exc)) from exc


@transaction.atomic
def delete_company(company_id: int) -> None:
    company = Company.objects.select_for_update().select_related("user").filter(id=company_id).first()
    if not company:
        raise CompanyServiceError("company_not_found", details="Company not found.")

    user = company.user
    company.delete()
    if user:
        user.delete()

    _invalidate_company_assignment_cache()



