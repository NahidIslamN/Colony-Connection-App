from rest_framework import serializers

from rest_framework import serializers
from apps.managements.models import Company, SubscribePlan


class CompanyManagementInputSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=250)
    ceo_name = serializers.CharField(max_length=250)
    email = serializers.EmailField()
    phone = serializers.CharField()

    subscription_package = serializers.PrimaryKeyRelatedField(
        queryset=SubscribePlan.objects.all(),
        required=False,
        allow_null=True
    )

    password = serializers.CharField()

