from rest_framework import serializers


class ChatOrGroupCreateInputSerializer(serializers.Serializer):
    user_list = serializers.ListField(child=serializers.IntegerField(), required=True)
    group_name = serializers.CharField(required=False, allow_blank=True, default="")


class AddPeopleToGroupInputSerializer(serializers.Serializer):
    user_list = serializers.ListField(child=serializers.IntegerField(), required=True)


class SendMessageInputSerializer(serializers.Serializer):
    message = serializers.CharField(required=False, allow_blank=True, default="")
    files = serializers.ListField(child=serializers.FileField(), required=False, allow_empty=True)
