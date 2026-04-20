from rest_framework import serializers


class VisitColonyReportQueryInputSerializer(serializers.Serializer):
	date = serializers.DateField(required=True, input_formats=["%Y-%m-%d"])


class VisitCustomerNoteInputSerializer(serializers.Serializer):
	customer_id = serializers.IntegerField(required=True)
	note = serializers.CharField(required=True)


class VisitCustomerMachineryInputSerializer(serializers.Serializer):
	customer_id = serializers.IntegerField(required=True)
	type = serializers.CharField(max_length=250, required=True)
	brand = serializers.CharField(max_length=250, required=True)
	model = serializers.CharField(max_length=250, required=True)
	serial_number = serializers.CharField(max_length=250, required=True)
	purchase_year = serializers.DateField(required=True)
	condition = serializers.CharField(max_length=250, required=True)
	next_nervice = serializers.CharField(max_length=250, required=True)
	note = serializers.CharField(required=False, allow_blank=True)


class VisitColonyReportUpdateInputSerializer(serializers.Serializer):
	is_visited = serializers.BooleanField(required=False)
	completed_customer_ids = serializers.ListField(
		child=serializers.IntegerField(),
		required=False,
		allow_empty=True,
	)
	notes = VisitCustomerNoteInputSerializer(many=True, required=False)
	mechineries = VisitCustomerMachineryInputSerializer(many=True, required=False)


