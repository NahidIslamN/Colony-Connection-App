from rest_framework import serializers

from apps.managements.models import Colony, Customer, VisitColony


class ReportCustomerOutputSerializer(serializers.ModelSerializer):
	class Meta:
		model = Customer
		fields = (
			"id",
			"owner_name",
			"company_name",
			"email",
			"phone",
			"status",
			"city",
			"state",
			"country",
		)


class ReportColonyOutputSerializer(serializers.ModelSerializer):
	class Meta:
		model = Colony
		fields = (
			"id",
			"name",
			"region",
			"status",
			"location_url",
			"latitude",
			"longitude",
		)


class VisitColonyReportOutputSerializer(serializers.ModelSerializer):
	colony = ReportColonyOutputSerializer(read_only=True)
	pending_customers = ReportCustomerOutputSerializer(many=True, read_only=True)
	completed_customers = ReportCustomerOutputSerializer(many=True, read_only=True)
	pending_count = serializers.SerializerMethodField()
	completed_count = serializers.SerializerMethodField()
	total_customers = serializers.SerializerMethodField()

	class Meta:
		model = VisitColony
		fields = (
			"id",
			"date",
			"is_visited",
			"colony",
			"pending_customers",
			"completed_customers",
			"pending_count",
			"completed_count",
			"total_customers",
		)

	def get_pending_count(self, obj):
		return len(obj.pending_customers.all())

	def get_completed_count(self, obj):
		return len(obj.completed_customers.all())

	def get_total_customers(self, obj):
		return len(obj.pending_customers.all()) + len(obj.completed_customers.all())

