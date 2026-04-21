from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.managements.models import Company, SubscribePlan
from apps.admin_dashboard.models import TermsCondition

User = get_user_model()


class TermsConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsCondition
        fields = "__all__"


class CompanyManagementBaseSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=250, required=False)
    ceo_name = serializers.CharField(max_length=250, required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    user_full_name = serializers.CharField(max_length=250, required=False, allow_blank=True)
    user_email = serializers.EmailField(required=False)
    user_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    user_status = serializers.BooleanField(required=False)
    user_is_active = serializers.BooleanField(required=False)

    subscription_package = serializers.PrimaryKeyRelatedField(
        queryset=SubscribePlan.objects.all(),
        required=False,
        allow_null=True,
    )
    is_subscribe = serializers.BooleanField(required=False)
    expire_date = serializers.DateField(required=False)
    password = serializers.CharField(required=False, write_only=True, min_length=8, allow_blank=False)

    def _company_instance(self):
        instance = getattr(self, "instance", None)
        return instance if isinstance(instance, Company) else None

    def _current_user(self):
        company = self._company_instance()
        return getattr(company, "user", None) if company else None

    def _validate_unique_email(self, value, *, current_company_id=None, current_user_id=None):
        if Company.objects.filter(email__iexact=value).exclude(id=current_company_id).exists():
            raise serializers.ValidationError("A company with this email already exists.")
        if User.objects.filter(email__iexact=value).exclude(id=current_user_id).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def _validate_unique_phone(self, value, *, current_company_id=None, current_user_id=None):
        if not value:
            return value
        if Company.objects.filter(phone=value).exclude(id=current_company_id).exists():
            raise serializers.ValidationError("A company with this phone already exists.")
        if User.objects.filter(phone=value).exclude(id=current_user_id).exists():
            raise serializers.ValidationError("A user with this phone already exists.")
        return value

    def validate_email(self, value):
        company = self._company_instance()
        return self._validate_unique_email(
            value,
            current_company_id=getattr(company, "id", None),
            current_user_id=getattr(getattr(company, "user", None), "id", None),
        )

    def validate_user_email(self, value):
        company = self._company_instance()
        return self._validate_unique_email(
            value,
            current_company_id=getattr(company, "id", None),
            current_user_id=getattr(getattr(company, "user", None), "id", None),
        )

    def validate_phone(self, value):
        company = self._company_instance()
        return self._validate_unique_phone(
            value,
            current_company_id=getattr(company, "id", None),
            current_user_id=getattr(getattr(company, "user", None), "id", None),
        )

    def validate_user_phone(self, value):
        company = self._company_instance()
        return self._validate_unique_phone(
            value,
            current_company_id=getattr(company, "id", None),
            current_user_id=getattr(getattr(company, "user", None), "id", None),
        )


class CompanyManagementInputSerializer(CompanyManagementBaseSerializer):
    company_name = serializers.CharField(max_length=250)
    ceo_name = serializers.CharField(max_length=250)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)


class CompanyManagementUpdateInputSerializer(CompanyManagementBaseSerializer):
    pass

