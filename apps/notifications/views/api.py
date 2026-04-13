from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.notifications.serializers.output import NotificationOutputSerializer
from apps.notifications.services.note_service import get_notifications_and_mark_seen, get_unseen_notifications_count
from core.pagination import CustomPagination
from core.responses import success_response


class UnseenNotificationsCountView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get(self, request):
        total = get_unseen_notifications_count(request.user)
        return success_response("data fatched!", status.HTTP_200_OK, total_unseen_note=total)


class NotificationsView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get(self, request):
        notifications = get_notifications_and_mark_seen(request.user)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(notifications, request)
        serializer = NotificationOutputSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)
