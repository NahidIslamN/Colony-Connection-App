from rest_framework import serializers

from apps.auths.models import CustomUser


class AuthenticatedUserOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "full_name", "username", "email", "image"]
