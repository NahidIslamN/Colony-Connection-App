from rest_framework import serializers

from apps.auths.models import CustomUser
from apps.profiles.models import UserProfile


class UserProfileOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "address",
            "date_of_birth",
            "gender",
            "city",
            "country",
            "postal_code",
            "bio",
            "website",
            "facebook",
            "linkedin",
            "twitter",
            "company",
            "job_title",
        ]


class CustomUserOutputSerializer(serializers.ModelSerializer):
    profile = UserProfileOutputSerializer(required=False)

    class Meta:
        model = CustomUser
        fields = ["id", "email", "full_name", "phone", "image", "profile"]
