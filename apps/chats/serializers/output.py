from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.chats.models import Chat, Message, MessageFiles

User = get_user_model()


class UserOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "image", "last_activity"]


class FileOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageFiles
        fields = ["file"]


class MessagePreviewOutputSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.full_name")
    files = FileOutputSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = ["id", "text", "files", "status", "sender_name", "created_at", "updated_at"]


class ChatListOutputSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ["id", "participants", "last_message"]

    def get_participants(self, obj):
        request = self.context.get("request")
        prefetched = getattr(obj, "prefetched_participants", None)
        if prefetched is not None:
            users = [user for user in prefetched if user.id != request.user.id]
        else:
            users = obj.participants.exclude(id=request.user.id)
        return UserOutputSerializer(users, many=True).data

    def get_last_message(self, obj):
        prefetched_message = getattr(obj, "prefetched_last_message", None)
        if prefetched_message is not None:
            return MessagePreviewOutputSerializer(prefetched_message).data

        if getattr(obj, "last_message_id", None):
            return {
                "id": obj.last_message_id,
                "text": obj.last_message_text,
                "files": [],
                "status": obj.last_message_status,
                "sender_name": obj.last_message_sender_name,
                "created_at": obj.last_message_created_at,
                "updated_at": obj.last_message_updated_at,
            }
        return None


class ChatCreateOutputSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ["id", "participants"]

    def get_participants(self, obj):
        request = self.context.get("request")
        prefetched = getattr(obj, "prefetched_participants", None)
        if prefetched is not None:
            users = [user for user in prefetched if user.id != request.user.id]
        else:
            users = obj.participants.exclude(id=request.user.id)
        return UserOutputSerializer(users, many=True).data


class MessageListOutputSerializer(serializers.ModelSerializer):
    sender = UserOutputSerializer()
    files = FileOutputSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = ["id", "text", "files", "status", "sender", "created_at", "updated_at"]
