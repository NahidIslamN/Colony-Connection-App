"""Device registration and management API views."""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.notifications.serializers.device import (
    DeviceOutputSerializer,
    DeviceRegisterInputSerializer,
)
from apps.notifications.services.push_notification_service import (
    deactivate_device,
    register_device_player_id,
)
from core.responses import error_response, success_response

logger = logging.getLogger(__name__)


class RegisterDeviceAPIView(APIView):
    """
    Register device player_id for push notifications.
    
    POST: Register/update device player_id for current user
    One user = One active device (last login device)
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def post(self, request):
        serializer = DeviceRegisterInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Validation error.",
                status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        try:
            device = register_device_player_id(
                user=request.user,
                player_id=serializer.validated_data["player_id"],
                platform=serializer.validated_data["platform"],
                device_token=serializer.validated_data.get("device_token", ""),
                device_name=serializer.validated_data.get("device_name", ""),
            )

            output_serializer = DeviceOutputSerializer(device)
            return success_response(
                "Device registered successfully.",
                status.HTTP_201_CREATED,
                data=output_serializer.data,
            )
        except Exception as exc:
            logger.error(f"Error registering device for user {request.user.id}: {exc}", exc_info=True)
            return error_response(
                "Failed to register device.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DeactivateDeviceAPIView(APIView):
    """Deactivate device when user logs out."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def post(self, request):
        player_id = request.data.get("player_id")
        if not player_id:
            return error_response(
                "Validation error.",
                status.HTTP_400_BAD_REQUEST,
                errors={"player_id": "This field is required."},
            )

        try:
            success = deactivate_device(player_id)
            if success:
                return success_response(
                    "Device deactivated successfully.",
                    status.HTTP_200_OK,
                )
            else:
                return error_response(
                    "Device not found.",
                    status.HTTP_404_NOT_FOUND,
                )
        except Exception as exc:
            logger.error(f"Error deactivating device {player_id}: {exc}", exc_info=True)
            return error_response(
                "Failed to deactivate device.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
