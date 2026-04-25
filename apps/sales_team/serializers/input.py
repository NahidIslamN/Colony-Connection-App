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



class CustomerCreateSerializer(serializers.Serializer):
	# User fields
	
	image = serializers.ImageField(required=False, allow_null=True)

	# Customer fields
	owner_name = serializers.CharField(required=True, max_length=250)
	company_name = serializers.CharField(required=True, max_length=250)
	email = serializers.EmailField(required=True)
	phone = serializers.CharField(required=True, allow_blank=True, max_length=15)
	industry = serializers.CharField(required=False, allow_blank=True, max_length=100)
	company_type = serializers.CharField(required=False, allow_blank=True, max_length=100)
	street_address = serializers.CharField(required=False, allow_blank=True)
	city = serializers.CharField(required=False, allow_blank=True, max_length=100)
	state = serializers.CharField(required=False, allow_blank=True, max_length=100)
	postal_code = serializers.CharField(required=False, allow_blank=True, max_length=20)
	country = serializers.CharField(required=False, allow_blank=True, max_length=100)
	location_url = serializers.URLField(required=False, allow_blank=True)
	latitude = serializers.FloatField(required=False, allow_null=True)
	longitude = serializers.FloatField(required=False, allow_null=True)

	def validate_email(self, value):
		from django.contrib.auth import get_user_model

		User = get_user_model()
		if User.objects.filter(email=value).exists():
			raise serializers.ValidationError("User with this email already exists.")
		return value

	def validate(self, data):
		# ensure unique customer email if provided
		cust_email = data.get("email")
		if cust_email:
			from apps.managements.models import Customer

			if Customer.objects.filter(email=cust_email).exists():
				raise serializers.ValidationError({"email": "Customer with this email already exists."})
		return data


