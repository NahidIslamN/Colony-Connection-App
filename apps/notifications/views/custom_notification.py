import logging

from celery import group
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.notifications.serializers import SentCustomNotificationInputSerializer
from apps.notifications.tasks.notification_tasks import sent_note_to_user
from core.custom_permission import IsAdmin, IsCompany
from core.responses import error_response, success_response


User = get_user_model()


class IsCompanyOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in {"company", "admin"}
        )


class SentCustomNotification(APIView):
    permission_classes = [IsCompany | IsAdmin]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        serializer = SentCustomNotificationInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Validation error.",
                status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        title = serializer.validated_data["title"]
        content = serializer.validated_data["description"]
        note_type = serializer.validated_data["notification_type"]
        user_ids = serializer.validated_data["user_ids"]
        extra_data = serializer.validated_data.get("data") or {}

        # Double-check against the current database state inside a transaction.
        with transaction.atomic():
            active_user_ids = list(
                User.objects.filter(id__in=user_ids, is_active=True).values_list("id", flat=True)
            )
            missing_user_ids = [user_id for user_id in user_ids if user_id not in active_user_ids]
            if missing_user_ids:
                return error_response(
                    "One or more users are invalid or inactive.",
                    status.HTTP_400_BAD_REQUEST,
                    errors={"user_ids": missing_user_ids},
                )

            notification_group = group(
                sent_note_to_user.s(user_id, title, content, note_type, extra_data)
                for user_id in active_user_ids
            )

            transaction.on_commit(notification_group.apply_async)

        return success_response(
            "Notifications queued successfully.",
            status.HTTP_202_ACCEPTED,
            data={
                "queued_count": len(user_ids),
                "notification_type": note_type,
            },
        )