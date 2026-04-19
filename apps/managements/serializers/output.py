from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.managements.models import Colony, Company, Customer, SalesRepresentative

User = get_user_model()


class SafeUserOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "role",
            "status",
            "phone",
            "is_email_verified",
            "is_phone_verified",
            "image",
            "last_activity",
            "latitude",
            "longitude",
            "created_at",
            "updated_at",
        )


class CompanyOutputSerializer(serializers.ModelSerializer):
    user = SafeUserOutputSerializer(read_only=True)

    class Meta:
        model = Company
        fields = (
            "id",
            "user",
            "company_name",
            "ceo_name",
            "email",
            "phone",
            "subscription_package",
            "is_subscribe",
            "expire_date",
        )


class SalesRepresentativeOutputSerializer(serializers.ModelSerializer):
    user = SafeUserOutputSerializer(read_only=True)

    class Meta:
        model = SalesRepresentative
        fields = (
            "id",
            "company",
            "user",
            "full_name",
            "status",
            "email",
            "phone",
        )


class CustomerOutputSerializer(serializers.ModelSerializer):
    user = SafeUserOutputSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = (
            "id",
            "owner_company",
            "user",
            "owner_name",
            "company_name",
            "industry",
            "company_type",
            "email",
            "phone",
            "street_address",
            "city",
            "state",
            "postal_code",
            "country",
            "location_url",
            "latitude",
            "longitude",
        )


class ColonyOutputSerializer(serializers.ModelSerializer):
    # colony_owner = CompanyOutputSerializer(read_only=True)
    sales_reps = SalesRepresentativeOutputSerializer(many=True, read_only=True)
    customers = CustomerOutputSerializer(many=True, read_only=True)

    class Meta:
        model = Colony
        fields = (
            "id",
            "colony_owner",
            "name",
            "region",
            "sales_reps",
            "customers",
            "location_url",
            "latitude",
            "longitude",
        )
