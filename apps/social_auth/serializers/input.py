from rest_framework import serializers


class GoogleLoginInputSerializer(serializers.Serializer):
    id_token = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        max_length=4096,
    )
