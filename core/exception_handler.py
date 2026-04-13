import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from core.exceptions import (
    AuthenticationDomainError,
    DomainError,
    NotFoundDomainError,
    PermissionDomainError,
    ValidationDomainError,
)
from core.logging_context import get_request_id

logger = logging.getLogger(__name__)


def _domain_status(exc: DomainError) -> int:
    if isinstance(exc, ValidationDomainError):
        return status.HTTP_400_BAD_REQUEST
    if isinstance(exc, AuthenticationDomainError):
        return status.HTTP_401_UNAUTHORIZED
    if isinstance(exc, PermissionDomainError):
        return status.HTTP_403_FORBIDDEN
    if isinstance(exc, NotFoundDomainError):
        return status.HTTP_404_NOT_FOUND
    return status.HTTP_400_BAD_REQUEST


def custom_exception_handler(exc, context):
    request_id = get_request_id()

    if isinstance(exc, DomainError):
        return Response(
            {
                "success": False,
                "message": exc.message,
                "errors": {"code": exc.code},
                "request_id": request_id,
            },
            status=_domain_status(exc),
        )

    response = drf_exception_handler(exc, context)
    if response is not None:
        detail = response.data
        message = "Request failed"
        if isinstance(detail, dict):
            message = str(detail.get("detail") or message)
        return Response(
            {
                "success": False,
                "message": message,
                "errors": detail,
                "request_id": request_id,
            },
            status=response.status_code,
        )

    logger.exception("Unhandled API exception", extra={"request_id": request_id})
    return Response(
        {
            "success": False,
            "message": "Internal server error",
            "errors": {"code": "internal_server_error"},
            "request_id": request_id,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
