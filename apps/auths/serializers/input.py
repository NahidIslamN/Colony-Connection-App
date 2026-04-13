from rest_framework import serializers

from apps.auths.models import CustomUser


class SignupInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["full_name", "email", "password"]


class OtpInputSerializer(serializers.Serializer):
    email = serializers.CharField()
    otp = serializers.CharField()


class OtpAndPasswordInputSerializer(serializers.Serializer):
    otp = serializers.CharField()
    password = serializers.CharField()


class LoginInputSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()


class ChangePasswordInputSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()


class ForgetPasswordInputSerializer(serializers.Serializer):
    email = serializers.CharField()


class ResetPasswordInputSerializer(serializers.Serializer):
    new_password = serializers.CharField()
