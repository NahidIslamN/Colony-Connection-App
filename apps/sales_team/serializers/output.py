from rest_framework import serializers

from apps.managements.models import Colony, Customer, CustomerMechanary, CustomerNote, VisitColony


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


class CustomerNoteOutputSerializer(serializers.ModelSerializer):
	class Meta:
		model = CustomerNote
		fields = (
			"id",
			"date",
			"note",
			"created_at",
			"updated_at",
		)


class CustomerMachineryOutputSerializer(serializers.ModelSerializer):
	class Meta:
		model = CustomerMechanary
		fields = (
			"id",
			"date",
			"type",
			"brand",
			"model",
			"serial_number",
			"purchase_year",
			"condition",
			"next_nervice",
			"note",
			"created_at",
			"updated_at",
		)


class ReportCompletedCustomerOutputSerializer(ReportCustomerOutputSerializer):
	notes = serializers.SerializerMethodField()
	mechineries = serializers.SerializerMethodField()

	class Meta(ReportCustomerOutputSerializer.Meta):
		fields = ReportCustomerOutputSerializer.Meta.fields + (
			"notes",
			"mechineries",
		)

	def get_notes(self, obj):
		report_date = self.context.get("report_date")
		prefetched = getattr(obj, "report_notes", None)
		if prefetched is None:
			queryset = obj.customernote_set.all()
			if report_date:
				queryset = queryset.filter(date=report_date)
			prefetched = queryset.order_by("-created_at")
		return CustomerNoteOutputSerializer(prefetched, many=True).data

	def get_mechineries(self, obj):
		report_date = self.context.get("report_date")
		prefetched = getattr(obj, "report_mechineries", None)
		if prefetched is None:
			queryset = obj.customermechanary_set.all()
			if report_date:
				queryset = queryset.filter(date=report_date)
			prefetched = queryset.order_by("-created_at")
		return CustomerMachineryOutputSerializer(prefetched, many=True).data


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
	completed_customers = serializers.SerializerMethodField()
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

	def get_completed_customers(self, obj):
		context = dict(self.context)
		context["report_date"] = obj.date
		serializer = ReportCompletedCustomerOutputSerializer(
			obj.completed_customers.all(),
			many=True,
			context=context,
		)
		return serializer.data

	def get_pending_count(self, obj):
		return len(obj.pending_customers.all())

	def get_completed_count(self, obj):
		return len(obj.completed_customers.all())

	def get_total_customers(self, obj):
		return len(obj.pending_customers.all()) + len(obj.completed_customers.all())

