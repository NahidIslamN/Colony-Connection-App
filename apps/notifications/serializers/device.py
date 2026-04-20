"""Input/output serializers for device registration and push notifications."""

from rest_framework import serializers

from apps.notifications.models import Device


class DeviceRegisterInputSerializer(serializers.Serializer):
    """Validate and parse device registration payload."""

    player_id = serializers.CharField(
        max_length=255,
        required=True,
        help_text="OneSignal player ID from SDK",
    )
    platform = serializers.ChoiceField(
        choices=["ios", "android", "web"],
        required=True,
        help_text="Device operating system",
    )
    device_token = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="FCM or APNS token for backup",
    )
    device_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Device model name (optional)",
    )

    def validate_player_id(self, value):
        """Ensure player_id is not empty after stripping."""
        if not value.strip():
            raise serializers.ValidationError("Player ID cannot be empty.")
        return value.strip()


class DeviceOutputSerializer(serializers.ModelSerializer):
    """Device information for read operations."""

    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Device
        fields = (
            "id",
            "user_email",
            "player_id",
            "platform",
            "device_name",
            "is_active",
            "last_activity",
            "created_at",
        )
        read_only_fields = (
            "id",
            "user_email",
            "player_id",
            "last_activity",
            "created_at",
        )
