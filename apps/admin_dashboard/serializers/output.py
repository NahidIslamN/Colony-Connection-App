from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.managements.models import Company, SubscribePlan, SupportModel, SupportFile

User = get_user_model()

class AdminSupportMessageFile(serializers.ModelSerializer):
	class Meta:
		model = SupportFile
		fields = "__all__"


class AdminSupportMessageSerializers(serializers.ModelSerializer):
	files = AdminSupportMessageFile(many=True, read_only = True)
	class Meta:
		model = SupportModel
		fields = "__all__"


class AdminUserOutputSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = (
			"id",
			"email",
			"full_name",
			"role",
			"status",
			"is_active",
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


class SubscriptionPlanMiniOutputSerializer(serializers.ModelSerializer):
	class Meta:
		model = SubscribePlan
		fields = (
			"id",
			"plan_Name",
			"price_monthly",
			"price_yearly",
			"user_limit",
			"colony_limit",
			"is_unlimit_users",
			"is_unlimit_colony",
		)


class CompanyManagementOutputSerializer(serializers.ModelSerializer):
	user = AdminUserOutputSerializer(read_only=True)
	subscription_package = SubscriptionPlanMiniOutputSerializer(read_only=True)

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
