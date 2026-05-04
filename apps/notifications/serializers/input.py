from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.notifications.models import NoteModel


User = get_user_model()


class SentCustomNotificationInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, allow_blank=False, trim_whitespace=True)
    description = serializers.CharField(allow_blank=False, trim_whitespace=True)
    notification_type = serializers.ChoiceField(choices=NoteModel.NOTE_TYPE)
    user_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        min_length=1,
        max_length=500,
    )
    data = serializers.JSONField(required=False)

    def validate_user_ids(self, value):
        unique_ids = list(dict.fromkeys(value))
        if len(unique_ids) != len(value):
            raise serializers.ValidationError("Duplicate user IDs are not allowed.")

        existing_ids = set(
            User.objects.filter(id__in=unique_ids, is_active=True).values_list("id", flat=True)
        )
        missing_ids = [user_id for user_id in unique_ids if user_id not in existing_ids]
        if missing_ids:
            raise serializers.ValidationError(
                f"Invalid or inactive user IDs: {missing_ids}"
            )

        return unique_ids
