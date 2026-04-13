from rest_framework import serializers

from apps.notifications.models import NoteModel


class NotificationOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteModel
        fields = ["id", "title", "content", "note_type"]
